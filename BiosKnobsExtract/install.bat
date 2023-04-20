echo off 
echo --- Creating BiosKnobsExtract folder on user folder ---
mkdir %HOMEPATH%\BiosKnobsExtract
echo --- Coping files ---
xcopy %~dp0*.* %HOMEPATH%\BiosKnobsExtract\ /Y /I /Q /C /S /E /exclude:%~dp0exclude.txt
echo --- Installation completed. ---