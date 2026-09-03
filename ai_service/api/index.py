import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pymysql
from dotenv import load_dotenv

load_dotenv()

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

def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASS', 'root'),
        database=os.getenv('DB_NAME', 'emolink'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_family_data(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, family_name FROM families WHERE id = %s", (family_id,))
            family = cursor.fetchone()
            if not family:
                return None

            cursor.execute("""
                SELECT u.name as user_name, m.mood, m.created_at, fm.visibility, fm.role
                FROM moods m
                JOIN users u ON m.user_id = u.id
                JOIN family_members fm ON m.user_id = fm.user_id AND m.family_id = fm.family_id
                WHERE m.family_id = %s
                ORDER BY m.created_at DESC
                LIMIT 20
            """, (family_id,))
            moods = cursor.fetchall()

            for m in moods:
                if m['visibility'] == 'private':
                    m['user_name'] = 'An Anonymous Family Member'

            cursor.execute("""
                SELECT u.name as user_name, j.entry_text, j.created_at, fm.visibility, fm.role, j.id as journal_id
                FROM journal_entries j
                JOIN users u ON j.user_id = u.id
                JOIN family_members fm ON j.user_id = fm.user_id AND j.family_id = fm.family_id
                WHERE j.family_id = %s
                ORDER BY j.created_at DESC
                LIMIT 15
            """, (family_id,))
            journals = cursor.fetchall()

            for j in journals:
                if j['visibility'] == 'private':
                    j['user_name'] = 'An Anonymous Family Member'

            cursor.execute("SELECT summary FROM ai_context WHERE family_id = %s", (family_id,))
            context = cursor.fetchone()
            summary = context['summary'] if context and context['summary'] else ""

            return {
                "family_name": family["family_name"],
                "moods": moods,
                "journals": journals,
                "summary": summary
            }
    finally:
        conn.close()

def save_ai_results(family_id: int, topics: list, new_summary: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for t in topics:
                topic_text = t.get('topic', '')
                based_on = t.get('based_on', '')[:255]
                cursor.execute("""
                    INSERT INTO ai_topics (family_id, topic_text, based_on)
                    VALUES (%s, %s, %s)
                """, (family_id, topic_text, based_on))

            cursor.execute("""
                INSERT INTO ai_context (family_id, summary)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE summary = VALUES(summary)
            """, (family_id, new_summary))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_family_members(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id, u.name, fm.role, fm.visibility
                FROM users u
                JOIN family_members fm ON u.id = fm.user_id
                WHERE fm.family_id = %s
            """, (family_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def get_family_dynamics(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM family_dynamics
                WHERE family_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (family_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def detect_crisis_patterns(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.*, u.name as user_name
                FROM moods m
                JOIN users u ON m.user_id = u.id
                WHERE m.family_id = %s AND m.created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY m.created_at DESC
            """, (family_id,))
            recent_moods = cursor.fetchall()

            alerts = []
            negative_count = sum(1 for m in recent_moods if m['mood'] in ['sad', 'angry', 'anxious', 'frustrated'])
            if negative_count >= 5:
                alerts.append({
                    "type": "mood_pattern",
                    "severity": "high",
                    "message": f"Multiple negative moods detected ({negative_count} in past week)"
                })

            cursor.execute("""
                SELECT j.*, u.name as user_name
                FROM journal_entries j
                JOIN users u ON j.user_id = u.id
                WHERE j.family_id = %s AND j.created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """, (family_id,))
            recent_journals = cursor.fetchall()

            crisis_keywords = ['suicide', 'self harm', 'want to die', 'cutting', 'hurt myself', 'end it']
            for j in recent_journals:
                text_lower = j['entry_text'].lower()
                if any(k in text_lower for k in crisis_keywords):
                    alerts.append({
                        "type": "crisis_keyword",
                        "severity": "critical",
                        "message": f"Crisis keyword detected in journal entry",
                        "user_id": j['user_id'],
                        "journal_id": j['id']
                    })
                    cursor.execute("""
                        INSERT INTO crisis_alerts (family_id, user_id, alert_type, severity, description, journal_id)
                        VALUES (%s, %s, 'keyword_detection', 'critical', %s, %s)
                    """, (family_id, j['user_id'], f"Crisis keyword in journal entry", j['id']))

            if alerts:
                conn.commit()

            return alerts
    finally:
        conn.close()

def get_unresolved_crisis_alerts(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM crisis_alerts
                WHERE family_id = %s AND resolved = 0
                ORDER BY created_at DESC
            """, (family_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def resolve_crisis_alert(alert_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE crisis_alerts SET resolved = 1, resolved_at = NOW()
                WHERE id = %s
            """, (alert_id,))
        conn.commit()
    finally:
        conn.close()

def analyze_sentiment(journal_entry_id: int, entry_text: str):
    sentiment_score = 0.0
    anxiety_score = 0.0

    positive_words = ['happy', 'joy', 'excited', 'love', 'great', 'wonderful', 'amazing', 'good', 'better', 'best']
    negative_words = ['sad', 'angry', 'anxious', 'worried', 'frustrated', 'upset', 'depressed', 'hopeless']
    anxiety_words = ['worried', 'anxious', 'nervous', 'scared', 'afraid', 'panic', 'stress', 'overwhelmed']

    text_lower = entry_text.lower()

    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    anx_count = sum(1 for w in anxiety_words if w in text_lower)

    total_words = len(entry_text.split())
    if total_words > 0:
        sentiment_score = (pos_count - neg_count) / min(total_words, 20)
        anxiety_score = min(anx_count / 5, 1.0)

    sentiment_score = max(-1, min(1, sentiment_score))

    return {
        "sentiment_score": round(sentiment_score, 3),
        "anxiety_score": round(anxiety_score, 3),
        "label": "positive" if sentiment_score > 0.2 else ("negative" if sentiment_score < -0.2 else "neutral"),
        "word_counts": {
            "positive": pos_count,
            "negative": neg_count,
            "anxiety": anx_count
        }
    }

def save_sentiment(journal_entry_id: int, sentiment: dict):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sentiment_analysis (journal_entry_id, sentiment_score, anxiety_score, label)
                VALUES (%s, %s, %s, %s)
            """, (journal_entry_id, sentiment['sentiment_score'], sentiment['anxiety_score'], sentiment['label']))
        conn.commit()
    finally:
        conn.close()

def get_sentiment_for_journals(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT sa.*, je.entry_text, je.created_at as journal_date
                FROM sentiment_analysis sa
                JOIN journal_entries je ON sa.journal_entry_id = je.id
                WHERE je.family_id = %s
                ORDER BY je.created_at DESC
                LIMIT 20
            """, (family_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def predict_next_mood(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.user_id, u.name, m.mood, m.created_at
                FROM moods m
                JOIN users u ON m.user_id = u.id
                WHERE m.family_id = %s
                ORDER BY m.created_at DESC
                LIMIT 50
            """, (family_id,))
            moods = cursor.fetchall()

            predictions = {}
            members = get_family_members(family_id)

            for member in members:
                user_moods = [m for m in moods if m['user_id'] == member['id']]

                if not user_moods:
                    continue

                recent = [m['mood'] for m in user_moods[:5]]
                mood_counts = {}
                for mood in recent:
                    mood_counts[mood] = mood_counts.get(mood, 0) + 1

                if not mood_counts:
                    continue

                predicted = max(mood_counts, key=mood_counts.get)
                confidence = mood_counts[predicted] / len(recent)

                predictions[member['id']] = {
                    "user_id": member['id'],
                    "user_name": member['name'],
                    "predicted_mood": predicted,
                    "confidence": round(confidence, 2),
                    "based_on_recent": recent
                }

            return predictions
    finally:
        conn.close()

def save_topic_feedback(topic_id: int, user_id: int, feedback_type: str, notes: str = None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO topic_feedback (topic_id, user_id, feedback_type, notes)
                VALUES (%s, %s, %s, %s)
            """, (topic_id, user_id, feedback_type, notes))
        conn.commit()
    finally:
        conn.close()

def get_topic_effectiveness(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id, t.topic_text, t.based_on, t.created_at,
                       SUM(CASE WHEN tf.feedback_type = 'discussed' THEN 1 ELSE 0 END) as discussed_count,
                       SUM(CASE WHEN tf.feedback_type = 'helpful' THEN 1 ELSE 0 END) as helpful_count,
                       SUM(CASE WHEN tf.feedback_type = 'not_helpful' THEN 1 ELSE 0 END) as not_helpful_count
                FROM ai_topics t
                LEFT JOIN topic_feedback tf ON t.id = tf.topic_id
                WHERE t.family_id = %s
                GROUP BY t.id
                ORDER BY t.created_at DESC
            """, (family_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def analyze_family_dynamics(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT fm.role, COUNT(*) as count
                FROM moods m
                JOIN family_members fm ON m.user_id = fm.user_id AND m.family_id = fm.family_id
                WHERE m.family_id = %s AND m.created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY fm.role
            """, (family_id,))
            mood_counts = cursor.fetchall()

            cursor.execute("""
                SELECT fm.role, COUNT(*) as count
                FROM journal_entries j
                JOIN family_members fm ON j.user_id = fm.user_id AND j.family_id = fm.family_id
                WHERE j.family_id = %s AND j.created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY fm.role
            """, (family_id,))
            journal_counts = cursor.fetchall()

            cursor.execute("""
                SELECT fm.role, COUNT(*) as count
                FROM topic_feedback tf
                JOIN family_members fm ON tf.user_id = fm.user_id
                JOIN ai_topics t ON tf.topic_id = t.id
                WHERE t.family_id = %s
                GROUP BY fm.role
            """, (family_id,))
            feedback_counts = cursor.fetchall()

            parent_moods = next((c['count'] for c in mood_counts if c['role'] == 'parent'), 0)
            teen_moods = next((c['count'] for c in mood_counts if c['role'] == 'teen'), 0)
            total_moods = parent_moods + teen_moods

            parent_journals = next((c['count'] for c in journal_counts if c['role'] == 'parent'), 0)
            teen_journals = next((c['count'] for c in journal_counts if c['role'] == 'teen'), 0)

            parent_feedback = next((c['count'] for c in feedback_counts if c['role'] == 'parent'), 0)
            teen_feedback = next((c['count'] for c in feedback_counts if c['role'] == 'teen'), 0)

            communication_gap = abs(parent_moods - teen_moods) / max(total_moods, 1) if total_moods > 0 else 0

            dominant_role = "balanced"
            if parent_moods > teen_moods * 2:
                dominant_role = "parent_led"
            elif teen_moods > parent_moods * 2:
                dominant_role = "teen_led"

            dynamics = {
                "family_id": family_id,
                "communication_gap": round(communication_gap, 2),
                "dominant_role": dominant_role,
                "participation": {
                    "parent": {"moods": parent_moods, "journals": parent_journals, "feedback": parent_feedback},
                    "teen": {"moods": teen_moods, "journals": teen_journals, "feedback": teen_feedback}
                }
            }

            cursor.execute("""
                INSERT INTO family_dynamics (family_id, communication_gap, dominant_role, participation_data)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    communication_gap = VALUES(communication_gap),
                    dominant_role = VALUES(dominant_role),
                    participation_data = VALUES(participation_data)
            """, (family_id, dynamics['communication_gap'], dynamics['dominant_role'], str(dynamics['participation'])))

            conn.commit()
            return dynamics
    finally:
        conn.close()

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
    db_status = "unknown"
    try:
        conn = get_connection()
        conn.ping()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "emolink-ai",
        "version": "2.0",
        "database": db_status,
        "providers": {
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "missing",
            "claude": "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "missing"
        }
    }

@app.post("/generate-topics")
def generate_topics_endpoint(req: GenerateRequest):
    family_data = get_family_data(req.family_id)
    if not family_data:
        return {"status": "error", "message": "Family not found."}

    if not family_data["moods"] and not family_data["journals"]:
        return {"status": "empty", "message": "Not enough check-ins yet."}

    dynamics = get_family_dynamics(req.family_id)

    topics = []
    if len(family_data["journals"]) > 0:
        recent_journal = family_data["journals"][0]
        topics.append({
            "topic": f"What did {recent_journal.get('user_name', 'you')} mean when they wrote about '{recent_journal['entry_text'][:50]}...'",
            "based_on": "recent_journal"
        })

    if family_data["moods"]:
        moods_summary = {}
        for m in family_data["moods"][:5]:
            mood = m['mood']
            moods_summary[mood] = moods_summary.get(mood, 0) + 1
        top_mood = max(moods_summary, key=moods_summary.get)
        topics.append({
            "topic": f"Everyone seems to be feeling {top_mood} lately. What's been causing that?",
            "based_on": "mood_pattern"
        })

    if len(topics) < 3:
        topics.append({
            "topic": "What are you grateful for this week?",
            "based_on": "general"
        })
        topics.append({
            "topic": "Is there anything you're looking forward to?",
            "based_on": "general"
        })

    summary = f"Family check-in: {len(family_data['moods'])} moods, {len(family_data['journals'])} journal entries"
    save_ai_results(req.family_id, topics, summary)
    detect_crisis_patterns(req.family_id)

    return {
        "status": "ok",
        "topics": [t["topic"] for t in topics],
        "topic_details": topics,
        "summary": summary,
        "ensemble_used": False,
        "models_used": ["rule_based"]
    }

@app.post("/detect-crisis")
def detect_crisis(req: CrisisCheckRequest):
    try:
        alerts = detect_crisis_patterns(req.family_id)
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
        alerts = get_unresolved_crisis_alerts(family_id)
        return {"status": "ok", "alerts": alerts, "count": len(alerts)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/resolve-crisis/{alert_id}")
def resolve_crisis(alert_id: int):
    try:
        resolve_crisis_alert(alert_id)
        return {"status": "ok", "message": "Alert resolved"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/analyze-sentiment")
def analyze_sentiment_endpoint(req: SentimentRequest):
    if not req.entry_text:
        return {"status": "error", "message": "Entry text is required"}

    try:
        sentiment = analyze_sentiment(req.journal_entry_id, req.entry_text)
        save_sentiment(req.journal_entry_id, sentiment)

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
        sentiment_data = get_sentiment_for_journals(family_id)
        return {"status": "ok", "sentiment_entries": sentiment_data, "count": len(sentiment_data)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/predict-moods")
def predict_moods_endpoint(req: PredictionRequest):
    try:
        predictions = predict_next_mood(req.family_id)
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
        save_topic_feedback(req.topic_id, req.user_id, req.feedback_type, req.notes)
        points = 2 if req.feedback_type == 'discussed' else (1 if req.feedback_type == 'helpful' else 0)
        return {"status": "ok", "message": f"Feedback '{req.feedback_type}' recorded", "points_earned": points}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/topic-effectiveness/{family_id}")
def get_effectiveness(family_id: int):
    try:
        effectiveness = get_topic_effectiveness(family_id)
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
def analyze_dynamics_endpoint(req: DynamicsRequest):
    try:
        dynamics = analyze_family_dynamics(req.family_id)
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
        dynamics = get_family_dynamics(family_id)
        if not dynamics:
            return {"status": "not_found", "message": "Run analyze-dynamics first"}
        return {"status": "ok", "dynamics": dynamics}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/family-overview/{family_id}")
def family_overview(family_id: int):
    try:
        family_data = get_family_data(family_id)
        if not family_data:
            return {"status": "error", "message": "Family not found."}

        dynamics = get_family_dynamics(family_id)
        crisis_alerts = get_unresolved_crisis_alerts(family_id)
        predictions = predict_next_mood(family_id)

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
