@echo off


:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo After installation, make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

cd /d "%~dp0"
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple




echo Setup Complete!^(^>_^<^)! ...
pause
exit /b 1