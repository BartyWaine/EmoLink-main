# EmoLink 🌉

**AI-powered family emotional connection platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PHP 8.0+](https://img.shields.io/badge/PHP-8.0+-purple.svg)](https://www.php.net/downloads/)

EmoLink replaces traditional parental control apps with a safe, privacy-focused, and gamified environment where families can share their emotional state and get AI-guided conversation topics to foster meaningful connections.

---

## 🏗️ System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   PHP Frontend   │────▶│   MySQL Database │◀────│  AI Service │
│   (User Web)     │     │   (emolink)      │     │  (FastAPI)  │
└─────────────────┘     └──────────────────┘     └─────────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Google Gemini    │
                                              │ + Claude (opt)   │
                                              │ + GPT (opt)       │
                                              └──────────────────┘
```

## ✨ Features

### Core Features
- **5-Second Check-in** - Quick mood selection (Happy, Okay, Sad, Angry, Anxious)
- **Journal Entries** - Optional brief journal with each mood check-in
- **"Open Door" Signal** - Silent signal when teen is available to talk
- **Family Pulse** - Real-time view of family members' emotional states
- **Privacy Controls** - Granular visibility (shared/private) per entry

### AI Features (Competition-Ready)
- **Multi-Model Ensemble** - Gemini + Claude + GPT topic voting
- **Crisis Detection** - Automatic alerts for concerning mood patterns
- **Sentiment Analysis** - Deep emotional analysis of journal entries
- **Mood Prediction** - Predict next emotional states based on trends
- **Family Dynamics** - Engagement scoring and communication gap analysis
- **Topic Effectiveness** - Feedback loop to improve topic quality
- **Toxicity Filter** - Content safety for AI-generated outputs

### Gamification
- **Growth Tree** - Visual progress bar (seedling 🌱 → tree 🌳 → forest 🌲)
- **Points System** - Earn points for check-ins and topic discussions
- **Level Progression** - Every 50 points = new level

---

## 🚀 Quick Start

### Prerequisites
- PHP 8.0+
- MySQL 5.7+
- Python 3.10+
- Google Gemini API key

### 1. Clone & Setup Database

```bash
# Create database
mysql -u root -p
CREATE DATABASE emolink CHARACTER SET utf8mb4;
EXIT;

# Run schema
mysql -u root -p emolink < sql/schema.sql
```

### 2. Configure PHP App

Edit `app/config.php`:
```php
define('DB_HOST', 'localhost');
define('DB_NAME', 'emolink');
define('DB_USER', 'root');
define('DB_PASS', 'your_password');
```

### 3. Setup AI Service

```bash
cd ai_service
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Start AI service
uvicorn main:app --reload --port 8001
```

### 4. Start Web Server

Configure Apache/Nginx to serve `public/` as document root, or:
```bash
php -S localhost:8080 -t public/
```

### 5. Access Application

- **Web App**: http://localhost:8080
- **AI Docs**: http://localhost:8001/docs

---

## 📁 Project Structure

```
EmoLink/
├── public/                 # PHP frontend
│   ├── index.php          # Landing page
│   ├── login.php          # User login
│   ├── register.php       # User registration
│   ├── dashboard.php      # Main family dashboard
│   ├── checkin.php        # Mood check-in
│   ├── topics.php         # AI topic generation
│   ├── family.php         # Family management
│   ├── open_door.php      # Open door signal API
│   └── assets/            # CSS, JS, images
│
├── app/                   # PHP core
│   ├── config.php         # Database configuration
│   ├── db.php             # Database connection + helpers
│   └── auth.php           # Authentication helpers
│
├── ai_service/            # Python AI microservice
│   ├── main.py            # FastAPI application
│   ├── db.py              # Database operations
│   ├── gemini_client.py   # AI model clients
│   ├── context_builder.py # Prompt engineering
│   ├── requirements.txt   # Python dependencies
│   └── vercel.json        # Vercel deployment config
│
├── sql/
│   └── schema.sql         # Database schema
│
└── README.md
```

---

## 🌐 Deployment

### PHP Frontend → Railway/Render

Railway and Render support PHP + MySQL:

1. Push to GitHub
2. Connect repository to Railway/Render
3. Add environment variables
4. Deploy!

### AI Service → Vercel

See [ai_service/DEPLOY_VERCEL.md](ai_service/DEPLOY_VERCEL.md)

---

## 🤖 AI API

Base URL: `http://localhost:8001` (local) or your Vercel URL

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service status |
| `GET` | `/health` | Health check |
| `POST` | `/generate-topics` | Generate conversation topics |
| `POST` | `/detect-crisis` | Detect crisis patterns |
| `GET` | `/get-crisis-alerts/{family_id}` | Get alerts |
| `POST` | `/resolve-crisis/{alert_id}` | Resolve alert |
| `POST` | `/analyze-sentiment` | Analyze journal sentiment |
| `POST` | `/predict-moods` | Predict next moods |
| `POST` | `/topic-feedback` | Submit topic feedback |
| `POST` | `/analyze-dynamics` | Analyze family dynamics |

### Example Request

```bash
curl -X POST http://localhost:8001/generate-topics \
  -H "Content-Type: application/json" \
  -d '{"family_id": 1, "use_ensemble": true}'
```

---

## 🔒 Privacy & Safety

### Data Privacy
- Private mood/journal entries are anonymized before AI processing
- Users control visibility per entry (shared/private)
- Family members see "(Hidden)" for private entries

### AI Safety
- Pattern-based toxicity detection
- Crisis keyword filtering
- Content length limits
- Automatic sanitization

### Crisis Detection
- Prolonged negative mood monitoring
- Severity levels: low, medium, high, critical
- Real-time alerting to family

---

## 🏆 Competition Features

| Feature | Description | Impact |
|---------|-------------|--------|
| Multi-Model Ensemble | Voting between Gemini, Claude, GPT | Higher quality topics |
| Crisis Detection | Pattern recognition for at-risk youth | Safety first |
| Sentiment Analysis | Deep emotional understanding | Context-aware topics |
| Mood Prediction | Trend analysis + forecasting | Proactive engagement |
| Family Dynamics | Engagement gap detection | Targeted interventions |
| Topic Feedback | Learning loop for improvement | Continuous optimization |

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file.

---

*Built for the AI Youth Competition 2026* 🎯
