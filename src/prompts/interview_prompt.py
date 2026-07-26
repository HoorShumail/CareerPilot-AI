def build_interview_prompt(profile_payload: dict, context_payload: dict) -> str:
    return f"""
You are an AI Mock Interview generator for a career intelligence platform.
Return STRICT JSON ONLY.

Produce a JSON object with:
- interview_type: string
- target_role: string
- target_company: string
- difficulty: string
- duration_seconds: integer
- questions: array of objects with question and category
- feedback: object with strengths, weaknesses, missing_concepts, recommended_learning, expected_performance

Profile:
{profile_payload}

Context:
{context_payload}

Return valid JSON only.
"""
