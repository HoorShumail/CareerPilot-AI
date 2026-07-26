import json
from typing import Any, Dict


JOB_PARSING_SYSTEM_INSTRUCTIONS = (
    "You are an expert technical recruiter and job intelligence assistant. "
    "Extract structured metadata from job descriptions. "
    "Return ONLY valid JSON. "
    "Never include markdown or explanations."
)

JOB_INSIGHTS_SYSTEM_INSTRUCTIONS = (
    "You are an expert Senior AI Recruiter, Hiring Manager, ATS Expert, and Career Coach. "
    "Analyze a structured job description and produce comprehensive hiring intelligence. "
    "Return ONLY valid JSON. "
    "Every top-level value MUST be a JSON object. "
    "Never return arrays directly at the top level. "
    "Infer hidden expectations from the job description. "
    "Rank ATS keywords by importance. "
    "Recommend certifications when beneficial. "
    "Identify interview topics likely to be asked. "
    "Suggest resume improvements. "
    "Recommend learning topics that would increase candidate competitiveness. "
    "Summarize the company and role professionally. "
    "Never invent facts not reasonably inferred from the job description. "
    "If information is unavailable, return {} instead of null."
)

JOB_MATCH_SYSTEM_INSTRUCTIONS = (
    "You are an expert resume reviewer and ATS specialist. "
    "Compare a specific resume version against a job description. "
    "Return ONLY valid JSON."
)


def build_job_parsing_prompt(raw_description: str) -> str:
    return f"""
{JOB_PARSING_SYSTEM_INSTRUCTIONS}

Extract:

{{
"title":"",
"company":"",
"location":"",
"remote":false,
"employment_type":"",
"experience_level":"",
"salary":"",
"responsibilities":[],
"required_skills":[],
"preferred_skills":[],
"education":[],
"certifications":[],
"technologies":[],
"soft_skills":[],
"keywords":[],
"raw_description":""
}}

Job Description:

{raw_description}

Return ONLY JSON.
"""


def build_job_insights_prompt(parsed_job: Dict[str, Any]) -> str:
    schema = """{
  \"executive_summary\": {
      \"summary\": \"\",
      \"role\": \"\",
      \"company\": \"\",
      \"experience_level\": \"\"
  },

  \"ats_keywords\": {
      \"keywords\": {
          \"must_have\": [],
          \"nice_to_have\": [],
          \"priority_order\": []
      }
  },

  \"hidden_requirements\": {
      \"communication\": [],
      \"leadership\": [],
      \"ownership\": [],
      \"business_expectations\": []
  },

  \"missing_certifications\": {
      \"recommended\": []
  },

  \"interview_focus_areas\": {
      \"technical\": [],
      \"behavioral\": [],
      \"system_design\": [],
      \"coding\": []
  },

  \"strengths\": {
      \"important_strengths\": []
  },

  \"risks\": {
      \"red_flags\": []
  },

  \"important_technologies\": {
      \"technologies\": []
  },

  \"recommended_learning_topics\": {
      \"topics\": []
  },

  \"resume_optimization_suggestions\": {
      \"recommendations\": []
  },

  \"company_insights\": {
      \"industry\": \"\",
      \"culture\": \"\",
      \"mission\": \"\",
      \"hiring_focus\": \"\"
  },

  \"embedding\": {
      \"keywords\": []
  }
}"""

    return (
        f"{JOB_INSIGHTS_SYSTEM_INSTRUCTIONS}\n\n"
        f"Job Data\n\n{json.dumps(parsed_job, indent=2, default=str)}\n\n"
        "Generate the following JSON.\n\n"
        f"{schema}\n\n"
        "Rules\n\n"
        "1. Return ONLY JSON.\n\n"
        "2. Never use markdown.\n\n"
        "3. Never invent company information that cannot be inferred.\n\n"
        "4. If a field is unknown use an empty object or empty string.\n\n"
        "5. Every top-level field MUST be an object.\n\n"
        "6. Never return arrays directly at the top level.\n\n"
        "7. Rank ATS keywords by importance and place the ranked list in ats_keywords.keywords.priority_order.\n\n"
        "8. Recommend certifications when beneficial and place them in missing_certifications.recommended.\n\n"
        "9. Identify interview topics likely to be asked and populate the relevant arrays in interview_focus_areas.\n\n"
        "10. Suggest resume improvements and populate resume_optimization_suggestions.recommendations.\n\n"
        "11. Recommend learning topics that would increase candidate competitiveness and populate recommended_learning_topics.topics.\n\n"
        "12. Summarize the company and role professionally in executive_summary and company_insights.\n\n"
        "13. If information is unavailable, return {} instead of null."
    )


def build_job_match_prompt(
    resume_version: Dict[str, Any],
    job_data: Dict[str, Any],
) -> str:

    return f"""
{JOB_MATCH_SYSTEM_INSTRUCTIONS}

Resume

{json.dumps(resume_version, indent=2, default=str)}

Job

{json.dumps(job_data, indent=2, default=str)}

Return ONLY JSON.
"""