@echo off
echo ========================================
echo EmoLink - GitHub Upload Script
echo ========================================
echo.

echo Checking Git status...
git status 2>nul
if errorlevel 1 (
    echo Initializing Git repository...
    git init
)
echo.

echo.
echo ========================================
echo IMPORTANT: Before running this script:
echo ========================================
echo 1. Create a NEW repository on GitHub.com
echo 2. Copy the repository URL
echo    (e.g., https://github.com/YOUR_USERNAME/EmoLink.git)
echo.
echo Press any key to continue when ready...
pause >nul
echo.

echo.
echo Enter your GitHub repository URL:
echo (e.g., https://github.com/YOUR_USERNAME/EmoLink.git)
set /p REPO_URL=
echo.

if "%REPO_URL%"=="" (
    echo ERROR: Repository URL is required!
    pause
    exit /b 1
)

echo.
echo Adding files to Git...
git add .
echo.

echo.
echo Enter commit message (or press Enter for default):
set /p COMMIT_MSG=
if "%COMMIT_MSG%"=="" set COMMIT_MSG=EmoLink v2.0 - AI-powered family emotional connection platform

git commit -m "%COMMIT_MSG%"
echo.

echo Adding remote origin...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
echo.

echo.
echo ========================================
echo Pushing to GitHub...
echo ========================================
echo.
echo If prompted for credentials:
echo - Username: YOUR_GITHUB_USERNAME
echo - Password: YOUR_GITHUB_TOKEN (NOT your password!)
echo.
echo To create a token: GitHub.com → Settings → Developer Settings
echo                   → Personal Access Tokens → Generate new token
echo.
git push -u origin main
echo.

echo.
echo ========================================
echo Done!
echo ========================================
echo.
echo Next steps for Vercel deployment:
echo 1. Go to https://vercel.com/new
echo 2. Import your GitHub repository
echo 3. Set root directory to: ai_service
echo 4. Add environment variables:
echo    - GEMINI_API_KEY
echo    - DB_HOST, DB_USER, DB_PASS, DB_NAME
echo 5. Deploy!
echo.
pause
