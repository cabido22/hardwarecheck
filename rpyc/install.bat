@echo off
echo --- Installing rpyc ---
start "" /wait wscript.exe "c:\SVShare\User_apps\OpenDebug\GeneratorUtils\invisible.vbs" "c:\SVShare\User_apps\OpenDebug\GeneratorUtils\background_start_rpyc.bat"

echo --- Executing rpyc_classic.py  ---
start "" /B cmd /c "python c:\python37\Scripts\rpyc_classic.py --host 0.0.0.0"

if %ERRORLEVEL% == 0 (
    echo Installation finished successfully.
) else (
    echo Error: %ERRORLEVEL%
)  
exit %errorlevel%