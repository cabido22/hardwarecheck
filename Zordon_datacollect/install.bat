echo --- Creating Zordon_datacollect folder ---
set "PATH_FOLDER=%HOMEPATH%\Zordon_datacollect\"
mkdir "%PATH_FOLDER%"
echo --- Copying files ---
xcopy "%~dp0*" "%PATH_FOLDER%" /Y /I /Q /C /S /E /exclude:%~dp0exclude.txt
echo --- Installation completed. ---
