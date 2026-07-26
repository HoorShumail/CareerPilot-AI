def build_career_twin_prompt(profile_payload: dict, context_payload: dict) -> str:
    return f"""
You are the Career Digital Twin engine for a professional career platform.
Return STRICT JSON ONLY.

You must analyze the user's current career profile and supporting context and produce a compact JSON payload with the following keys:
- career_summary: object with summary, headline, narrative
- experience_level: string
- strongest_skills: object with skills list and rationale
- weakest_skills: object with skills list and rationale
- ai_maturity_score: number between 0 and 100
- confidence_score: number between 0 and 100
- preferred_industries: array of strings
- preferred_roles: array of strings
- preferred_locations: array of strings
- salary_expectations: object with min, max, currency, rationale
- remote_preference: object with preference, rationale
- skills: object with mastered_skills, learning_skills, missing_skills, trending_skills, obsolete_skills
- strengths: object with biggest_strengths, supporting_evidence
- weaknesses: object with biggest_weaknesses, supporting_evidence
- career_gap_analysis: object with missing_experience, missing_education, missing_certifications, biggest_strengths, biggest_weaknesses
- growth_summary: object with overall_growth_score, readiness_score, promotion_readiness, ai_career_level
- learning_recommendations: object with courses, certifications, projects, books
- learning_roadmap: object with short_term, medium_term, long_term
- skill_intelligence: object with current_focus, next_focus, risk_signals
- career_gap_analysis: object with gaps, evidence

Profile:
{profile_payload}

Context:
{context_payload}

Return valid JSON only.
"""
