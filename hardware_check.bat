@echo off
python --version > version.txt
findstr "Python 3\." < version.txt > nul
del version.txt
if %errorlevel% equ 0 (
    python C:\SVSHARE\User_Apps\hardwarecheck\script\hardware_check_python3.py
    exit
) else (
    python C:\SVSHARE\User_Apps\hardwarecheck\script\hardware_check_python2.py
    exit
)

