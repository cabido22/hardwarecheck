echo --- Creating HardwareCheck folder ---
set "PATH_FOLDER=C:\SVSHARE\User_Apps\hardwarecheck\"
mkdir "%PATH_FOLDER%"
echo --- Copying files ---
xcopy "%~dp0*" "%PATH_FOLDER%" /Y /I /Q /C /S /E /exclude:%~dp0exclude.txt
echo --- Installation completed. ---
