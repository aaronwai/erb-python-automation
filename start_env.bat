@echo off
chcp 65001 >nul
echo ======================================
echo Activating virtual environment [automation_env]
echo ======================================
call automation_env\Scripts\activate.bat
echo.
echo Venv activated, (automation_env) prompt ready.
echo Run your python scripts here.
echo.
cmd /k
