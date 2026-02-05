@echo off
echo Building BatteryDataTool.exe...
pyinstaller.exe --onefile --noconsole --noconfirm --uac-admin --hidden-import fsspec "c:\Users\Ryu\battery\python\dataprocess\BatteryDataTool copy\BatteryDataTool.py" --distpath "c:\Users\Ryu\battery\python\dataprocess\BatteryDataTool copy\dist"
echo Build complete.
pause
