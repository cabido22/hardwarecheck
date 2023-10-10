echo off 
echo --- check_requirements folder on user folder ---
set temp=C:\Temp
mkdir %temp%\check_requirements
echo --- Coping files ---
xcopy %~dp0*.* %temp%\check_requirements\ /Y /I /Q /C /S /E /exclude:%~dp0exclude.txt
echo --- Installation completed. ---