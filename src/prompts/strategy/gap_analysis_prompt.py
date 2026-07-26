import json
from typing import Any, Dict


def build_gap_analysis_prompt(profile_payload: Dict[str, Any], context_payload: Dict[str, Any]) -> str:
    return (
        "You are a career strategy gap analysis engine.\n"
        "Analyze the profile and context below and identify skill gaps.\n\n"
        "CRITICAL RULES:\n"
        "1. Return ONLY a single valid JSON object. No markdown, no code fences, no explanations.\n"
        "2. Do NOT wrap the response in ```json or ``` or any other formatting.\n"
        "3. Do NOT include any text before or after the JSON object.\n"
        "4. Every string value MUST use double quotes.\n"
        "5. Do NOT use trailing commas.\n"
        "6. Return ONLY the JSON object described below.\n\n"
        "Required JSON schema:\n"
        "{\n"
        '  "gaps": [{"skill": "string", "severity": "high|medium|low", "reason": "string"}],\n'
        '  "weak_skills": [{"skill": "string", "severity": "high|medium|low", "reason": "string"}],\n'
        '  "emerging_skills": [{"skill": "string", "severity": "high|medium|low", "reason": "string"}],\n'
        '  "priority_skills": ["string"]\n'
        "}\n\n"
        f"Profile: {json.dumps(profile_payload, default=str)}\n"
        f"Context: {json.dumps(context_payload, default=str)}\n"
    )
