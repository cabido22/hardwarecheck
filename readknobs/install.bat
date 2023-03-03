echo off 
echo --- Creating ReadKnobs folder on Desktop ---
mkdir %HOMEPATH%\ReadKnobs
echo --- Coping readknobs.py ---
xcopy %~dp0*.* %HOMEPATH%\ReadKnobs\ /Y /I /Q /C /S /E
echo --- Installation completed. ---