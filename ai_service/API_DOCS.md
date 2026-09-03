# EmoLink AI Service v2.0 API Documentation

## Overview

The EmoLink AI Service provides a comprehensive suite of emotional intelligence features for family wellness monitoring. It uses a multi-model ensemble approach for generating high-quality conversation topics and includes safety features like crisis detection.

## Architecture

```
PHP Frontend (Port 80)
    ↓ cURL
Python FastAPI (Port 8001)
    ↓
MySQL Database
    ↓
Google Gemini / Claude / GPT APIs
```

## Installation

```bash
cd ai_service
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn main:app --reload --port 8001
```

## API Endpoints

### Health & Status

#### `GET /`
Returns service status and available features.

#### `GET /health`
Returns health status of all configured AI providers.

### Topic Generation

#### `POST /generate-topics`
Generate AI conversation topics using ensemble voting.

**Request:**
```json
{
  "family_id": 1,
  "use_ensemble": true
}
```

**Response:**
```json
{
  "status": "ok",
  "topics": [
    "What was the most interesting thing you learned this week?",
    "Is there anything you'd like support with?",
    "What's something you're looking forward to?"
  ],
  "topic_details": [...],
  "summary": "Family emotional state summary...",
  "ensemble_used": true,
  "models_used": ["gemini", "claude"]
}
```

### Crisis Detection

#### `POST /detect-crisis`
Analyze mood patterns for crisis indicators.

**Request:**
```json
{
  "family_id": 1
}
```

**Response:**
```json
{
  "status": "ok",
  "alerts_triggered": 1,
  "alerts": [
    {
      "user_id": 5,
      "user_name": "John",
      "role": "teen",
      "alert_type": "prolonged_sad",
      "severity": "high",
      "message": "John (teen) has been feeling sad/anxious for 5/5 check-ins...",
      "is_resolved": false
    }
  ],
  "has_critical": false,
  "has_high": true
}
```

#### `GET /get-crisis-alerts/{family_id}`
Get all unresolved crisis alerts for a family.

#### `POST /resolve-crisis/{alert_id}`
Mark a crisis alert as acknowledged/resolved.

### Sentiment Analysis

#### `POST /analyze-sentiment`
Analyze emotional sentiment of a journal entry.

**Request:**
```json
{
  "journal_entry_id": 123,
  "entry_text": "Today was really stressful because of exams..."
}
```

**Response:**
```json
{
  "status": "ok",
  "sentiment": {
    "sentiment_score": -0.3,
    "anxiety_score": 0.7,
    "hope_score": 0.2,
    "keywords": ["stressed", "exams", "worried"],
    "themes": ["school", "pressure"]
  },
  "crisis_indicators": ["High anxiety detected"],
  "requires_attention": true
}
```

#### `GET /get-sentiment/{family_id}`
Get sentiment analysis history for a family.

### Mood Prediction

#### `POST /predict-moods`
Predict next mood states for family members based on patterns.

**Request:**
```json
{
  "family_id": 1
}
```

**Response:**
```json
{
  "status": "ok",
  "predictions": [
    {
      "user_id": 1,
      "user_name": "John",
      "role": "teen",
      "predicted_mood": "okay",
      "confidence": 0.75,
      "trend": "stable",
      "prediction_basis": "Based on 4 recent check-ins"
    }
  ],
  "concerning_predictions": [],
  "total_predicted": 3
}
```

### Topic Feedback

#### `POST /topic-feedback`
Submit feedback on a conversation topic.

**Request:**
```json
{
  "topic_id": 45,
  "user_id": 1,
  "feedback_type": "discussed",
  "notes": "Great conversation at dinner!"
}
```

Valid `feedback_type` values:
- `discussed` - Family discussed this topic (+2 points)
- `skipped` - Topic was skipped
- `helpful` - Topic was helpful (+1 point)
- `not_helpful` - Topic wasn't helpful

#### `GET /topic-effectiveness/{family_id}`
Get topic effectiveness statistics.

**Response:**
```json
{
  "status": "ok",
  "effectiveness": [...],
  "summary": {
    "total_topics": 20,
    "discussed_count": 12,
    "helpful_count": 15,
    "discussed_rate": 60.0,
    "helpful_rate": 75.0
  }
}
```

### Family Dynamics

#### `POST /analyze-dynamics`
Analyze family communication patterns and dynamics.

**Request:**
```json
{
  "family_id": 1
}
```

**Response:**
```json
{
  "status": "ok",
  "dynamics": {
    "parent_engagement_score": 0.75,
    "teen_engagement_score": 0.45,
    "communication_gap": 0.30,
    "dominant_role": "parent_led",
    "suggested_focus_areas": "Encourage more teen participation"
  },
  "insights": [
    "There's a significant engagement gap between family members.",
    "Try more teen-led conversations or activities they enjoy."
  ]
}
```

#### `GET /get-dynamics/{family_id}`
Get previously analyzed family dynamics.

### Comprehensive Overview

#### `GET /family-overview/{family_id}`
Get a complete family wellness snapshot.

**Response:**
```json
{
  "status": "ok",
  "family_name": "Smith Family",
  "mood_count": 25,
  "journal_count": 12,
  "dynamics": {...},
  "crisis_alerts": [...],
  "crisis_count": 0,
  "predictions": [...],
  "recommendations": [
    "Family is doing well! Keep the positive momentum going."
  ]
}
```

## Database Tables

### New Tables Added

- `crisis_alerts` - Stores detected crisis patterns
- `sentiment_analysis` - Stores journal sentiment scores
- `topic_feedback` - Tracks topic effectiveness
- `model_votes` - Stores ensemble voting data
- `mood_predictions` - Stores mood predictions
- `family_dynamics` - Caches family dynamics analysis

## Safety Features

### Toxicity Filter
- Pattern-based detection for harmful content
- Crisis keyword detection
- Content length limits
- Automatic sanitization

### Crisis Detection
- Prolonged negative mood detection (sad/anxious)
- Sudden mood spike detection
- Severity levels: low, medium, high, critical
- Real-time alerting

### Privacy
- Private mood/journal data anonymized before AI processing
- Role-based topic suggestions
- Granular visibility controls

## Multi-Model Ensemble

The system can use multiple AI models for topic generation:

1. **Google Gemini** (required) - Primary model
2. **Anthropic Claude** (optional) - Secondary model
3. **OpenAI GPT** (optional) - Tertiary model

When multiple models are configured, topics are:
- Generated by each model independently
- Voted on based on relevance and quality
- Top 3 selected by vote count

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | No |
| `OPENAI_API_KEY` | OpenAI GPT API key | No |
| `DB_HOST` | MySQL host | No (default: 127.0.0.1) |
| `DB_USER` | MySQL username | No (default: root) |
| `DB_PASS` | MySQL password | No |
| `DB_NAME` | Database name | No (default: emolink) |
| `AI_PORT` | Service port | No (default: 8001) |

## Competition-Ready Features

1. **Multi-AI Ensemble** - Competing systems use single models; ensemble voting provides higher quality
2. **Crisis Detection** - Unique safety feature for youth wellness competitions
3. **Sentiment Analysis** - Deep emotional understanding beyond simple mood tags
4. **Predictive Analytics** - Proactive wellness monitoring
5. **Family Dynamics** - Unique engagement scoring and gap detection
6. **Topic Effectiveness** - Feedback loops for continuous improvement
7. **Role-Based Suggestions** - Personalized for parents vs teens
8. **Safety Filtering** - Content safety for AI-generated topics