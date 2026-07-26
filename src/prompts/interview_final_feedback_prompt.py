from typing import Any, Dict


def build_interview_final_feedback_prompt(interview_data: Dict[str, Any]) -> str:
    return f"""
You are an expert AI Technical Interview Evaluator.

Return STRICT JSON ONLY.

Evaluate the COMPLETE interview transcript.

Base your evaluation ONLY on the candidate's answers.

Do NOT use placeholder values.

Do NOT invent information.

Return EXACTLY this JSON structure:

{{
  "overall_score": 84,
  "technical_score": 82,
  "communication_score": 86,
  "confidence_score": 79,

  "strengths": [
    "Strong Python knowledge",
    "Good understanding of Machine Learning"
  ],

  "weaknesses": [
    "Needs stronger cloud knowledge",
    "Limited production deployment experience"
  ],

  "missing_concepts": [
    "Kubernetes",
    "CI/CD",
    "AWS"
  ],

  "recommended_learning": [
    "AWS",
    "Docker",
    "System Design"
  ],

  "hire_recommendation": "Hire with reservations",

  "summary": "Candidate demonstrates strong AI fundamentals but needs additional production engineering experience.",

  "next_steps": [
    "Study Kubernetes",
    "Practice System Design",
    "Build production AI projects"
  ]
}}

Interview Transcript:

{interview_data}

Return STRICT JSON ONLY.
"""