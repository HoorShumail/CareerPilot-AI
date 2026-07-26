import json
from typing import Any, Dict


def build_strategy_prompt(
    gap_payload: Dict[str, Any],
    roadmap_payload: Dict[str, Any],
    profile_payload: Dict[str, Any],
    context_payload: Dict[str, Any],
) -> str:
    return (
        "You are a career strategy synthesis agent.\n"
        "Combine the gap analysis and roadmap into a comprehensive career strategy.\n\n"
        "CRITICAL RULES:\n"
        "1. Return ONLY a single valid JSON object. No markdown, no code fences, no explanations.\n"
        "2. Do NOT wrap the response in ```json or ``` or any other formatting.\n"
        "3. Do NOT include any text before or after the JSON object.\n"
        "4. Every string value MUST use double quotes.\n"
        "5. Do NOT use trailing commas.\n"
        "6. Keep responses concise. Use short descriptions (1-2 sentences max per field).\n"
        "7. You MUST generate exactly 5 personalized certifications, 5 portfolio projects, 5 weekly goals, and 5 monthly goals based on the user's resume and skill gaps. Do NOT return empty arrays for these sections.\n"
        "8. Return ONLY the JSON object described below.\n\n"
        "Required JSON schema:\n"
        "{\n"
        '  "user_id": null,\n'
        '  "strategy_version": 1,\n'
        '  "skill_gap_analysis": {"gaps": [], "weak_skills": [], "emerging_skills": [], "priority_skills": []},\n'
        '  "roadmap": {"weekly_roadmap": [], "monthly_roadmap": [], "quarterly_roadmap": [], "roadmap": []},\n'
        '  "certifications": [{"name": "string", "provider": "string", "difficulty": "easy|medium|hard", "estimated_study_time": "string", "priority": "high|medium|low", "reason": "string"}],\n'
        '  "projects": [{"title": "string", "description": "string", "skills_gained": ["string"], "technologies": ["string"], "difficulty": "easy|medium|hard", "estimated_duration": "string", "resume_value": "string"}],\n'
        '  "weekly_goals": [{"title": "string", "focus": "string", "target": "string"}],\n'
        '  "monthly_goals": [{"title": "string", "focus": "string", "target": "string"}],\n'
        '  "progress_snapshot": {"completed_items": 0, "progress_percent": 0.0, "goal_completion": {"weekly": 0.0, "monthly": 0.0}},\n'
        '  "refresh_count": 0\n'
        "}\n\n"
        f"Gaps: {json.dumps(gap_payload, default=str)}\n"
        f"Roadmap: {json.dumps(roadmap_payload, default=str)}\n"
        f"Profile: {json.dumps(profile_payload, default=str)}\n"
        f"Context: {json.dumps(context_payload, default=str)}\n"
    )