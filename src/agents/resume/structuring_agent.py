from typing import Dict, Any

class ResumeStructuringAgent:
    def __init__(self):
        pass

    def structure(self, parsed_text: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": parsed_text.get("full_name"),
            "email": parsed_text.get("email"),
            "phone": parsed_text.get("phone"),
            "summary": parsed_text.get("summary"),
            "skills": parsed_text.get("skills"),
            "experience": parsed_text.get("experience"),
            "education": parsed_text.get("education"),
        }
