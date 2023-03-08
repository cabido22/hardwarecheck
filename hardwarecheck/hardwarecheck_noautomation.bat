@echo off
echo --------------------------------------------------------------------------------
echo Executing boardinfo.py.
echo --------------------------------------------------------------------------------
python C:\SVSHARE\BoardInfo\BoardInfo.py
echo --------------------------------------------------------------------------------
echo Executing hardware_check.bat
echo --------------------------------------------------------------------------------
cmd /c C:\SVSHARE\User_Apps\hardwarecheck\hardware_check.bat
pause