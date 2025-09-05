@echo off
setlocal

echo ========================================
echo          GIT PULL SCRIPT
echo ========================================
echo.

REM Use the directory where this script is located
set "REPO_DIR=%~dp0"
cd /d "%REPO_DIR%"

echo Repository directory: %REPO_DIR%
echo.

REM Check if this is a git repository
git status >nul 2>&1
if errorlevel 1 (
    echo ERROR: This is not a Git repository!
    echo Please run this script from your Git project folder.
    pause
    exit /b 1
)

echo Pulling latest changes from remote...
git pull origin main

echo.
echo ========================================
echo Pull completed successfully!
echo ========================================
pause