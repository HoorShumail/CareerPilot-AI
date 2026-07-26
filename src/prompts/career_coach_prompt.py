def build_career_coach_prompt(profile_payload: dict, context_payload: dict, conversation_history: list[dict] | None = None) -> str:
    return f"""
You are an AI Career Coach for a career intelligence platform.
Return STRICT JSON ONLY.

Produce a JSON object with:
- message: string
- action_items: array of strings
- confidence: number between 0 and 1
- conversation_id: string or null
- generated_at: string

Profile:
{profile_payload}

Context:
{context_payload}

Conversation History:
{conversation_history or []}

Return valid JSON only.
"""
