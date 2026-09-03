import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

import db
import context_builder
import gemini_client

app = FastAPI(title="EmoLink AI Service", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    family_id: int
    use_ensemble: bool = True

class CrisisCheckRequest(BaseModel):
    family_id: int

class SentimentRequest(BaseModel):
    journal_entry_id: int
    entry_text: str

class FeedbackRequest(BaseModel):
    topic_id: int
    user_id: int
    feedback_type: str
    notes: Optional[str] = None

class DynamicsRequest(BaseModel):
    family_id: int

class PredictionRequest(BaseModel):
    family_id: int

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "EmoLink AI Service v2.0",
        "version": "2.0",
        "endpoints": ["/health", "/generate-topics", "/detect-crisis", "/analyze-sentiment", "/predict-moods", "/analyze-dynamics"]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "emolink-ai",
        "version": "2.0",
        "providers": {
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "missing",
            "claude": "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "missing"
        }
    }

@app.post("/generate-topics")
def generate_topics_endpoint(req: GenerateRequest):
    family_data = db.get_family_data(req.family_id)
    if not family_data:
        return {"status": "error", "message": "Family not found."}

    if not family_data["moods"] and not family_data["journals"]:
        return {"status": "empty", "message": "Not enough check-ins yet."}

    dynamics = db.get_family_dynamics(req.family_id)
    prompt = context_builder.build_prompt(
        family_data,
        include_dynamics=bool(dynamics),
        dynamics=dynamics
    )

    try:
        if req.use_ensemble:
            ai_result = gemini_client.generate_ensemble_topics(
                prompt,
                req.family_id,
                save_vote_func=db.save_model_votes
            )
        else:
            ai_result = gemini_client.generate_topics(prompt)

        db.save_ai_results(req.family_id, ai_result["topics"], ai_result["summary"])
        db.detect_crisis_patterns(req.family_id)

        return {
            "status": "ok",
            "topics": [t["topic"] for t in ai_result["topics"]],
            "topic_details": ai_result["topics"],
            "summary": ai_result.get("summary", ""),
            "ensemble_used": ai_result.get("ensemble_used", False),
            "models_used": ai_result.get("models_used", ["gemini"])
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/detect-crisis")
def detect_crisis(req: CrisisCheckRequest):
    try:
        alerts = db.detect_crisis_patterns(req.family_id)
        return {
            "status": "ok",
            "alerts_triggered": len(alerts),
            "alerts": alerts,
            "has_critical": any(a['severity'] == 'critical' for a in alerts),
            "has_high": any(a['severity'] == 'high' for a in alerts)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/get-crisis-alerts/{family_id}")
def get_crisis_alerts(family_id: int):
    try:
        alerts = db.get_unresolved_crisis_alerts(family_id)
        return {"status": "ok", "alerts": alerts, "count": len(alerts)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/resolve-crisis/{alert_id}")
def resolve_crisis(alert_id: int):
    try:
        db.resolve_crisis_alert(alert_id)
        return {"status": "ok", "message": "Alert resolved"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/analyze-sentiment")
def analyze_sentiment(req: SentimentRequest):
    if not req.entry_text:
        return {"status": "error", "message": "Entry text is required"}

    try:
        sentiment = gemini_client.analyze_text_sentiment(req.entry_text)
        db.analyze_sentiment(req.journal_entry_id, sentiment)

        crisis_indicators = []
        if sentiment['anxiety_score'] > 0.7:
            crisis_indicators.append("High anxiety detected")
        if sentiment['sentiment_score'] < -0.5:
            crisis_indicators.append("Strong negative sentiment")
        if any(k in req.entry_text.lower() for k in ['suicide', 'self harm', 'want to die', 'cutting']):
            crisis_indicators.append("CRISIS KEYWORD DETECTED")

        return {
            "status": "ok",
            "sentiment": sentiment,
            "crisis_indicators": crisis_indicators,
            "requires_attention": len(crisis_indicators) > 0
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/get-sentiment/{family_id}")
def get_sentiment(family_id: int):
    try:
        sentiment_data = db.get_sentiment_for_journals(family_id)
        return {"status": "ok", "sentiment_entries": sentiment_data, "count": len(sentiment_data)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/predict-moods")
def predict_moods(req: PredictionRequest):
    try:
        predictions = db.predict_next_mood(req.family_id)
        concerning = [
            p for p in predictions.values()
            if p.get('predicted_mood') in ['sad', 'anxious'] and p.get('confidence', 0) > 0.7
        ]
        return {
            "status": "ok",
            "predictions": list(predictions.values()),
            "concerning_predictions": concerning,
            "total_predicted": len(predictions)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/topic-feedback")
def submit_feedback(req: FeedbackRequest):
    valid_types = ['discussed', 'skipped', 'helpful', 'not_helpful']
    if req.feedback_type not in valid_types:
        return {"status": "error", "message": f"Invalid feedback type. Must be one of: {valid_types}"}

    try:
        db.save_topic_feedback(req.topic_id, req.user_id, req.feedback_type, req.notes)
        points = 2 if req.feedback_type == 'discussed' else (1 if req.feedback_type == 'helpful' else 0)
        return {"status": "ok", "message": f"Feedback '{req.feedback_type}' recorded", "points_earned": points}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/topic-effectiveness/{family_id}")
def get_effectiveness(family_id: int):
    try:
        effectiveness = db.get_topic_effectiveness(family_id)
        total = len(effectiveness)
        discussed = sum(1 for t in effectiveness if t['discussed_count'] > 0)
        helpful = sum(1 for t in effectiveness if t['helpful_count'] > t['not_helpful_count'])
        return {
            "status": "ok",
            "effectiveness": effectiveness,
            "summary": {
                "total_topics": total,
                "discussed_count": discussed,
                "helpful_count": helpful,
                "discussed_rate": round(discussed / total * 100, 1) if total > 0 else 0,
                "helpful_rate": round(helpful / total * 100, 1) if total > 0 else 0
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/analyze-dynamics")
def analyze_dynamics(req: DynamicsRequest):
    try:
        dynamics = db.analyze_family_dynamics(req.family_id)
        insights = []
        if dynamics:
            gap = dynamics.get('communication_gap', 0)
            if gap > 0.4:
                insights.append("Significant engagement gap - consider one-on-one time")
            elif gap > 0.2:
                insights.append("Slight communication imbalance")
            if dynamics.get('dominant_role') == 'parent_led':
                insights.append("Create space for teens to lead topics")
            elif dynamics.get('dominant_role') == 'teen_led':
                insights.append("Parents should ask more follow-up questions")
        return {"status": "ok", "dynamics": dynamics, "insights": insights}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/get-dynamics/{family_id}")
def get_dynamics(family_id: int):
    try:
        dynamics = db.get_family_dynamics(family_id)
        if not dynamics:
            return {"status": "not_found", "message": "Run analyze-dynamics first"}
        return {"status": "ok", "dynamics": dynamics}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/family-overview/{family_id}")
def family_overview(family_id: int):
    try:
        family_data = db.get_family_data(family_id)
        if not family_data:
            return {"status": "error", "message": "Family not found."}

        dynamics = db.get_family_dynamics(family_id)
        crisis_alerts = db.get_unresolved_crisis_alerts(family_id)
        predictions = db.predict_next_mood(family_id)

        recommendations = []
        if any(a['severity'] in ['critical', 'high'] for a in crisis_alerts):
            recommendations.append("CRITICAL: Some crisis alerts need immediate attention")
        if not recommendations:
            recommendations.append("Family is doing well!")

        return {
            "status": "ok",
            "family_name": family_data["family_name"],
            "mood_count": len(family_data["moods"]),
            "journal_count": len(family_data["journals"]),
            "dynamics": dynamics,
            "crisis_alerts": crisis_alerts,
            "crisis_count": len(crisis_alerts),
            "predictions": list(predictions.values()) if predictions else [],
            "recommendations": recommendations
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
