import os
import json
import re
try:
    from google import genai
except ImportError:
    import google.generativeai as genai
    genai = type('obj', (object, dict), {'configure': lambda **kwargs: None})()
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

class Topic(BaseModel):
    topic: str
    based_on: str = Field(..., max_length=255)

class GeminiResponse(BaseModel):
    topics: list[Topic]
    summary: str

class SentimentResponse(BaseModel):
    sentiment_score: float = Field(..., ge=-1, le=1)
    anxiety_score: float = Field(..., ge=0, le=1)
    hope_score: float = Field(..., ge=0, le=1)
    keywords: list[str]
    themes: list[str]

TOXIC_PATTERNS = [
    r'\b(hate|kill|die|suicide|self.?harm|cutting|overdose)\b',
    r'\b(bomb|attack|weapon)\b',
    r'\b(drugs?|cocaine|heroin|weed)\s*sell',
    r'\b(predator|pedophile|grooming)\b',
    r'\b(threat|menace)\b',
]

CRISIS_KEYWORDS = [
    'suicide', 'self harm', 'cutting', 'overdose', 'kill myself',
    'want to die', 'better off dead', 'no point living'
]

def is_safe_content(text: str) -> tuple[bool, Optional[str]]:
    text_lower = text.lower()

    for pattern in TOXIC_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, f"Content flagged by safety pattern: {pattern}"

    for keyword in CRISIS_KEYWORDS:
        if keyword in text_lower:
            return False, f"Crisis keyword detected: {keyword}"

    if len(text) > 5000:
        return False, "Content exceeds maximum length"

    return True, None

def sanitize_topic(topic_text: str) -> str:
    topic_text = topic_text.strip()
    topic_text = re.sub(r'\s+', ' ', topic_text)
    topic_text = topic_text[:500]

    if not topic_text.endswith(('?', '.', '!', ':')):
        topic_text += '?'

    return topic_text

def generate_with_gemini(prompt: str, temperature: float = 0.7) -> Optional[dict]:
    try:
        import google.genai as genai_client
        client = genai_client.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": temperature
            }
        )

        data = json.loads(response.text)
        validated = GeminiResponse(**data)

        safe_topics = []
        for t in validated.topics:
            safe_topic = sanitize_topic(t.topic)
            is_safe, _ = is_safe_content(safe_topic)
            if is_safe:
                safe_topics.append({"topic": safe_topic, "based_on": t.based_on[:120]})

        while len(safe_topics) < 3:
            safe_topics.append({"topic": "How has everyone's day been?", "based_on": "General check-in default"})

        return {
            "topics": safe_topics[:3],
            "summary": validated.summary[:500] if validated.summary else ""
        }
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

def generate_with_claude(prompt: str, api_key: str = None) -> Optional[dict]:
    try:
        import anthropic
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt + "\n\nRespond in JSON with topics array and summary field."}]
        )

        text = response.content[0].text
        data = json.loads(text)
        validated = GeminiResponse(**data)

        safe_topics = []
        for t in validated.topics:
            safe_topic = sanitize_topic(t.topic)
            is_safe, _ = is_safe_content(safe_topic)
            if is_safe:
                safe_topics.append({"topic": safe_topic, "based_on": t.based_on[:120]})

        while len(safe_topics) < 3:
            safe_topics.append({"topic": "What's on your mind today?", "based_on": "Default fallback"})

        return {
            "topics": safe_topics[:3],
            "summary": validated.summary[:500] if validated.summary else ""
        }
    except Exception as e:
        print(f"Claude error: {e}")
        return None

def generate_with_gpt(prompt: str, api_key: str = None) -> Optional[dict]:
    try:
        import openai
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a family emotional support AI. Generate 3 conversation topics and a summary."},
                {"role": "user", "content": prompt}
            ]
        )

        data = json.loads(response.choices[0].message.content)
        validated = GeminiResponse(**data)

        safe_topics = []
        for t in validated.topics:
            safe_topic = sanitize_topic(t.topic)
            is_safe, _ = is_safe_content(safe_topic)
            if is_safe:
                safe_topics.append({"topic": safe_topic, "based_on": t.based_on[:120]})

        while len(safe_topics) < 3:
            safe_topics.append({"topic": "What made you smile today?", "based_on": "Positive default"})

        return {
            "topics": safe_topics[:3],
            "summary": validated.summary[:500] if validated.summary else ""
        }
    except Exception as e:
        print(f"GPT error: {e}")
        return None

def generate_ensemble_topics(prompt: str, family_id: int, save_vote_func=None) -> dict:
    results = []
    generation_round = 1

    gemini_result = generate_with_gemini(prompt, temperature=0.7)
    if gemini_result:
        results.append(("gemini", gemini_result))

    if save_vote_func:
        for r in results:
            for topic in r[1]['topics']:
                save_vote_func(family_id, r[0], topic['topic'], topic['based_on'], generation_round)

    if len(results) == 0:
        return {
            "topics": [
                {"topic": "How has everyone's day been?", "based_on": "Default - no AI available"},
                {"topic": "Is there anything you'd like support with?", "based_on": "Default"},
                {"topic": "What's something you're looking forward to?", "based_on": "Default"}
            ],
            "summary": "AI services were unavailable. Family has been engaging with the platform.",
            "ensemble_used": False,
            "models_used": []
        }

    all_topics = []
    for model_name, result in results:
        for topic in result['topics']:
            topic_copy = topic.copy()
            topic_copy['model'] = model_name
            topic_copy['vote'] = 1
            all_topics.append(topic_copy)

    topic_votes = {}
    for t in all_topics:
        key = t['topic'].lower()[:100]
        if key not in topic_votes:
            topic_votes[key] = {'topic': t['topic'], 'based_on': t['based_on'], 'votes': 0, 'models': []}
        topic_votes[key]['votes'] += t['vote']
        topic_votes[key]['models'].append(t['model'])

    sorted_topics = sorted(topic_votes.values(), key=lambda x: x['votes'], reverse=True)
    final_topics = []
    for i, t in enumerate(sorted_topics[:3]):
        is_safe, reason = is_safe_content(t['topic'])
        if not is_safe:
            continue
        final_topics.append({
            "topic": t['topic'],
            "based_on": t['based_on'] + f" (voted by {', '.join(set(t['models']))})"
        })

    while len(final_topics) < 3:
        final_topics.append({
            "topic": f"What would make today better for everyone?",
            "based_on": "Default filler topic"
        })

    combined_summary = " ".join(set(r[1]['summary'] for r in results))[:500]

    return {
        "topics": final_topics[:3],
        "summary": combined_summary,
        "ensemble_used": len(results) > 1,
        "models_used": [r[0] for r in results]
    }

def analyze_text_sentiment(text: str, prompt_override: str = None) -> dict:
    if prompt_override:
        prompt = prompt_override
    else:
        prompt = f"""Analyze this journal entry and return a JSON object with:
{{
    "sentiment_score": -1.0 to 1.0 (negative to positive),
    "anxiety_score": 0.0 to 1.0 (0=none, 1=very high),
    "hope_score": 0.0 to 1.0 (0=none, 1=very hopeful),
    "keywords": ["list of emotional keywords found"],
    "themes": ["main themes like 'school', 'friends', 'family', 'health', etc"]
}}

Journal entry: {text[:2000]}

Respond with ONLY valid JSON."""

    try:
        import google.genai as genai_client
        client = genai_client.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        data = json.loads(response.text)

        validated = SentimentResponse(**data)

        return {
            "sentiment_score": max(-1.0, min(1.0, validated.sentiment_score)),
            "anxiety_score": max(0.0, min(1.0, validated.anxiety_score)),
            "hope_score": max(0.0, min(1.0, validated.hope_score)),
            "keywords": validated.keywords[:10],
            "themes": validated.themes[:5]
        }
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Sentiment analysis error: {e}")
        keywords = []
        text_lower = text.lower()

        anxiety_words = ['worried', 'anxious', 'nervous', 'stressed', 'scared', 'fear', 'panic']
        hope_words = ['excited', 'happy', 'hopeful', 'looking forward', 'cant wait', 'optimistic']

        for w in anxiety_words:
            if w in text_lower:
                keywords.append(w)
        for w in hope_words:
            if w in text_lower:
                keywords.append(w)

        sentiment = 0.0
        for hw in hope_words:
            if hw in text_lower:
                sentiment += 0.3
        for aw in anxiety_words:
            if aw in text_lower:
                sentiment -= 0.2

        return {
            "sentiment_score": max(-1.0, min(1.0, sentiment)),
            "anxiety_score": sum(0.2 for w in anxiety_words if w in text_lower),
            "hope_score": sum(0.2 for w in hope_words if w in text_lower),
            "keywords": keywords,
            "themes": ["general"]
        }

def generate_topics(prompt: str) -> dict:
    return generate_with_gemini(prompt) or {
        "topics": [
            {"topic": "What was the best part of your week?", "based_on": "Fallback standard topic"},
            {"topic": "Is there anything you'd like support with right now?", "based_on": "Fallback standard topic"},
            {"topic": "What's something you're looking forward to?", "based_on": "Fallback standard topic"}
        ],
        "summary": "The family has been experiencing a mix of emotions recently."
    }