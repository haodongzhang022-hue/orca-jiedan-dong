# Obsidian 开机自启 —— 计划任务 AtLogOn（项目铁律：唯一可靠常驻）
# 零积分：纯本地 COM 调用，无需 schtasks（被安全策略禁用）
import pythoncom
import win32com.client

TASK_NAME = "Lobster_ObsidianLaunch"
EXE = r"G:\龙虾AI主控中心\ObsidianApp\Obsidian.exe"
CWD = r"G:\龙虾AI主控中心\ObsidianApp"

pythoncom.CoInitialize()
svc = win32com.client.Dispatch("Schedule.Service")
svc.Connect()
folder = svc.GetFolder("\\")

td = svc.NewTask(0)
td.RegistrationInfo.Description = "龙虾主控 Obsidian 1.13.7 开机自启（加载 E 盘主控库）"
td.Settings.AllowDemandStart = True
td.Settings.StartWhenAvailable = True
td.Settings.StopIfGoingOnBatteries = False
td.Settings.DisallowStartIfOnBatteries = False
td.Settings.ExecutionTimeLimit = "PT0S"  # 不限时（GUI 常驻）

# 触发器：用户登录时
trigger = td.Triggers.Create(9)  # TASK_TRIGGER_LOGON = 9
trigger.StartBoundary = "2026-09-02T17:00:00"
trigger.Delay = "PT30S"  # 登录后延后 30 秒，避免开机高峰抢资源

action = td.Actions.Create(0)  # TASK_ACTION_EXEC
action.Path = EXE
action.WorkingDirectory = CWD

# 6 = TASK_CREATE_OR_UPDATE, 3 = TASK_LOGON_INTERACTIVE_TOKEN
folder.RegisterTaskDefinition(TASK_NAME, td, 6, None, None, 3)

task = folder.GetTask(TASK_NAME)
print(f"REGISTERED: {TASK_NAME} | exe={EXE} | logon+30s | state={task.State}")
