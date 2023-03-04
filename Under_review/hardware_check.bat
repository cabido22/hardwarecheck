@echo off
python -u --version 2>&1 | findstr "Python 2." > version.txt
del version.txt
if "%errorlevel%" equ "0" (
    python -u C:\SVSHARE\User_Apps\hardwarecheck\script\hardware_check_python2.py
    exit
) else (
    python -u C:\SVSHARE\User_Apps\hardwarecheck\script\hardware_check_python3.py
    exit
)