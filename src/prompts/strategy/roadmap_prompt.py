import json
from typing import Any, Dict


def build_roadmap_prompt(gap_payload: Dict[str, Any], profile_payload: Dict[str, Any], context_payload: Dict[str, Any]) -> str:
    return (
        "You are a career roadmap planner.\n"
        "Create a practical learning roadmap based on the skill gaps, profile, and context below.\n\n"
        "CRITICAL RULES:\n"
        "1. Return ONLY a single valid JSON object. No markdown, no code fences, no explanations.\n"
        "2. Do NOT wrap the response in ```json or ``` or any other formatting.\n"
        "3. Do NOT include any text before or after the JSON object.\n"
        "4. Every string value MUST use double quotes.\n"
        "5. Do NOT use trailing commas.\n"
        "6. Return ONLY the JSON object described below.\n\n"
        "Required JSON schema:\n"
        "{\n"
        '  "weekly_roadmap": [{"title": "string", "topic": "string", "duration_weeks": 1, "priority": "high|medium|low", "dependencies": ["string"], "expected_outcomes": ["string"], "timeframe": "string"}],\n'
        '  "monthly_roadmap": [{"title": "string", "topic": "string", "duration_weeks": 1, "priority": "high|medium|low", "dependencies": ["string"], "expected_outcomes": ["string"], "timeframe": "string"}],\n'
        '  "quarterly_roadmap": [{"title": "string", "topic": "string", "duration_weeks": 1, "priority": "high|medium|low", "dependencies": ["string"], "expected_outcomes": ["string"], "timeframe": "string"}],\n'
        '  "roadmap": [{"title": "string", "topic": "string", "duration_weeks": 1, "priority": "high|medium|low", "dependencies": ["string"], "expected_outcomes": ["string"], "timeframe": "string"}]\n'
        "}\n\n"
        f"Gaps: {json.dumps(gap_payload, default=str)}\n"
        f"Profile: {json.dumps(profile_payload, default=str)}\n"
        f"Context: {json.dumps(context_payload, default=str)}\n"
    )
