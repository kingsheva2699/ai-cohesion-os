@echo off
setlocal
cd /d "%~dp0"
echo AI Cohesion OS GitHub publish helper
echo.
echo Make sure you already created an EMPTY public repo on GitHub named ai-cohesion-os.
echo Do NOT initialize it with README/license/gitignore.
echo.
set /p REMOTE=Paste remote URL, e.g. https://github.com/YOUR_USERNAME/ai-cohesion-os.git: 
if "%REMOTE%"=="" (
  echo No remote URL provided.
  pause
  exit /b 1
)
git remote remove origin >nul 2>nul
git remote add origin "%REMOTE%"
git branch -M main
git push -u origin main
if errorlevel 1 (
  echo.
  echo Push failed. If Git asks for login, authenticate with GitHub/Git Credential Manager and rerun this file.
  pause
  exit /b 1
)
echo.
echo Published successfully.
pause
