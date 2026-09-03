import os
import pymysql
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASS', ''),
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
                FROM family_members fm
                JOIN users u ON fm.user_id = u.id
                WHERE fm.family_id = %s
            """, (family_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def detect_crisis_patterns(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id as user_id, u.name, m.mood, m.created_at, fm.role
                FROM moods m
                JOIN users u ON m.user_id = u.id
                JOIN family_members fm ON m.user_id = fm.user_id AND m.family_id = fm.family_id
                WHERE m.family_id = %s AND m.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY m.created_at DESC
            """, (family_id,))
            recent_moods = cursor.fetchall()

            alerts = []
            user_moods = {}
            for m in recent_moods:
                uid = m['user_id']
                if uid not in user_moods:
                    user_moods[uid] = {'name': m['name'], 'role': m['role'], 'moods': []}
                user_moods[uid]['moods'].append({'mood': m['mood'], 'created_at': m['created_at']})

            for uid, data in user_moods.items():
                moods_list = data['moods']
                if len(moods_list) < 3:
                    continue

                sad_count = sum(1 for m in moods_list if m['mood'] in ['sad', 'anxious'])
                total = len(moods_list)

                if total >= 3:
                    sad_ratio = sad_count / total
                    if sad_ratio >= 0.8:
                        severity = 'critical' if sad_ratio >= 1.0 else 'high'
                        alerts.append({
                            'user_id': uid,
                            'user_name': data['name'],
                            'role': data['role'],
                            'alert_type': 'prolonged_sad' if sad_ratio >= 0.8 else 'prolonged_anxious',
                            'severity': severity,
                            'message': f"{data['name']} ({data['role']}) has been feeling sad/anxious for {sad_count}/{total} check-ins in the past week.",
                            'is_resolved': False
                        })

            for uid, data in user_moods.items():
                if len(data['moods']) >= 5:
                    recent_5 = data['moods'][:5]
                    if recent_5[0]['mood'] in ['sad', 'anxious'] and all(m['mood'] in ['happy', 'okay'] for m in recent_5[1:]):
                        alerts.append({
                            'user_id': uid,
                            'user_name': data['name'],
                            'role': data['role'],
                            'alert_type': 'mood_spike',
                            'severity': 'medium',
                            'message': f"Sudden mood improvement detected for {data['name']} - possible masking or positive event.",
                            'is_resolved': False
                        })

            for alert in alerts:
                cursor.execute("""
                    INSERT INTO crisis_alerts (family_id, user_id, alert_type, severity, message)
                    VALUES (%s, %s, %s, %s, %s)
                """, (family_id, alert['user_id'], alert['alert_type'], alert['severity'], alert['message']))

            conn.commit()
            return alerts
    finally:
        conn.close()

def get_unresolved_crisis_alerts(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT ca.*, u.name as user_name
                FROM crisis_alerts ca
                JOIN users u ON ca.user_id = u.id
                WHERE ca.family_id = %s AND ca.is_resolved = FALSE
                ORDER BY
                    CASE ca.severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    ca.created_at DESC
            """, (family_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def resolve_crisis_alert(alert_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE crisis_alerts
                SET is_resolved = TRUE, resolved_at = NOW()
                WHERE id = %s
            """, (alert_id,))
        conn.commit()
    finally:
        conn.close()

def analyze_sentiment(journal_entry_id: int, sentiment_data: dict):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sentiment_analysis
                (journal_entry_id, sentiment_score, anxiety_score, hope_score, keywords, themes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                journal_entry_id,
                sentiment_data.get('sentiment_score', 0),
                sentiment_data.get('anxiety_score', 0),
                sentiment_data.get('hope_score', 0),
                ','.join(sentiment_data.get('keywords', [])),
                ','.join(sentiment_data.get('themes', []))
            ))
        conn.commit()
    finally:
        conn.close()

def get_sentiment_for_journals(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT sa.*, j.entry_text, u.name as user_name
                FROM sentiment_analysis sa
                JOIN journal_entries j ON sa.journal_entry_id = j.id
                JOIN users u ON j.user_id = u.id
                JOIN family_members fm ON j.user_id = fm.user_id AND j.family_id = fm.family_id
                WHERE j.family_id = %s AND fm.visibility = 'shared'
                ORDER BY sa.created_at DESC
                LIMIT 10
            """, (family_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def predict_next_mood(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id as user_id, u.name, fm.role,
                       m.mood, m.created_at,
                       LAG(m.mood) OVER (PARTITION BY m.user_id ORDER BY m.created_at) as prev_mood,
                       LAG(m.mood, 2) OVER (PARTITION BY m.user_id ORDER BY m.created_at) as prev_prev_mood
                FROM moods m
                JOIN users u ON m.user_id = u.id
                JOIN family_members fm ON m.user_id = fm.user_id AND m.family_id = fm.family_id
                WHERE m.family_id = %s
                ORDER BY m.created_at DESC
            """, (family_id,))

            all_moods = cursor.fetchall()
            predictions = {}

            user_moods = {}
            for m in all_moods:
                uid = m['user_id']
                if uid not in user_moods:
                    user_moods[uid] = {'name': m['name'], 'role': m['role'], 'history': []}
                if len(user_moods[uid]['history']) < 5:
                    user_moods[uid]['history'].append({
                        'mood': m['mood'],
                        'prev': m['prev_mood'],
                        'prev_prev': m['prev_prev_mood']
                    })

            mood_weights = {'happy': 5, 'okay': 4, 'anxious': 2, 'sad': 1, 'angry': 1}

            for uid, data in user_moods.items():
                history = data['history']
                if len(history) < 2:
                    continue

                recent = history[:3]
                mood_scores = []
                for h in recent:
                    scores = [mood_weights.get(h['mood'], 3)]
                    if h['prev']:
                        scores.append(mood_weights.get(h['prev'], 3))
                    mood_scores.append(sum(scores) / len(scores))

                avg_score = sum(mood_scores) / len(mood_scores)

                if avg_score >= 4.5:
                    predicted = 'happy'
                    confidence = min(0.95, 0.7 + (avg_score - 4) * 0.1)
                elif avg_score >= 3.5:
                    predicted = 'okay'
                    confidence = min(0.85, 0.6 + (avg_score - 3) * 0.1)
                elif avg_score >= 2:
                    predicted = 'anxious'
                    confidence = min(0.75, 0.5 + (avg_score - 2) * 0.1)
                else:
                    predicted = 'sad'
                    confidence = min(0.8, 0.5 + (2 - avg_score) * 0.1)

                trend = "stable"
                if len(history) >= 2:
                    if history[0]['mood'] in ['sad', 'angry', 'anxious'] and history[1]['mood'] in ['happy', 'okay']:
                        trend = "improving"
                    elif history[0]['mood'] in ['happy', 'okay'] and history[1]['mood'] in ['sad', 'angry', 'anxious']:
                        trend = "declining"

                predictions[uid] = {
                    'user_id': uid,
                    'user_name': data['name'],
                    'role': data['role'],
                    'predicted_mood': predicted,
                    'confidence': round(confidence, 2),
                    'trend': trend,
                    'prediction_basis': f"Based on {len(history)} recent check-ins"
                }

                cursor.execute("""
                    INSERT INTO mood_predictions
                    (family_id, user_id, predicted_mood, confidence, prediction_basis)
                    VALUES (%s, %s, %s, %s, %s)
                """, (family_id, uid, predicted, confidence, predictions[uid]['prediction_basis']))

            conn.commit()
            return predictions
    finally:
        conn.close()

def validate_mood_prediction(prediction_id: int, actual_mood: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE mood_predictions
                SET is_accurate = (predicted_mood = %s), validated_at = NOW()
                WHERE id = %s
            """, (actual_mood, prediction_id))
        conn.commit()
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

            if feedback_type == 'discussed':
                cursor.execute("""
                    INSERT INTO tree_progress (family_id, points)
                    VALUES (
                        (SELECT family_id FROM ai_topics WHERE id = %s),
                        2
                    )
                    ON DUPLICATE KEY UPDATE points = points + 2
                """, (topic_id,))
            elif feedback_type == 'helpful':
                cursor.execute("""
                    INSERT INTO tree_progress (family_id, points)
                    VALUES (
                        (SELECT family_id FROM ai_topics WHERE id = %s),
                        1
                    )
                    ON DUPLICATE KEY UPDATE points = points + 1
                """, (topic_id,))

        conn.commit()
    finally:
        conn.close()

def get_topic_effectiveness(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    t.id, t.topic_text, t.created_at,
                    COUNT(DISTINCT tf.id) as feedback_count,
                    SUM(CASE WHEN tf.feedback_type = 'discussed' THEN 1 ELSE 0 END) as discussed_count,
                    SUM(CASE WHEN tf.feedback_type = 'helpful' THEN 1 ELSE 0 END) as helpful_count,
                    SUM(CASE WHEN tf.feedback_type = 'not_helpful' THEN 1 ELSE 0 END) as not_helpful_count
                FROM ai_topics t
                LEFT JOIN topic_feedback tf ON t.id = tf.topic_id
                WHERE t.family_id = %s
                GROUP BY t.id
                ORDER BY t.created_at DESC
                LIMIT 20
            """, (family_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def analyze_family_dynamics(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id, u.name, fm.role,
                       COUNT(DISTINCT m.id) as mood_count,
                       COUNT(DISTINCT j.id) as journal_count,
                       MAX(m.created_at) as last_mood,
                       MAX(j.created_at) as last_journal
                FROM family_members fm
                JOIN users u ON fm.user_id = u.id
                LEFT JOIN moods m ON u.id = m.user_id AND m.family_id = fm.family_id AND m.created_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                LEFT JOIN journal_entries j ON u.id = j.user_id AND j.family_id = fm.family_id AND j.created_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                WHERE fm.family_id = %s
                GROUP BY u.id
            """, (family_id,))
            members = cursor.fetchall()

            if not members:
                return None

            parents = [m for m in members if m['role'] == 'parent']
            teens = [m for m in members if m['role'] == 'teen']

            parent_engagement = sum(p['mood_count'] + p['journal_count'] * 2 for p in parents) / (len(parents) * 28) if parents else 0
            teen_engagement = sum(t['mood_count'] + t['journal_count'] * 2 for t in teens) / (len(teens) * 28) if teens else 0

            parent_engagement = min(1.0, parent_engagement)
            teen_engagement = min(1.0, teen_engagement)

            communication_gap = abs(parent_engagement - teen_engagement)

            dominant_role = 'balanced'
            if parent_engagement > teen_engagement * 1.5:
                dominant_role = 'parent_led'
            elif teen_engagement > parent_engagement * 1.5:
                dominant_role = 'teen_led'

            focus_areas = []
            if communication_gap > 0.3:
                focus_areas.append('Improve communication balance between parents and teens')
            if teen_engagement < 0.4:
                focus_areas.append('Encourage more teen participation')
            if parent_engagement < 0.4:
                focus_areas.append('Increase parent engagement')
            if not focus_areas:
                focus_areas.append('Maintain current positive engagement')

            dynamics_data = {
                'parent_engagement_score': round(parent_engagement, 2),
                'teen_engagement_score': round(teen_engagement, 2),
                'communication_gap': round(communication_gap, 2),
                'dominant_role': dominant_role,
                'suggested_focus_areas': '; '.join(focus_areas)
            }

            cursor.execute("""
                INSERT INTO family_dynamics (family_id, parent_engagement_score, teen_engagement_score, communication_gap, dominant_role, suggested_focus_areas)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    parent_engagement_score = VALUES(parent_engagement_score),
                    teen_engagement_score = VALUES(teen_engagement_score),
                    communication_gap = VALUES(communication_gap),
                    dominant_role = VALUES(dominant_role),
                    suggested_focus_areas = VALUES(suggested_focus_areas)
            """, (family_id, dynamics_data['parent_engagement_score'], dynamics_data['teen_engagement_score'],
                  dynamics_data['communication_gap'], dynamics_data['dominant_role'], dynamics_data['suggested_focus_areas']))

            conn.commit()
            return dynamics_data
    finally:
        conn.close()

def get_family_dynamics(family_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM family_dynamics WHERE family_id = %s", (family_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def save_model_votes(family_id: int, model_name: str, topic_text: str, based_on: str, generation_round: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO model_votes (family_id, model_name, topic_text, based_on, generation_round)
                VALUES (%s, %s, %s, %s, %s)
            """, (family_id, model_name, topic_text, based_on, generation_round))
        conn.commit()
    finally:
        conn.close()

def get_ensemble_topics(family_id: int, generation_round: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT topic_text, based_on, model_name, vote_score
                FROM model_votes
                WHERE family_id = %s AND generation_round = %s
                ORDER BY vote_score DESC, created_at DESC
            """, (family_id, generation_round))
            all_votes = cursor.fetchall()

            topic_scores = {}
            for v in all_votes:
                key = v['topic_text']
                if key not in topic_scores:
                    topic_scores[key] = {'text': key, 'based_on': v['based_on'], 'score': 0, 'models': []}
                topic_scores[key]['score'] += v['vote_score']
                topic_scores[key]['models'].append(v['model_name'])

            sorted_topics = sorted(topic_scores.values(), key=lambda x: x['score'], reverse=True)
            return sorted_topics[:3]
    finally:
        conn.close()

def update_model_vote(topic_text: str, family_id: int, generation_round: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE model_votes
                SET vote_score = vote_score + 1
                WHERE topic_text = %s AND family_id = %s AND generation_round = %s
            """, (topic_text, family_id, generation_round))
        conn.commit()
    finally:
        conn.close()