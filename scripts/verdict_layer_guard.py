# -*- coding: utf-8 -*-
"""
龙虾判定层守卫 v1.0  (verdict_layer_guard.py)
================================================================
「假成功/假失败」**第 37 形态：判定层错配 —— 用过程信号冒充结果状态**

核心理论：任何一次"做没做成"的判定，都有五层信号：

    L0 意图层   我说我要做 X                      -> 不可信（最廉价的自欺）
    L1 调用层   命令发出 / 请求已发送              -> 不可信
    L2 传输层   socket 通、TLS 握手成功            -> 不可信（#8/#16）
    L3 过程层   rc=0 / exit code / status 字段     -> 弱可信（重灾区）
    L4 结果态   产物实际字节/数量/hash/内容/远端回查 -> ★唯一可信

铁律：**判定必须落在 L4；L3 只能当"要不要继续查"的分流信号，不能当结论。**

    · 假成功 = L3 绿、L4 红   （robocopy exit 0 但零文件；构建 success 但工作区 closed；
                               "推送成功"打印但 push rc=1）
    · 假失败 = L3 红、L4 绿   （magic number 断言失败但 490 帧全对；socket 000 但服务在跑）

子命令
    audit     静态 AST 扫描自写脚本的六大反模式（V1~V6）
    assert    对产物做 L4 结果态断言（存在/字节/数量/hash/包含/扩展名）
    dupcheck  产物重复检测（同文档多版本 / 同内容多副本，形态 #36）
    cases     真实故障案例库（L3 信号 vs L4 真相 对照）
    selftest  离线自测（不联网、不依赖外部文件）

零积分：纯 stdlib，只读（除 selftest 自建临时目录）。
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VERSION = "1.0"

# ---------------------------------------------------------------- 反模式规则
# 全限定名白名单（防 `str.replace` / `str.copy` 这类同名方法误报 —— 形态 #11）
WRITE_EXACT = {
    "os.replace", "os.rename", "os.makedirs", "os.mkdir", "os.system",
    "shutil.move", "shutil.copy", "shutil.copy2", "shutil.rmtree",
}
# 方法名白名单（这些名字没有同名字符串方法，可安全按 tail 匹配）
# 注：mkdir/makedirs 不算「产物」，刻意排除 —— 否则 V4 会被建目录刷屏（噪音 = 形态 #11 可信度崩塌）
WRITE_METHODS = {"write_text", "write_bytes", "writelines", "write", "dump"}
READ_CALLS = {
    "read_text", "read_bytes", "exists", "isdir", "isfile", "getsize",
    "stat", "listdir", "walk", "read", "readlines", "load", "loads",
    "iglob", "glob",
}
READ_EXACT = {"os.path.exists", "os.path.isdir", "os.path.isfile", "os.path.getsize",
              "os.listdir", "os.walk", "os.stat", "glob.glob", "glob.iglob"}
SUCCESS_WORDS = ("成功", "ok", "success", "succeed", "完成", "✅", "done", "passed", "pass")
RC_ATTRS = {"returncode", "rc", "return_code", "exitcode", "exit_code", "code"}

# 惯用常量白名单（不算 magic number）
SAFE_CONSTS = {0, 1, -1, 2, 3, 4, 8, 16, 24, 32, 64, 100, 128, 200, 255,
               256, 404, 500, 1024, 2048, 4096, 8192, 65536, 80, 443}


def _walk(node):
    for n in ast.walk(node):
        yield n


def _dotted(node):
    """把 Attribute/Name 还原成点分字符串，取不到返回 None。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _is_subprocess_call(node) -> bool:
    """是否 subprocess 家族调用（run/Popen/call/check_output/getoutput 等）。"""
    name = _dotted(node.func) if isinstance(node, ast.Call) else None
    if not name:
        return False
    return bool(re.search(r"(subprocess\.(run|call|check_call|check_output|Popen|getoutput|getstatusoutput)"
                          r"|os\.system|os\.popen|\.communicate|\.wait)$", name)) or \
        name.endswith((".wait", ".communicate"))


def _consts_in(node):
    """递归取出比较两侧的所有字面常量（含 Tuple/List 内的，(w,h)!=(948,112) 也抓得到）。"""
    out = []
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        out.append(node)
    elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        for e in node.elts:
            out.extend(_consts_in(e))
    elif isinstance(node, ast.BinOp):
        out.extend(_consts_in(node.left))
        out.extend(_consts_in(node.right))
    return out


def _var_used_as_rc(test, var) -> bool:
    """
    判定表达式里，该变量是否真以「退出码」语义出现。
    防形态 #11（守卫误报）：同名变量被复用成路径/容器时（os.path.exists(p)）不算。
    """
    for n in _walk(test):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) \
                and n.value.id == var and n.attr in RC_ATTRS:
            return True
        if isinstance(n, ast.Compare):
            sides = [n.left] + list(n.comparators)
            mine = [s for s in sides if isinstance(s, ast.Name) and s.id == var]
            other = [s for s in sides if not (isinstance(s, ast.Name) and s.id == var)]
            if mine and other and all(isinstance(o, ast.Constant)
                                      and isinstance(o.value, (int, float)) for o in other):
                return True
        if isinstance(n, ast.Name) and n.id == var:
            if n is test or (isinstance(test, ast.UnaryOp) and test.operand is n):
                return True
    return False


def _is_rc_expr(node) -> bool:
    """是否取退出码的表达式：`p.returncode` / `r.returncode`。"""
    if isinstance(node, ast.Attribute) and node.attr in RC_ATTRS:
        return True
    if isinstance(node, ast.Name) and node.id.lower() in RC_ATTRS:
        return True
    return False


# ---------------------------------------------------------------- V1 变量覆盖
def _scope_map(tree):
    """节点 -> 作用域 ID（防跨函数同名变量被当成同一条 —— 形态 #11 第三类误报）。"""
    scope = {}
    fns = (ast.FunctionDef, ast.AsyncFunctionDef)

    def visit(node, sid):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, fns):
                scope[ch] = sid
                visit(ch, f"{ch.name}@{ch.lineno}")
            else:
                scope[ch] = sid
                visit(ch, sid)

    for ch in ast.iter_child_nodes(tree):
        if isinstance(ch, fns):
            scope[ch] = "<module>"
            visit(ch, f"{ch.name}@{ch.lineno}")
        else:
            scope[ch] = "<module>"
            visit(ch, "<module>")
    scope[tree] = "<module>"
    return scope


def rule_v1(tree, src_lines):
    """
    V1 判定复用被后续步骤覆盖的变量（形态 #35）
    同一变量被多次赋成"某步的退出码"，之后又拿它做最终判定
    -> 前面的失败全被吞，只有最后一步说了算。
    """
    hits = []
    scope = _scope_map(tree)
    assigns: dict[tuple, list[int]] = {}
    for n in _walk(tree):
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            sid = scope.get(n, "<module>")
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            val = n.value
            if val is None:
                continue
            is_rc = _is_rc_expr(val) or _is_subprocess_call(val)
            if not is_rc:
                continue
            for t in targets:
                if isinstance(t, ast.Name):
                    assigns.setdefault((sid, t.id), []).append(n.lineno)
    for n in _walk(tree):
        if isinstance(n, ast.If):
            sid = scope.get(n, "<module>")
            used = {x.id for x in _walk(n.test) if isinstance(x, ast.Name)}
            for (vsid, var), lines in assigns.items():
                if vsid != sid or var not in used or len(lines) < 2:
                    continue
                if not _var_used_as_rc(n.test, var):
                    continue  # 同名但当路径/容器用 —— 不误报（形态 #11）
                # 判定位置在第 2 次及以后赋值之后 => 只反映最后一次
                if n.lineno > lines[0]:
                    prev = [l for l in lines if l < n.lineno]
                    if len(prev) >= 2:
                        hits.append({
                            "line": n.lineno,
                            "var": var,
                            "assigns": lines,
                            "why": f"变量 `{var}` 在 {lines} 行被重复赋值为各步退出码，"
                                   f"第 {n.lineno} 行的判定只反映最后一次赋值（{max(prev)} 行）",
                            "src": src_lines[n.lineno - 1].strip()[:90],
                        })
    return hits


# ---------------------------------------------------------------- V2 magic 数
def rule_v2(tree, src_lines):
    """
    V2 期望值写死成 magic number（形态 #34）
    断言比较中直接出现字面常量，且该常量不是由同文件定义式推导出来的。
    """
    # 收集文件里所有被"命名"的常量（EXPECTED_H = 168 这种算有出处）
    named = set()
    for n in _walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, (int, float)):
            named.add(n.value.value)
        if isinstance(n, ast.AnnAssign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, (int, float)):
            named.add(n.value.value)

    hits = []
    for n in _walk(tree):
        if not isinstance(n, ast.Compare):
            continue
        consts = []
        for side in list(n.comparators) + [n.left]:
            consts.extend(_consts_in(side))
        for c in consts:
            v = c.value
            if v in SAFE_CONSTS or v in named:
                continue
            if isinstance(v, float) or abs(v) < 5:
                continue
            # 该行有注释给出推导式？降级为 INFO
            line = src_lines[c.lineno - 1]
            has_derivation = bool(re.search(r"[=＝].*[\*\+\-/]", line)) or "#" in line
            hits.append({
                "line": c.lineno,
                "value": v,
                "level": "INFO" if has_derivation else "WARN",
                "why": f"期望值 `{v}` 写死在比较里（未见同文件定义式推导）"
                       + ("；本行有注释，仍建议改成表达式" if has_derivation else ""),
                "src": line.strip()[:90],
            })
    return hits


# ---------------------------------------------------------------- V3 只看 rc
def rule_v3(tree, src_lines):
    """V3 只凭 rc==0 就打印成功，分支内无任何产物校验（形态 #35 近亲）。"""
    hits = []
    for n in _walk(tree):
        if not isinstance(n, ast.If):
            continue
        test_txt = ast.dump(n.test)
        if not any(a in test_txt for a in RC_ATTRS):
            continue
        body_txt = " ".join(ast.dump(x) for x in n.body)
        has_success = False
        for x in _walk(n):
            if isinstance(x, ast.Constant) and isinstance(x.value, str):
                if any(w in x.value.lower() for w in SUCCESS_WORDS):
                    has_success = True
        if not has_success:
            continue
        has_verify = any(k in body_txt for k in
                         ("exists", "isdir", "isfile", "getsize", "read_text",
                          "read_bytes", "stat", "listdir", "walk", "st_size",
                          "read", "open"))
        if not has_verify and "0" in test_txt:
            hits.append({
                "line": n.lineno,
                "why": "该分支仅凭退出码为 0 就宣称成功，分支内没有任何产物检查",
                "src": src_lines[n.lineno - 1].strip()[:90],
            })
    return hits


# ---------------------------------------------------------------- V4 写完不回读
def rule_v4(tree, src_lines):
    """V4 写产物但不回读验收（形态 #9 铁律的静态版）。"""
    writes, reads = [], []
    for n in _walk(tree):
        if isinstance(n, ast.Call):
            d = _dotted(n.func)
            if not d:
                continue
            tail = d.split(".")[-1]
            is_write = (d in WRITE_EXACT) or (tail in WRITE_METHODS)
            is_read = (d in READ_EXACT) or (tail in READ_CALLS)
            if is_write:
                writes.append(n.lineno)
            if is_read:
                reads.append(n.lineno)
    if not writes:
        return []
    # 允许：读发生在任意一次写之后
    late_reads = [r for r in reads if r > min(writes)]
    if late_reads:
        return []
    return [{
        "line": min(writes),
        "why": f"检出 {len(writes)} 处写操作，但之后没有任何回读/验收调用"
               f"（写 {min(writes)}~{max(writes)} 行）",
        "src": src_lines[min(writes) - 1].strip()[:90],
    }]


# ---------------------------------------------------------------- V5 裸 socket
def rule_v5(tree, src_lines):
    """V5 用裸 socket 连通当网络判据（形态 #8/#16）。"""
    hits = []
    has_sock, has_http = False, False
    for n in _walk(tree):
        if isinstance(n, ast.Call):
            d = _dotted(n.func) or ""
            if "socket" in d and ("create_connection" in d or "connect" in d):
                has_sock = True
                hits.append({"line": n.lineno, "socket": d})
        if isinstance(n, ast.Name) and n.id.lower() in ("http", "https", "urllib", "requests"):
            has_http = True
        if isinstance(n, ast.Attribute) and n.attr in ("urlopen", "request", "get", "post", "head"):
            has_http = True
    if has_sock and not has_http:
        for h in hits:
            h["why"] = "用裸 socket 连通判定网络可达，未见任何应用层 HTTP 探针（TCP 通 ≠ 服务可用）"
            h["src"] = src_lines[h["line"] - 1].strip()[:90]
        return hits
    return []


# ---------------------------------------------------------------- V6 退出码唯一
def rule_v6(tree, src_lines):
    """V6 进程调用结果只取 .returncode，从不校验产物（robocopy/PS 退出码假象）。"""
    hits = []
    for n in _walk(tree):
        if isinstance(n, ast.Attribute) and n.attr in RC_ATTRS:
            hits.append(n.lineno)
            break
    if not hits:
        return []
    body = " ".join(ast.dump(x) for x in _walk(tree))
    has_prod = any(k in body for k in ("exists", "getsize", "st_size", "listdir",
                                       "walk", "read_text", "read_bytes", "glob"))
    if has_prod:
        return []
    return [{
        "line": hits[0],
        "why": "脚本依赖退出码下结论，但全文没有任何产物态校验（退出码在回收/沙箱/多阶段场景会说谎）",
        "src": src_lines[hits[0] - 1].strip()[:90],
    }]


RULES = [
    ("V1", "判定复用被覆盖变量", "CRIT", rule_v1),
    ("V2", "magic number 期望值", "WARN", rule_v2),
    ("V3", "仅凭 rc==0 宣称成功", "HIGH", rule_v3),
    ("V4", "写产物不回读验收", "HIGH", rule_v4),
    ("V5", "裸 socket 当网络判据", "HIGH", rule_v5),
    ("V6", "退出码作唯一结论", "MID", rule_v6),
]


def cmd_audit(paths):
    total = {"CRIT": 0, "HIGH": 0, "WARN": 0, "MID": 0, "INFO": 0}
    files_scanned = 0
    files_clean = 0
    for p in paths:
        if os.path.isdir(p):
            subs = []
            for root, dirs, fs in os.walk(p):
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
                for f in fs:
                    if f.endswith(".py"):
                        subs.append(os.path.join(root, f))
            for s in subs:
                r = cmd_audit([s])
                total = {k: total[k] + r[0][k] for k in total}
                files_scanned += r[1]
                files_clean += r[2]
            continue
        try:
            src = open(p, "r", encoding="utf-8", errors="replace").read()
        except OSError as e:
            print(f"[SKIP] {p} -> {e}")
            continue
        files_scanned += 1
        try:
            tree = ast.parse(src, filename=p)
        except SyntaxError as e:
            print(f"[SKIP] {p} 语法错误无法解析: {e}")
            continue
        lines = src.splitlines() or [""]
        found = []
        for rid, name, sev, fn in RULES:
            try:
                for h in fn(tree, lines):
                    h.setdefault("level", sev)
                    h["id"] = rid
                    h["name"] = name
                    found.append(h)
            except Exception as e:  # 单条规则失败不影响整体（防守卫自己造假失败 #11）
                print(f"  [规则 {rid} 异常] {type(e).__name__}: {e}")
        found.sort(key=lambda x: ({"CRIT": 0, "HIGH": 1, "WARN": 2, "MID": 3, "INFO": 4}
                                  .get(x.get("level", "WARN"), 9), x["line"]))
        if not found:
            files_clean += 1
            print(f"[CLEAN] {p}")
            continue
        print(f"\n[FILE] {p}")
        for h in found:
            lvl = h.get("level", "WARN")
            total[lvl] = total.get(lvl, 0) + 1
            tag = {"CRIT": "[严重]", "HIGH": "[高]  ", "WARN": "[中]  ",
                   "MID": "[低]  ", "INFO": "[提示]"}.get(lvl, "[中]  ")
            print(f"  {tag} {h['id']} {h['name']}  行{h['line']}")
            print(f"         {h['why']}")
            if h.get("src"):
                print(f"         > {h['src']}")
    print("\n" + "=" * 70)
    print(f"扫描 {files_scanned} 个文件，洁净 {files_clean} 个")
    print("命中：" + "  ".join(f"{k}={v}" for k, v in total.items() if v))
    verdict = "FAIL" if total.get("CRIT") else ("WARN" if total.get("HIGH") or total.get("WARN") else "PASS")
    print(f"结论：{verdict}")
    return total, files_scanned, files_clean


# ---------------------------------------------------------------- L4 结果态断言
def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_assert(args):
    """
    assert --target DIR [--ext .png] [--min-files N] [--max-files N]
            [--min-bytes N] [--hash sha256hex] [--contains "str"] [--json]
    """
    opts = {}
    for i in range(0, len(args), 2):
        if args[i].startswith("--"):
            opts[args[i][2:]] = args[i + 1] if i + 1 < len(args) else ""
    target = opts.get("target") or opts.get("t")
    if not target:
        print("[用法] assert --target DIR [--ext .png] [--min-files N] [--min-bytes N] "
              "[--hash H] [--contains S]")
        return 2
    ext = opts.get("ext")
    results = []

    def add(name, ok, detail):
        results.append((ok, name, detail))

    exists = os.path.exists(target)
    add("存在性", exists, target)
    if not exists:
        _print_assert(results)
        return 1

    if os.path.isdir(target):
        files = []
        for root, dirs, fs in os.walk(target):
            for f in fs:
                if ext and not f.endswith(ext):
                    continue
                files.append(os.path.join(root, f))
        add("文件数>0", len(files) > 0, f"{len(files)} 个" + (f"（{ext}）" if ext else ""))
        if "min-files" in opts:
            n = int(opts["min-files"])
            add(f"文件数>={n}", len(files) >= n, f"实际 {len(files)}")
        if "max-files" in opts:
            n = int(opts["max-files"])
            add(f"文件数<={n}", len(files) <= n, f"实际 {len(files)}")
        total_bytes = sum(os.path.getsize(f) for f in files)
        add("字节数>0", total_bytes > 0, f"{total_bytes} B ({total_bytes/1024:.1f} KB)")
        if "min-bytes" in opts:
            n = int(opts["min-bytes"])
            add(f"字节数>={n}", total_bytes >= n, f"实际 {total_bytes}")
        if files and "contains" in opts:
            needle = opts["contains"]
            hit = 0
            for f in files[:200]:
                try:
                    if needle in open(f, "r", encoding="utf-8", errors="ignore").read():
                        hit += 1
                except OSError:
                    pass
            add(f"含「{needle}」", hit > 0, f"{hit}/{min(len(files),200)} 个文件命中")
    else:
        size = os.path.getsize(target)
        add("字节数>0", size > 0, f"{size} B")
        if "min-bytes" in opts:
            n = int(opts["min-bytes"])
            add(f"字节数>={n}", size >= n, f"实际 {size}")
        if "hash" in opts:
            h = _sha256(target)
            add("SHA256 一致", h == opts["hash"], f"{h[:16]}… vs 期望 {opts['hash'][:16]}…")
        if "contains" in opts:
            try:
                txt = open(target, "r", encoding="utf-8", errors="ignore").read()
            except OSError:
                txt = ""
            add(f"含「{opts['contains']}」", opts["contains"] in txt, f"正文 {len(txt)} 字符")
    return _print_assert(results)


def _print_assert(results):
    print("=" * 70)
    print("L4 结果态断言")
    print("=" * 70)
    for ok, name, detail in results:
        print(f"[{'GREEN' if ok else 'RED'}] {name:<18} {detail}")
    bad = [r for r in results if not r[0]]
    print("-" * 70)
    if bad:
        print(f"结论：FAIL（{len(bad)}/{len(results)} 项未达预期）")
        return 1
    print(f"结论：PASS（{len(results)}/{len(results)} 项全部落在 L4 结果态）")
    return 0


# ---------------------------------------------------------------- 重复产物检测
VERSION_PAT = re.compile(r"(_v\d+|\(\d+\)|[-_\s]+(副本|copy|final|final2|新版|new|bak|old)"
                         r"|[-_]\d{8}|[-_]?首版|[-_]?最终版)", re.I)


def cmd_dupcheck(args):
    """dupcheck DIR [--ext .md]  —— 检出「同一逻辑产物的多个版本」（形态 #36）。"""
    target = args[0] if args else "."
    ext = None
    if "--ext" in args:
        ext = args[args.index("--ext") + 1]
    groups: dict[str, list[str]] = {}
    by_hash: dict[str, list[str]] = {}
    for root, dirs, fs in os.walk(target):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
        for f in fs:
            if ext and not f.endswith(ext):
                continue
            p = os.path.join(root, f)
            stem = os.path.splitext(f)[0]
            key = VERSION_PAT.sub("", stem).lower()
            groups.setdefault(key, []).append(p)
            try:
                by_hash.setdefault(_sha256(p), []).append(p)
            except OSError:
                pass
    print("=" * 70)
    print("重复产物检测（L4 回查：不只看「到没到」，还看「多没多」）")
    print("=" * 70)
    n_ver = n_dup = 0
    for key, ps in sorted(groups.items()):
        if len(ps) > 1:
            n_ver += 1
            print(f"[版本簇] {key}  -> {len(ps)} 个")
            for p in sorted(ps):
                print(f"    {p}")
    for h, ps in by_hash.items():
        if len(ps) > 1:
            n_dup += 1
            print(f"[同内容副本] {h[:12]}… -> {len(ps)} 个")
            for p in sorted(ps)[:5]:
                print(f"    {p}")
    print("-" * 70)
    if n_ver or n_dup:
        print(f"结论：WARN —— {n_ver} 个版本簇 / {n_dup} 组同内容副本"
              f"（确认哪个是活的，其余标 [已废弃]）")
        return 1
    print("结论：PASS —— 未发现重复产物")
    return 0


# ---------------------------------------------------------------- 案例库
CASES = [
    ("robocopy 退出码", "exit 127 / 日志零报错行", "源目录仍在、目标 0 文件", "比对源/目标文件数与字节"),
    ("PowerShell 工具退出码", "-1073741571 栈溢出", "崩溃前删除已实际完成", "读日志确认动作，不判失败"),
    ("像素精灵验收", "断言 168 失败 → FAIL", "490 帧全部 16×28 RGBA 正确", "期望值由定义式推导"),
    ("GitHub 推送脚本", "打印「推送成功」", "fetch rc=128 / push rc=1 非快进", "只取当步 rc + ls-remote 回查"),
    ("CNB 云原生开发", "构建 status: success", "工作区 closed，端点 404", "list-workspaces 查 status=running"),
    ("乐享知识库推送", "code:0 新建成功", "同文档出两页，旧页成活页", "回查条数，重复页标 [已废弃]"),
    ("网络连通", "socket 3/3 通", "curl 000 / git 超时", "应用层 http HEAD 探针"),
    ("回环代理", "502 upstream connect", "本地服务其实没起", "回环强制直连 + NO_PROXY"),
    ("CNB 构建受理", "message 含 'not finish'", "其实已受理（200+业务ID）", "200+业务ID = 受理，终态另查"),
    ("stage 内起服务", "stage 日志 success", "进程随构建 End 被回收", "setsid 起 + 应用层探针验收"),
    ("磁盘清理", "清理脚本 Result=0", "释放 0MB（批量删除守卫）", "清理前后各测一次可用空间"),
    ("模型切换", "配置落盘成功", "进程内 $ENV 仍是旧值", "查进程内实际生效值"),
]


def cmd_cases():
    print("=" * 78)
    print("第 37 形态 · 案例库：L3 过程信号  vs  L4 结果真相")
    print("=" * 78)
    print(f"{'场景':<18}{'L3 过程信号（骗了你）':<26}{'L4 真相':<26}防法")
    print("-" * 78)
    for a, b, c, d in CASES:
        print(f"{a:<18}{b:<26}{c:<26}{d}")
    print("-" * 78)
    print("共性：判定依据取自「过程层」，而真相只在「结果态层」。")
    return 0


# ---------------------------------------------------------------- selftest
BAD = '''
import subprocess, os
def main():
    rc = subprocess.run(["git","fetch","origin"],capture_output=True).returncode
    rc = subprocess.run(["git","merge","origin/main"],capture_output=True).returncode
    rc = subprocess.run(["git","push","origin","main"],capture_output=True).returncode
    rc = subprocess.run(["git","cat-file","-e","HEAD"],capture_output=True).returncode
    if rc == 0:
        print("推送成功")
    return 0
'''

BAD2 = '''
import socket
def check():
    s = socket.create_connection(("github.com",443),timeout=3)
    s.close()
    return True
'''

BAD3 = '''
def verify(w,h):
    if (w,h) != (948,112):
        return False
    if h <= 168:
        return False
    return True
'''


def cmd_selftest():
    print("=" * 70)
    print("龙虾判定层守卫 v1.0 · selftest")
    print("=" * 70)
    ok = fail = 0

    def chk(name, cond, extra=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"[PASS] {name} {extra}")
        else:
            fail += 1
            print(f"[FAIL] {name} {extra}")

    # 1 V1 检出变量覆盖
    v1 = rule_v1(ast.parse(BAD), BAD.splitlines())
    chk("V1 检出「rc 复用被覆盖」", len(v1) >= 1, f"（命中 {len(v1)} 处）")

    # 2 V1 不误报：逐步留证的写法
    good = '''
import subprocess
def main():
    r1 = subprocess.run(["git","fetch"],capture_output=True)
    if r1.returncode != 0:
        return 1
    r2 = subprocess.run(["git","push"],capture_output=True)
    if r2.returncode != 0:
        return 2
    return 0
'''
    chk("V1 不在逐步留证写法上误报", len(rule_v1(ast.parse(good), good.splitlines())) == 0)

    # 2b V1 同名变量后来被复用成路径 —— 不得误报（形态 #11）
    reuse = '''
import subprocess, os
def main():
    p = subprocess.run(["git","fetch"],capture_output=True)
    if p.returncode != 0:
        return 1
    p = "/tmp/x.txt"
    if os.path.exists(p):
        return 2
    return 0
'''
    chk("V1 同名变量复用为路径不误报", len(rule_v1(ast.parse(reuse), reuse.splitlines())) == 0)

    # 2c V1 跨函数同名变量 —— 不得误报（形态 #11 第三类）
    cross = '''
import subprocess
def a():
    p = subprocess.run(["git","fetch"],capture_output=True)
    if p.returncode != 0:
        return 1
    return 0
def b():
    p = subprocess.run(["git","push"],capture_output=True)
    if p.returncode == 0:
        return 0
    return 1
'''
    chk("V1 跨函数同名变量不误报", len(rule_v1(ast.parse(cross), cross.splitlines())) == 0)

    # 3 V2 检出 magic number
    v2 = rule_v2(ast.parse(BAD3), BAD3.splitlines())
    chk("V2 检出 magic number(948/112/168)", len(v2) >= 3, f"（命中 {len(v2)} 处）")

    # 4 V2 对命名常量不误报
    good2 = '''
FRAME_W = 16
FRAME_H = 28
def verify(w,h):
    return (w,h) == (FRAME_W, FRAME_H)
'''
    chk("V2 对命名常量不误报", len(rule_v2(ast.parse(good2), good2.splitlines())) == 0)

    # 5 V3 检出"仅凭 rc 宣称成功"
    chk("V3 检出仅凭 rc==0 宣称成功", len(rule_v3(ast.parse(BAD), BAD.splitlines())) >= 1)

    # 6 V4 写完不回读
    bad4 = '''
from pathlib import Path
def run():
    Path("a.txt").write_text("hello",encoding="utf-8")
'''
    chk("V4 检出写完不回读", len(rule_v4(ast.parse(bad4), bad4.splitlines())) == 1)

    # 7 V4 有回读则不报
    good4 = '''
from pathlib import Path
def run():
    p = Path("a.txt")
    p.write_text("hello",encoding="utf-8")
    assert p.read_text(encoding="utf-8") == "hello"
'''
    chk("V4 有回读则不误报", len(rule_v4(ast.parse(good4), good4.splitlines())) == 0)

    # 8 V5 裸 socket
    chk("V5 检出裸 socket 判网络", len(rule_v5(ast.parse(BAD2), BAD2.splitlines())) >= 1)

    # 9 L4 assert 正例
    tmp = tempfile.mkdtemp(prefix="lbverdict_")
    d = os.path.join(tmp, "out")
    os.makedirs(d, exist_ok=True)
    for i in range(3):
        with open(os.path.join(d, f"f{i}.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + os.urandom(64))
    rc = cmd_assert(["--target", d, "--ext", ".png", "--min-files", "3", "--min-bytes", "100"])
    chk("L4 assert 正例 PASS", rc == 0)

    # 10 L4 assert 反例（数量不足）
    rc = cmd_assert(["--target", d, "--ext", ".png", "--min-files", "99"])
    chk("L4 assert 反例正确判 FAIL", rc == 1)

    # 11 dupcheck 检出版本簇
    for n in ("报告.md", "报告_v2.md", "报告 - 副本.md"):
        with open(os.path.join(tmp, n), "w", encoding="utf-8") as f:
            f.write("x" * 10)
    rc = cmd_dupcheck([tmp, "--ext", ".md"])
    chk("dupcheck 检出版本簇", rc == 1)

    # 12 dupcheck 同内容副本
    d2 = os.path.join(tmp, "same")
    os.makedirs(d2, exist_ok=True)
    for n in ("a.md", "b.md"):
        with open(os.path.join(d2, n), "w", encoding="utf-8") as f:
            f.write("identical")
    rc = cmd_dupcheck([d2, "--ext", ".md"])
    chk("dupcheck 检出同内容副本", rc == 1)

    print("-" * 70)
    print(f"selftest 结果：{ok} 通过 / {fail} 失败")
    return 0 if fail == 0 else 1


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        print("用法：")
        print("  verdict_layer_guard.py audit   <file.py|dir> [...]")
        print("  verdict_layer_guard.py assert  --target DIR [--ext .png] [--min-files N] "
              "[--min-bytes N] [--hash H] [--contains S]")
        print("  verdict_layer_guard.py dupcheck <dir> [--ext .md]")
        print("  verdict_layer_guard.py cases")
        print("  verdict_layer_guard.py selftest")
        return 0
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "audit":
        if not rest:
            print("[ERR] 需要至少一个路径")
            return 2
        t, _, _ = cmd_audit(rest)
        return 1 if t.get("CRIT") else 0
    if cmd == "assert":
        return cmd_assert(rest)
    if cmd == "dupcheck":
        return cmd_dupcheck(rest)
    if cmd == "cases":
        return cmd_cases()
    if cmd == "selftest":
        return cmd_selftest()
    print(f"[ERR] 未知子命令 {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
