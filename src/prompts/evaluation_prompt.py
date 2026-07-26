def build_evaluation_prompt(question: str, answer: str) -> str:
    return f"""
You are an AI interview evaluator.
Return STRICT JSON ONLY.

Produce a JSON object with:
- technical_score: number between 0 and 10
- communication_score: number between 0 and 10
- confidence_score: number between 0 and 10
- completeness: number between 0 and 10
- correctness: number between 0 and 10
- improvement_suggestions: array of strings
- follow_up_question: string

Question:
{question}

Answer:
{answer}

Return valid JSON only.
"""
