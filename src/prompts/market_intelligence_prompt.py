def build_market_intelligence_prompt(profile_payload: dict, context_payload: dict) -> str:
    return f"""
You are a Market Intelligence engine for a career intelligence platform.
Return STRICT JSON ONLY.

Produce a JSON object with:
- demanded_skills: array of strings
- technologies: array of strings
- certifications: array of strings
- frameworks: array of strings
- ai_tools: array of strings
- cloud_providers: array of strings
- programming_languages: array of strings
- trends: array of strings
- generated_at: string

Profile:
{profile_payload}

Context:
{context_payload}

Return valid JSON only.
"""
