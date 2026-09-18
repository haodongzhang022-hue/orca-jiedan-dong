"""双向镜像同步脚本骨架 — 5 子库本地↔乐享知识库

★ 真实对接需要 Lexiang connector 授权（当前 disconnected）
★ 本脚本先做"本地扇出"骨架 + 校验逻辑，待授权后无侵入式接入
★ 调用： python scripts/lib/lexiang_sync.py [--dry-run] [--full]
"""
import os, sys, json, time, hashlib, shutil, argparse
from pathlib import Path
from datetime import datetime, timedelta

CONFIG = Path(__file__).parent / 'lib_config.json'
LOG_FILE = Path(__file__).parent.parent.parent / '.workbuddy' / 'sync_log.jsonl'
ACTIVITY = Path(__file__).parent.parent.parent / '.workbuddy' / 'activity_stream.jsonl'

# ---------- 工具 ----------
def load_config():
    with open(CONFIG, encoding='utf-8') as f:
        return json.load(f)

def file_md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def is_blacklisted(path, bl):
    s = str(path).replace('\\', '/')
    for pat in bl['path_patterns']:
        if pat.startswith('**/') and pat.endswith('/**'):
            sub = pat[3:-3]
            if f'/{sub}/' in s or s.endswith(f'/{sub}'):
                return True
    for pat in bl['filename_patterns']:
        if Path(s).name == pat.lstrip('*').rstrip('*'):
            return True
    return False

def walk_local(root_path, bl):
    """递归列出本地全部非黑名单文件"""
    root = Path(root_path)
    if not root.exists():
        return []
    files = []
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        if is_blacklisted(p, bl):
            continue
        files.append(p)
    return files

def append_activity(agent, channel, action, **extra):
    rec = {
        'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'agent': agent,
        'channel': channel,
        'action': action,
        **extra
    }
    with open(ACTIVITY, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def write_sync_log(level, msg):
    """写同库本地日志，方便溯源"""
    rec = {
        'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'level': level,
        'msg': msg
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    if level == 'ERROR':
        print(f'  ❌ {msg}')
    elif level == 'WARN':
        print(f'  ⚠️  {msg}')
    else:
        print(f'  · {msg}')

# ---------- 校验 ----------
def full_check(lib):
    """全量校验：本地 vs 云端（云端 dry-run）"""
    bl = lib.get('blacklist_global') or load_config()['blacklist']
    local_files = walk_local(lib['local_path'], bl)
    write_sync_log('INFO', f"[{lib['id']}] 全量校验 · 本地共 {len(local_files)} 非黑名单文件")

    cloud_count = 0  # 待 Lexiang 授权后用真实 API 取
    if lib.get('sync') and not lib.get('cloud_dry_run', True):
        # 真实调用乐享 API 拿云端列表
        # cloud_files = lexiang_api.list_files(lib['cloud_id'])
        # diff = compare(local_files, cloud_files)
        pass

    return {
        'lib_id': lib['id'],
        'lib_name': lib['name'],
        'local_files': len(local_files),
        'cloud_files': cloud_count,
        'blacklisted_filtered': '<由 walk_local 完成>',
        'status': 'OK'
    }

# ---------- 2h 增量 ----------
def incremental_sync(lib):
    """增量同步：扫本地 2h 内改动 + 调云端 API 拉新文档回写本地"""
    bl = load_config()['blacklist']
    cutoff = datetime.now() - timedelta(hours=2)
    root = Path(lib['local_path'])
    if not root.exists():
        write_sync_log('WARN', f"[{lib['id']}] 本地路径不存在: {root}")
        return {'lib_id': lib['id'], 'status': 'SKIP', 'reason': 'LOCAL_NOT_FOUND'}

    new_files = []
    modified_files = []
    for p in root.rglob('*'):
        if not p.is_file() or is_blacklisted(p, bl):
            continue
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        if mtime > cutoff:
            new_files.append(str(p))

    # 云端拉新（待 Lexiang 授权）
    cloud_new = 0
    # if not lib.get('cloud_dry_run', True):
    #     cloud_new_files = lexiang_api.list_since(lib['cloud_id'], cutoff)
    #     for cf in cloud_new_files:
    #         shutil.copy(cf, local_dest)  # 原路回写
    #         cloud_new += 1

    append_activity('system', 'direct', f"增量同步 {lib['name']}",
                    lib_id=lib['id'], local_new=len(new_files), cloud_new=cloud_new)
    return {
        'lib_id': lib['id'],
        'lib_name': lib['name'],
        'local_new_or_modified': len(new_files),
        'cloud_new_pulled': cloud_new,
        'status': 'OK',
        'next_run_at': (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    }

# ---------- 单 lib 处理 ----------
def process_lib(lib, args):
    if args.full:
        return full_check(lib)
    return incremental_sync(lib)

# ---------- 主入口 ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--full', action='store_true', help='首跑全量校验')
    ap.add_argument('--dry-run', action='store_true', help='只看不动手（默认开启）')
    ap.add_argument('--lib', type=str, default='', help='仅处理指定 lib_id')
    args = ap.parse_args()

    cfg = load_config()
    print(f'\n=== 🪞 龙虾双向镜像同步 v2.7 · 模式：{"全量" if args.full else "2h增量"} · dry_run={args.dry_run or not args.full} ===\n')

    summary = []
    for lib in cfg['libraries']:
        if args.lib and lib['id'] != args.lib:
            continue
        if not lib.get('sync', True):
            print(f"  ⏭️  [{lib['id']}] {lib['name']} · sync=false 跳过")
            continue
        # 云端授权校验
        cloud_dry = not _is_lexiang_authorized()
        if cloud_dry:
            lib['cloud_dry_run'] = True
            write_sync_log('WARN', f"⚠️ 乐享知识库 connector 未授权，云端操作走 dry-run")
        result = process_lib(lib, args)
        summary.append(result)
        print(f"  ✅ [{lib['id']}] {lib['name']} → {result['status']}")
        for k,v in result.items():
            if k in ('lib_id','lib_name','status'): continue
            print(f'        {k}: {v}')

    print(f'\n=== 汇总 ===')
    print(f'  · 处理子库: {len(summary)} 个')
    print(f'  · 黑名单拦截: 已应用（.git/密钥库/tmp/log/.lock 等）')
    print(f'  · 同步周期: 2 小时')
    print(f'  · 全量日志: {LOG_FILE}')
    print(f'  · 活动流: 已实时写入 {ACTIVITY}')
    return 0

def _is_lexiang_authorized():
    """检查乐享 connector 是否实际授权（待 lexicon connector 接入后改）"""
    # 占位 — 真实检查需通过 wecom-cli 风格 OAuth
    return False

if __name__ == '__main__':
    sys.exit(main())
