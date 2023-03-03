python --version > version.txt
findstr "Python 3\." < version.txt > nul
echo %errorlevel%
del version.txt
if %errorlevel% equ 0 (
    python C:\SVSHARE\User_Apps\hardwarecheck\script\hardware_check_python3.py
    pause
    exit
) else (
    python C:\SVSHARE\User_Apps\hardwarecheck\script\hardware_check_python2.py
    pause
    exit
)

