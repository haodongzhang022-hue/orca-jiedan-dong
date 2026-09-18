# Obsidian 快捷方式自愈守护 —— 360 桌面整理删了也能自动长回来
# 零积分：纯本地 COM + 文件操作，不调任何云端模型
# 用法: python obsidian_lnk_guardian.py   （由计划任务每 30 分钟拉起）
import os
import sys
import pythoncom
import win32com.shell.shell as shell

LOG = r"E:\龙虾AI主控中心\MCP服务\logs\obsidian_lnk_guardian.log"

TARGET = r"G:\龙虾AI主控中心\ObsidianApp\Obsidian.exe"
CWD = r"G:\龙虾AI主控中心\ObsidianApp"
NAME = "Obsidian知识库"
DESC = "龙虾主控 Obsidian 知识库 1.13.7（直达 E 盘主控库）"

# 三处落点：用户桌面（带热键）/ 公共桌面（360 清理兜底）/ 开始菜单
PLACES = [
    (r"C:\Users\Administrator\Desktop", True),
    (r"C:\Users\Public\Desktop", False),
    (r"C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Start Menu\Programs", False),
]

# 额外检测：Obsidian 进程是否存活（可选自拉起）
AUTO_RELAUNCH = True


def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        from datetime import datetime
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")


def make_lnk(dest, hotkey):
    os.makedirs(dest, exist_ok=True)
    lnk = os.path.join(dest, NAME + ".lnk")
    pythoncom.CoInitialize()
    sl = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, pythoncom.IID_IPersistFile
    )
    sll = sl.QueryInterface(shell.IID_IShellLinkW)
    sll.SetPath(TARGET)
    sll.SetWorkingDirectory(CWD)
    sll.SetIconLocation(TARGET, 0)
    sll.SetDescription(DESC)
    if hotkey:
        sll.SetHotkey((0x06 << 8) | 0x4F)  # Ctrl+Alt+O
    sl.QueryInterface(pythoncom.IID_IPersistFile).Save(lnk, 0)
    return lnk


def obsidian_running():
    import subprocess
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Obsidian.exe"], capture_output=True)
    txt = r.stdout.decode("gbk", errors="ignore")
    # 判活标准：存在内存占用 > 20MB 的进程（排除 64K 僵尸）
    return txt.count("Obsidian.exe") > 0


def relaunch():
    import subprocess
    subprocess.Popen([TARGET], cwd=CWD)


def main():
    fixed = []
    for dest, hotkey in PLACES:
        lnk = os.path.join(dest, NAME + ".lnk")
        if not os.path.exists(lnk):
            make_lnk(dest, hotkey)
            fixed.append(dest)
    if fixed:
        log(f"自愈重建快捷方式: {fixed}")
    else:
        log("三处快捷方式完好")
    if AUTO_RELAUNCH and not obsidian_running():
        # 仅在无人值守时段（0:00-8:00 之外）不强制拉起，避免打扰
        from datetime import datetime
        if 8 <= datetime.now().hour < 24:
            relaunch()
            log("Obsidian 未运行 -> 已自动拉起")


if __name__ == "__main__":
    main()
