@echo off
set LOG=E:\tmp_cleanup.log
echo [%date% %time%] E盘tmp清理 开始 >> %LOG%
echo -- MarvisUpdate (1.5GB, 可再生更新缓存) >> %LOG%
rd /s /q "E:\tmp\MarvisUpdate" >> %LOG% 2>&1
echo -- sogou_updater_pkg* (可再生安装包) >> %LOG%
for /d %%d in ("E:\tmp\sogou_updater_pkg*") do rd /s /q "%%d" >> %LOG% 2>&1
echo -- 根目录散落 *.tmp *.pyc 临时/编译残留 >> %LOG%
del /q /f "E:\tmp\*.tmp" >> %LOG% 2>&1
del /q /f "E:\tmp\*.pyc" >> %LOG% 2>&1
echo [%date% %time%] E盘tmp清理 完成 >> %LOG%
