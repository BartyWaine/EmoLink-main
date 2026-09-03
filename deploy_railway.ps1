# EmoLink Railway Deployment Script
# Run this in PowerShell: .\deploy_railway.ps1

Write-Host "EmoLink Railway Deployment Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "EmoLink deployment ready for Railway"
} else {
    Write-Host "Git already initialized" -ForegroundColor Green
}

# Check if remote exists
$remote = git remote -v 2>$null
if ($remote.Count -eq 0) {
    Write-Host "Adding GitHub remote..." -ForegroundColor Yellow
    Write-Host "Please create a repo at https://github.com/new named 'emolink-main'" -ForegroundColor Yellow
    $username = Read-Host "Enter your GitHub username"
    git remote add origin "https://github.com/$username/emolink-main.git"
}

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git branch -M main
git push -u origin main --force

Write-Host ""
Write-Host "Deployment Steps:" -ForegroundColor Green
Write-Host "1. Go to https://railway.app" -ForegroundColor Cyan
Write-Host "2. Sign up with GitHub" -ForegroundColor Cyan
Write-Host "3. Click 'New Project' -> 'Deploy from GitHub'" -ForegroundColor Cyan
Write-Host "4. Select 'emolink-main' repository" -ForegroundColor Cyan
Write-Host "5. Add MySQL database to the project" -ForegroundColor Cyan
Write-Host "6. Configure environment variables:" -ForegroundColor Cyan
Write-Host "   - DB_HOST, DB_NAME, DB_USER, DB_PASS" -ForegroundColor Gray
Write-Host "   - AI_SERVICE_URL = https://emolink-ai.vercel.app" -ForegroundColor Gray
Write-Host ""
Write-Host "See DEPLOY_RAILWAY.md for full instructions" -ForegroundColor Green
