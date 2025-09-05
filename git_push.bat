@echo off
setlocal

echo ========================================
echo          GIT PUSH SCRIPT
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

REM Check git status
echo Current status:
git status

echo.
echo Adding all changes to staging...
git add .

echo.
set "commit_message=AutoCommit: %date% %time%"
echo Committing changes: %commit_message%
git commit -m "%commit_message%"

echo.
echo Pushing to remote repository...
git push origin main

echo.
echo ========================================
echo Push completed successfully!
echo ========================================
pause