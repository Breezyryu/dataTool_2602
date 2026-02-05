@echo off
echo Building BatteryDataTool.exe...

REM 현재 배치 파일 위치로 이동
cd /d "%~dp0"

".venv\Scripts\pyinstaller.exe" ^
    --onefile ^
    --noconsole ^
    --noconfirm ^
    --uac-admin ^
    --hidden-import fsspec ^
    "BatteryDataTool.py" ^
    --distpath "."

echo Build complete.
pause
