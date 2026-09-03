# EmoLink Deployment to Render

## Overview
This guide deploys EmoLink to Render.com for AI competition submission.

## Architecture
- **Frontend**: PHP 8.x on Apache (Render)
- **AI Service**: Python FastAPI (Vercel - already deployed at https://emolink-ai.vercel.app)
- **Database**: MySQL (Render Cloud)

## Step 1: Create Render Account
1. Go to https://render.com and sign up (free tier)
2. Verify email

## Step 2: Create MySQL Database
1. Dashboard → New → PostgreSQL (or MySQL if available)
2. Name: `emolink-db`
3. Region: Choose closest
4. Wait for provision (2-3 mins)
5. Copy connection string

Note: If Render doesn't offer free MySQL, use:
- **PlanetScale** (free tier available)
- **Neon** (PostgreSQL, free tier)
- **AWS RDS** (free tier eligible)

## Step 3: Deploy PHP Frontend

### Option A: Via Render Dashboard
1. Dashboard → New → PHP (Static is not what we need - we need PHP+Apache)
2. Actually, Render stopped supporting PHP directly. Use **Option B** instead.

### Option B: Deploy to Railway.app (Easier for PHP)
1. Go to https://railway.app
2. Sign up with GitHub
3. New Project → Deploy from GitHub repo
4. Select your EmoLink repo
5. Railway auto-detects PHP

OR use **000webhost** (free PHP hosting):
1. Go to https://www.000webhost.com
2. Upload via FileZilla FTP

### Option C: Use XAMPP + ngrok for demo
1. Run XAMPP (Apache + MySQL)
2. Start ngrok: `ngrok http 80`
3. Share the ngrok URL

## Step 4: Import Database Schema
1. Connect to MySQL:
   ```bash
   mysql -h <host> -u <user> -p <database> < schema.sql
   ```
2. Or use phpMyAdmin / TablePlus

## Step 5: Configure AI Service URL
Update `app/config.php`:
```php
define('AI_SERVICE_URL', 'https://emolink-ai.vercel.app');
```

## Step 6: Set Environment Variables
In your hosting dashboard, set:
- `DB_HOST` = your MySQL host
- `DB_NAME` = emolink
- `DB_USER` = your MySQL user
- `DB_PASS` = your MySQL password

## Quick Alternative: All on Render (Recommended)

### Deploy Python AI to Render
1. Create new Web Service
2. Connect GitHub repo, select `ai_service` folder
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables for API keys

### Deploy PHP Frontend to Render
Render discontinued PHP support. Use alternatives:
- **Fly.io** - Supports Docker (including PHP)
- ** Railway** - Check if PHP still supported
- **000webhost** - Pure PHP hosting, free

### Recommended Free Stack for Competition
| Component | Service | URL |
|-----------|---------|-----|
| Frontend (PHP) | 000webhost | https://www.000webhost.com |
| AI Backend | Vercel (deployed) | https://emolink-ai.vercel.app |
| Database | PlanetScale (free) | https://planetscale.com |

## Database Schema Import
After setting up MySQL, run these tables:
```sql
-- Run in phpMyAdmin or MySQL client
-- See sql/schema.sql for full schema
```
