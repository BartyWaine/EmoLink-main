def build_prompt(family_data: dict, include_dynamics: bool = False, dynamics: dict = None) -> str:
    moods = family_data.get("moods", [])
    journals = family_data.get("journals", [])
    summary = family_data.get("summary", "")
    family_name = family_data.get("family_name", "the family")

    prompt = f"""You are an empathetic AI assistant helping the '{family_name}' family connect emotionally. You will analyze recent check-ins and generate warm, specific conversation topics.

"""

    if summary:
        prompt += f"Previous context summary:\n{summary}\n\n"

    if include_dynamics and dynamics:
        prompt += f"""Family Dynamics Analysis:
- Parent engagement level: {dynamics.get('parent_engagement_score', 0):.0%}
- Teen engagement level: {dynamics.get('teen_engagement_score', 0):.0%}
- Dominant role: {dynamics.get('dominant_role', 'balanced')}
- Suggested focus areas: {dynamics.get('suggested_focus_areas', 'general connection')}

"""

    prompt += "Recent Moods (last 2 weeks):\n"
    if moods:
        for m in moods:
            role_tag = f"[{m.get('role', 'member').upper()}]" if m.get('role') else ""
            prompt += f"- {m['user_name']} {role_tag} was feeling {m['mood']} on {m['created_at'].strftime('%Y-%m-%d')}\n"
    else:
        prompt += "- No recent mood check-ins recorded\n"

    prompt += "\nRecent Journal Entries:\n"
    if journals:
        for j in journals:
            text = j['entry_text'][:300] + ("..." if len(j['entry_text']) > 300 else "")
            role_tag = f"[{j.get('role', 'member').upper()}]" if j.get('role') else ""
            prompt += f"- {j['user_name']} {role_tag} wrote: \"{text}\"\n"
    else:
        prompt += "- No recent journal entries\n"

    dynamics_hint = ""
    if dynamics:
        gap = dynamics.get('communication_gap', 0)
        if gap > 0.3:
            dynamics_hint = "IMPORTANT: There's a communication gap in this family. Suggest topics that encourage the less-engaged family member(s) to participate."

    prompt += f"""
{dynamics_hint}

Based on the above information, suggest exactly 3 gentle, specific conversation topics this family could discuss to foster warmth and emotional connection.

Guidelines:
- For teens: Use relatable, low-pressure framing (e.g., "What's something that made you laugh this week?")
- For parents: Focus on active listening and validating feelings
- Topics should be specific, not generic ("How was school?" → "What was the most interesting thing you learned this week?")
- If mood trends show stress, suggest calming activities or gratitude practices
- If there's positive momentum, build on it with celebration topics

You MUST respond in valid JSON matching this exact schema:
{{
  "topics": [
    {{"topic": "...", "based_on": "Short rationale (max 120 chars) explicitly stating why this was chosen based on the provided data"}},
    {{"topic": "...", "based_on": "..."}},
    {{"topic": "...", "based_on": "..."}}
  ],
  "summary": "A detailed 2-3 sentence paragraph summarizing the family's recent emotional state, capturing specific themes and nuances."
}}
"""

    return prompt


def build_sentiment_prompt(journals: list) -> str:
    prompt = """Analyze the following journal entries and identify emotional patterns:

"""
    for j in journals:
        text = j.get('entry_text', '')[:500]
        user = j.get('user_name', 'Anonymous')
        prompt += f"\n--- Entry by {user} ---\n{text}\n"

    prompt += """
For each journal, provide:
1. Overall sentiment (positive, neutral, negative)
2. Anxiety indicators (worry, stress, fear words)
3. Hope indicators (optimism, excitement, gratitude)
4. Key themes (school, family, friends, health, future, etc.)

Respond in JSON format with the analysis.
"""
    return prompt


def build_prediction_prompt(mood_history: list) -> str:
    prompt = f"""Based on this mood history, predict the next likely mood and identify any concerning patterns:

"""
    for m in mood_history[-10:]:
        prompt += f"- {m['user_name']} ({m['role']}): {m['mood']} on {m['created_at'].strftime('%Y-%m-%d %H:%M')}\n"

    prompt += """

Identify:
1. Any declining trend in emotional wellbeing
2. Any prolonged negative moods (sad, anxious, angry)
3. Any sudden mood shifts
4. Predicted next mood for each family member
5. Any crisis warning signs

Respond in JSON format with your analysis.
"""
    return prompt


def build_topic_feedback_prompt(family_data: dict, topic: str) -> str:
    prompt = f"""A family member was asked about this conversation topic: "{topic}"

Family recent context:
"""
    moods = family_data.get("moods", [])[:5]
    for m in moods:
        prompt += f"- {m['user_name']}: {m['mood']}\n"

    prompt += """

Generate a personalized follow-up question or encouragement based on:
1. The topic itself
2. Recent family mood patterns
3. What might make this topic easier or more engaging to discuss

Keep it warm and encouraging. Respond in JSON format:
{{"follow_up": "...", "tip_for_discussion": "..."}}
"""
    return prompt