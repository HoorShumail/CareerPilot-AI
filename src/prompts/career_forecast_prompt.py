def build_career_forecast_prompt(profile_payload: dict, context_payload: dict) -> str:
    return f"""
You are an AI Career Forecasting engine for a career intelligence platform.
Return STRICT JSON ONLY.

Produce a JSON object with:
- forecasts: array of objects, one for 6 months, 1 year, 3 years, 5 years
  each object must include: horizon, predicted_job_titles, salary_projection, hiring_probability, promotion_probability, career_trajectory, confidence_score, estimated_timeline
- summary: string
- generated_at: string

Profile:
{profile_payload}

Context:
{context_payload}

Return valid JSON only.
"""
