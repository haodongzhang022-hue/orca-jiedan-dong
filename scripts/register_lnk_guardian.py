# 注册快捷方式自愈守护为计划任务（每 30 分钟一次，开机也跑一次）
# 零积分：纯本地 COM
import pythoncom
import win32com.client

PY = r"C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
SCRIPT = r"E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\obsidian_lnk_guardian.py"
TASK_NAME = "Lobster_ObsidianLnkGuardian"

pythoncom.CoInitialize()
svc = win32com.client.Dispatch("Schedule.Service")
svc.Connect()
folder = svc.GetFolder("\\")

td = svc.NewTask(0)
td.RegistrationInfo.Description = "Obsidian 快捷方式自愈守护（360 桌面清理兜底）"
td.Settings.AllowDemandStart = True
td.Settings.StartWhenAvailable = True
td.Settings.StopIfGoingOnBatteries = False
td.Settings.DisallowStartIfOnBatteries = False
td.Settings.ExecutionTimeLimit = "PT5M"
td.Settings.MultipleInstances = 2  # 已有实例则跳过，不重入

# 触发器1：登录时
t1 = td.Triggers.Create(9)  # LOGON
t1.StartBoundary = "2026-09-02T17:00:00"
t1.Delay = "PT60S"

# 触发器2：每 30 分钟重复
t2 = td.Triggers.Create(2)  # TIME
t2.StartBoundary = "2026-09-02T17:00:00"
t2.Repetition.Interval = "PT30M"
t2.Repetition.Duration = "P1D"
t2.Repetition.StopAtDurationEnd = False

action = td.Actions.Create(0)
action.Path = PY
action.Arguments = f'"{SCRIPT}"'
action.WorkingDirectory = r"E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts"

folder.RegisterTaskDefinition(TASK_NAME, td, 6, None, None, 3)
task = folder.GetTask(TASK_NAME)
task.Run("")
print(f"REGISTERED: {TASK_NAME} | logon + 每30分钟 | state={task.State}")
