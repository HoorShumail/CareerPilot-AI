def build_feedback_prompt(session_payload: dict) -> str:
    return f"""
You are an AI interview feedback engine.
Return STRICT JSON ONLY.

Produce a JSON object with:
- strengths: array of strings
- weaknesses: array of strings
- missing_concepts: array of strings
- recommended_learning: array of strings
- expected_performance: string

Session:
{session_payload}

Return valid JSON only.
"""
