def build_learning_planner_prompt(profile_payload: dict, context_payload: dict) -> str:
    return f"""
You are an AI Learning Planner for a career intelligence platform.
Return STRICT JSON ONLY.

Produce a JSON object with:
- daily: array of strings
- weekly: array of strings
- monthly: array of strings
- quarterly: array of strings
- yearly: array of strings
- books: array of strings
- projects: array of strings
- certifications: array of strings
- courses: array of strings
- research_papers: array of strings
- open_source_contributions: array of strings
- generated_at: string

Profile:
{profile_payload}

Context:
{context_payload}

Return valid JSON only.
"""
