echo --- Creating CollectOrg folder ---
set "PATH_FOLDER=C:\SVSHARE\User_Apps\OD_config_package\flows\CollectOrg"
mkdir "%PATH_FOLDER%"
echo --- Copying files ---
xcopy "%~dp0*" "%PATH_FOLDER%" /Y /I /Q /C /S /E /exclude:%~dp0exclude.txt
echo --- Installation completed. ---
