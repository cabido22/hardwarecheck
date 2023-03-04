echo --- Creating HardwareCheck folder ---
set "PATH_FOLDER=C:\SVSHARE\User_Apps\hardwarecheck\"
mkdir "%PATH_FOLDER%"
echo --- Coping files ---
xcopy "%~dp0hardware_check.bat" "%PATH_FOLDER%" /Y /I /Q /C /S /E
xcopy "%~dp0HardwareCheck_NoAutomation.bat" "%PATH_FOLDER%" /Y /I /Q /C /S /E
xcopy "%~dp0yaml" "%PATH_FOLDER%\yaml\" /Y /I /Q /C /S /E
xcopy "%~dp0conf" "%PATH_FOLDER%\conf\" /Y /I /Q /C /S /E
xcopy "%~dp0script" "%PATH_FOLDER%\script\" /Y /I /Q /C /S /E
echo --- Installation completed. ---