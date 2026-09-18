@echo off
chcp 65001 >nul
title Lobster E盘清理
set SRC=E:\tmp
set DST=G:\龙虾AI主控中心\_E盘清理归档\tmp_归档
if not exist "%DST%" mkdir "%DST%"
robocopy "%SRC%" "%DST%" /MOV /MINAGE:2 /R:1 /W:1 /NFL /NDL /NJH /NJS
echo %DATE% %TIME% E盘临时文件清理完成 >> "%DST%\clean_log.txt"
exit /b 0