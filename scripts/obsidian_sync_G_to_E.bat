@echo off
REM Obsidian sync: G (master) -> E (hot backup). Mirror mode.
REM Run by double-click. Requires robocopy (built into Windows).
set SRC=G:\龙虾AI主控中心\Obsidian
set DST=E:\龙虾AI主控中心\Obsidian_E_bak_20260902
if not exist "%SRC%" (
  echo [ERR] G drive vault not found: %SRC%
  pause
  exit /b 1
)
echo Mirroring G -> E ...
robocopy "%SRC%" "%DST%" /MIR /R:1 /W:1 /NFL /NDL /NP
echo Done. E backup at: %DST%
pause
