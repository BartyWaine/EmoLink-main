# Deploying EmoLink AI Service to Vercel

## Prerequisites
1. Vercel account (free tier works)
2. MySQL database (Railway, PlanetScale, or similar)
3. Google Gemini API key

## Environment Variables (Vercel Dashboard)

Go to your Vercel project → Settings → Environment Variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `GEMINI_API_KEY` | your_gemini_key | Required |
| `ANTHROPIC_API_KEY` | your_claude_key | Optional |
| `OPENAI_API_KEY` | your_gpt_key | Optional |
| `DB_HOST` | your_db_host | MySQL host |
| `DB_USER` | your_db_user | MySQL user |
| `DB_PASS` | your_db_password | MySQL password |
| `DB_NAME` | emolink | Database name |
| `PORT` | 8001 | Vercel sets this |

## Deploy Steps

### Option 1: GitHub Integration (Recommended)

1. Push the `ai_service/` folder to GitHub
2. Go to https://vercel.com/new
3. Import the repository
4. Set root directory to `ai_service`
5. Add environment variables
6. Deploy!

### Option 2: Vercel CLI

```bash
npm i -g vercel
cd ai_service
vercel
# Follow prompts, add env vars when asked
```

## After Deployment

Your AI service will be available at:
```
https://your-project.vercel.app/
```

Update your PHP app's `config.php`:
```php
define('AI_SERVICE_URL', 'https://your-project.vercel.app');
```

## API Endpoints

After deployment, these endpoints will be available:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service status |
| GET | `/health` | Health check with provider status |
| POST | `/generate-topics` | Generate conversation topics |
| POST | `/detect-crisis` | Detect crisis patterns |
| GET | `/get-crisis-alerts/{family_id}` | Get unresolved alerts |
| POST | `/resolve-crisis/{alert_id}` | Mark alert resolved |
| POST | `/analyze-sentiment` | Analyze journal sentiment |
| GET | `/get-sentiment/{family_id}` | Get sentiment history |
| POST | `/predict-moods` | Predict next moods |
| POST | `/topic-feedback` | Submit topic feedback |
| GET | `/topic-effectiveness/{family_id}` | Topic stats |
| POST | `/analyze-dynamics` | Analyze family dynamics |
| GET | `/get-dynamics/{family_id}` | Get dynamics data |
| GET | `/family-overview/{family_id}` | Complete family snapshot |

## Troubleshooting

### Cold Start
Vercel functions may take 1-2 seconds on first request (cold start). This is normal.

### Timeout
Default timeout is 30 seconds. For long AI requests, consider:
- Using streaming responses
- Implementing async job queue
- Increasing timeout in vercel.json

### Database Connection
If database connection fails:
1. Check environment variables are set correctly
2. Verify MySQL allows external connections
3. Use a connection pooler like PlanetScale's Prisma or Railway's MySQL

## Free Tier Limits

- 100GB bandwidth/month
- 100,000 serverless function invocations/day
- 10s timeout per function (request), 30s for Python
