@echo off
REM Obsidian sync: E (temp edits) -> G (master). Add-only mode (safe).
REM ONLY run after G drive is reconnected AND you edited files on E while G was away.
REM /E = copy subdirectories including empty; we do NOT use /MIR so G's other files are kept.
set SRC=E:\龙虾AI主控中心\Obsidian_E_bak_20260902
set DST=G:\龙虾AI主控中心\Obsidian
if not exist "%DST%" (
  echo [ERR] G drive vault not found: %DST%
  pause
  exit /b 1
)
echo Pushing E temp edits back to G (add-only, no delete) ...
robocopy "%SRC%" "%DST%" /E /R:1 /W:1 /NFL /NDL /NP /XX
echo Done. Review conflicts manually if any.
pause
