echo off 
echo --- Creating ReadKnobs folder on Desktop ---
mkdir %HOMEPATH%\ReadKnobs
echo --- Coping readknobs.py ---
xcopy %~dp0*.* %HOMEPATH%\ReadKnobs\ /Y /I /Q /C /S /E /exclude:%~dp0exclude.txt
echo --- Installation completed. ---