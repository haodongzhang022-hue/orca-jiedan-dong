# -*- coding: utf-8 -*-
"""夜星空01 三件套硬校验：PSD 尺寸/72PPI 元数据 + PNG dpi + zip 一致性（零外部依赖，纯手写解析）"""
import struct, os, zipfile, json

BASE = r"E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/01_正在执行实单/【20260812_夜星空01_PSD设计+网页+Word交付】"
DRAFTS = os.path.join(BASE, "各版本稿件")
WEB = os.path.join(BASE, "工程源文件", "web")
FINAL = os.path.join(BASE, "最终交付文件")

def psd_info(path):
    """从 8BPS 头 + 图像资源块读尺寸与分辨率"""
    with open(path, "rb") as f:
        head = f.read(26)
        assert head[:4] == b"8BPS", "not PSD"
        ver = struct.unpack(">H", head[4:6])[0]
        channels, height, width, depth, mode = struct.unpack(">HIIHH", head[12:26])
        # 跳过颜色模式数据 + 图像资源段
        f.seek(26)
        cm_len = struct.unpack(">I", f.read(4))[0]
        f.seek(4 + cm_len, 1)
        ir_len = struct.unpack(">I", f.read(4))[0]
        ird = f.read(ir_len)
    res = None
    i = 0
    while i + 12 <= len(ird):
        sig = ird[i:i+4]
        if sig != b"8BIM":
            i += 1
            continue
        rid = struct.unpack(">H", ird[i+4:i+6])[0]
        nlen = ird[i+6]  # Pascal 字符串长度：1 字节
        pname = ((1 + nlen) + 1) // 2 * 2  # 含长度字节，补齐到偶数
        dlen = struct.unpack(">I", ird[i+6+pname:i+10+pname])[0]
        dstart = i + 10 + pname
        if rid == 0x1005 and dlen >= 16:  # resolutionInfo
            hres = struct.unpack(">I", ird[dstart:dstart+4])[0]
            hfrac = struct.unpack(">H", ird[dstart+4:dstart+6])[0]
            res = hres + hfrac / 65536.0
        i = dstart + dlen + (1 if dlen % 2 else 0)
    return {"w": width, "h": height, "depth": depth, "mode": mode, "ver": ver, "dpi": res}

def png_dpi(path):
    """读 PNG pHYs 块"""
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not PNG"
    i, dpi = 8, None
    while i + 8 <= len(data):
        ln = struct.unpack(">I", data[i:i+4])[0]
        typ = data[i+4:i+8]
        if typ == b"pHYs":
            x, y, unit = struct.unpack(">IIB", data[i+8:i+8+9])
            dpi = x if unit == 1 else None
            break
        i += 12 + ln
    return dpi

report = {"psd": {}, "png": {}, "zip": {}, "issues": []}

for name in ["夜星空01_Logo_v1", "夜星空01_Banner_v1", "夜星空01_海报_v1"]:
    psdp, pngp = os.path.join(DRAFTS, name + ".psd"), os.path.join(DRAFTS, name + ".png")
    if os.path.exists(psdp):
        report["psd"][name] = psd_info(psdp)
    if os.path.exists(pngp):
        report["png"][name] = {"size": os.path.getsize(pngp), "dpi": png_dpi(pngp)}

# web assets
for a in ["logo.png", "banner.png", "poster.png"]:
    p = os.path.join(WEB, "assets", a)
    if os.path.exists(p):
        report.setdefault("web_assets", {})[a] = {"size": os.path.getsize(p), "dpi": png_dpi(p)}

# zip 包
for z in os.listdir(FINAL):
    if z.endswith(".zip"):
        zp = os.path.join(FINAL, z)
        with zipfile.ZipFile(zp) as zf:
            names = zf.namelist()
            report["zip"][z] = {"files": len(names), "names": names, "test": zf.testzip() is None}

# 判定
for k, v in report["psd"].items():
    if v["w"] != 1920:
        report["issues"].append(f"{k}.psd 宽 {v['w']} != 1920")
    if v.get("dpi") not in (None,) and v["dpi"] and abs(v["dpi"] - 72) > 0.01:
        report["issues"].append(f"{k}.psd dpi {v['dpi']} != 72")
for k, v in report["png"].items():
    if v.get("dpi") != 72:
        report["issues"].append(f"{k}.png dpi {v.get('dpi')} != 72")

print(json.dumps(report, ensure_ascii=False, indent=1))
