def build_followup_prompt(question: str, answer: str) -> str:
    return f"""
You are an AI interviewer creating a conversational follow-up question.
Return STRICT JSON ONLY.

Produce a JSON object with:
- follow_up_question: string
- category: string

Question:
{question}

Answer:
{answer}

Return valid JSON only.
"""
