import io
import mimetypes
import os
from pathlib import Path

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

print("=" * 50)
print("API_URL =", API_URL)
print("=" * 50)

class APIClient:
    def __init__(self):
        self.base_url = API_URL
        
    @property
    def headers(self):
        headers = {"Content-Type": "application/json"}
        if "access_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        return headers

    @property
    def auth_headers(self):
        headers = {}
        if "access_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        return headers

    def register(self, email, password, full_name):
        res = requests.post(
            f"{self.base_url}/auth/register",
            json={"email": email, "password": password, "full_name": full_name}
        )
        return res

    # ---------- FIXED: indentation corrected ----------
    def login(self, email, password):
        url = f"{self.base_url}/auth/login"
        print("=" * 60)
        print("Calling URL:", url)
        print("Username:", email)

        try:
            res = requests.post(
                url,
                data={
                    "username": email,
                    "password": password,
                },
                timeout=10,
            )

            print("Status Code:", res.status_code)
            print("Response:", res.text)

            if res.status_code == 200:
                data = res.json()
                st.session_state.access_token = data["access_token"]
                st.session_state.refresh_token = data["refresh_token"]

            return res

        except Exception as e:
            print("LOGIN ERROR:", repr(e))
            raise

    def get_me(self):
        res = requests.get(f"{self.base_url}/auth/me", headers=self.headers)
        if res.status_code == 200:
            st.session_state.user = res.json()
        return res

    def update_profile(self, full_name=None, avatar_url=None):
        payload = {}
        if full_name is not None:
            payload["full_name"] = full_name
        if avatar_url is not None:
            payload["avatar_url"] = avatar_url
        return requests.put(
            f"{self.base_url}/auth/me",
            json=payload,
            headers=self.headers,
        )

    def _build_file_tuple(self, filename, data, content_type=None):
        if content_type is None:
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        if isinstance(data, (bytes, bytearray)):
            data = io.BytesIO(data)
        return (filename, data, content_type)

    def upload_resume(self, file_path):
        file_path = Path(file_path)
        with open(file_path, "rb") as f:
            files = {"file": self._build_file_tuple(file_path.name, f, mimetypes.guess_type(file_path.name)[0])}
            return requests.post(
                f"{self.base_url}/resumes/upload",
                files=files,
                headers=self.auth_headers,
            )

    def upload_resume_bytes(self, filename, data, content_type=None):
        files = {"file": self._build_file_tuple(filename, data, content_type)}
        return requests.post(
            f"{self.base_url}/resumes/upload",
            files=files,
            headers=self.auth_headers,
        )

    def list_resumes(self):
        return requests.get(
            f"{self.base_url}/resumes/",
            headers=self.headers,
        )

    def get_resume_versions(self, resume_id):
        return requests.get(
            f"{self.base_url}/resumes/{resume_id}/versions",
            headers=self.headers,
        )

    def download_resume(self, resume_id):
        return requests.get(
            f"{self.base_url}/resumes/{resume_id}/download",
            headers=self.auth_headers,
            stream=True,
        )

    def create_job(self, title, company, raw_description, url=None):
        payload = {
            "title": title,
            "company": company,
            "raw_description": raw_description,
        }
        if url:
            payload["url"] = url
        return requests.post(
            f"{self.base_url}/jobs/",
            json=payload,
            headers=self.headers,
        )

    def upload_job_pdf(self, filename, data, title, company, url=None):
        files = {
            "file": (filename, io.BytesIO(data), "application/pdf"),
        }
        payload = {
            "title": title,
            "company": company,
        }
        if url:
            payload["url"] = url
        return requests.post(
            f"{self.base_url}/jobs/",
            data=payload,
            files=files,
            headers=self.auth_headers,
        )

    def get_jobs(self):
        return requests.get(
            f"{self.base_url}/jobs/",
            headers=self.headers,
        )

    def refresh_job_insights(self, job_id):
        return requests.post(
            f"{self.base_url}/jobs/{job_id}/insights",
            headers=self.headers,
        )

    def delete_job(self, job_id):
        return requests.delete(
            f"{self.base_url}/jobs/{job_id}",
            headers=self.headers,
        )

    def create_application(self, job_id, resume_version_id, status, applied_date=None):
        payload = {
            "job_id": job_id,
            "resume_version_id": resume_version_id,
            "status": status,
        }
        if applied_date is not None:
            payload["applied_date"] = applied_date
        return requests.post(
            f"{self.base_url}/applications/",
            json=payload,
            headers=self.headers,
        )

    def get_applications(self):
        return requests.get(
            f"{self.base_url}/applications/",
            headers=self.headers,
        )

    def get_application(self, application_id):
        return requests.get(
            f"{self.base_url}/applications/{application_id}",
            headers=self.headers,
        )

    def match_application(self, application_id):
        return requests.post(
            f"{self.base_url}/applications/{application_id}/match",
            headers=self.headers,
        )

    def update_application(self, application_id, update_payload):
        return requests.put(
            f"{self.base_url}/applications/{application_id}",
            json=update_payload,
            headers=self.headers,
        )

    def delete_application(self, application_id):
        return requests.delete(
            f"{self.base_url}/applications/{application_id}",
            headers=self.headers,
        )

    def request_password_reset(self, email):
        return requests.post(
            f"{self.base_url}/auth/password-reset",
            json={"email": email},
            headers=self.headers,
        )

    def request_email_verification(self, email):
        return requests.post(
            f"{self.base_url}/auth/email-verification",
            json={"email": email},
            headers=self.headers,
        )

    # ------------------------------------------------------------------ #
    # Phase 5 – Match Intelligence  (prefix: /matches)
    # ------------------------------------------------------------------ #

    def compare_resume_to_job(self, resume_version_id, job_id):
        return requests.post(
            f"{self.base_url}/matches/compare",
            json={"resume_version_id": str(resume_version_id), "job_id": str(job_id)},
            headers=self.headers,
        )

    def get_match(self, match_id):
        return requests.get(
            f"{self.base_url}/matches/{match_id}",
            headers=self.headers,
        )

    def list_matches(self):
        return requests.get(
            f"{self.base_url}/matches/",
            headers=self.headers,
        )

    def list_matches_for_resume(self, resume_version_id):
        return requests.get(
            f"{self.base_url}/matches/resume/{resume_version_id}",
            headers=self.headers,
        )

    def list_matches_for_job(self, job_id):
        return requests.get(
            f"{self.base_url}/matches/job/{job_id}",
            headers=self.headers,
        )

    def delete_match(self, match_id):
        return requests.delete(
            f"{self.base_url}/matches/{match_id}",
            headers=self.headers,
        )

    # ------------------------------------------------------------------ #
    # Phase 6 – Career Digital Twin  (prefix: /career-twin)
    # ------------------------------------------------------------------ #

    def get_career_profile(self):
        return requests.get(
            f"{self.base_url}/career-twin/profile",
            headers=self.headers,
        )

    def get_career_timeline(self):
        return requests.get(
            f"{self.base_url}/career-twin/timeline",
            headers=self.headers,
        )

    def refresh_career_profile(self):
        return requests.post(
            f"{self.base_url}/career-twin/refresh",
            headers=self.headers,
        )

    def get_career_recommendations(self):
        return requests.get(
            f"{self.base_url}/career-twin/recommendations",
            headers=self.headers,
        )

    def get_career_strengths(self):
        return requests.get(
            f"{self.base_url}/career-twin/strengths",
            headers=self.headers,
        )

    def get_career_weaknesses(self):
        return requests.get(
            f"{self.base_url}/career-twin/weaknesses",
            headers=self.headers,
        )

    def get_learning_roadmap(self):
        return requests.get(
            f"{self.base_url}/career-twin/learning-roadmap",
            headers=self.headers,
        )

    # ------------------------------------------------------------------ #
    # Phase 7 – AI Career Coach  (prefix: /career-coach)
    # ------------------------------------------------------------------ #

    def coach_chat(self, message, conversation_id=None):
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = str(conversation_id)
        return requests.post(
            f"{self.base_url}/career-coach/chat",
            json=payload,
            headers=self.headers,
        )

    def coach_advice(self, question, conversation_id=None):
        payload = {"question": question}
        if conversation_id:
            payload["conversation_id"] = str(conversation_id)
        return requests.post(
            f"{self.base_url}/career-coach/advice",
            json=payload,
            headers=self.headers,
        )

    def coach_action_plan(self, goal, conversation_id=None):
        payload = {"goal": goal}
        if conversation_id:
            payload["conversation_id"] = str(conversation_id)
        return requests.post(
            f"{self.base_url}/career-coach/action-plan",
            json=payload,
            headers=self.headers,
        )

    def coach_goals(self, goals, conversation_id=None):
        payload = {"goals": goals}
        if conversation_id:
            payload["conversation_id"] = str(conversation_id)
        return requests.post(
            f"{self.base_url}/career-coach/goals",
            json=payload,
            headers=self.headers,
        )

    def get_career_forecast(self):
        return requests.get(
            f"{self.base_url}/career-coach/forecast",
            headers=self.headers,
        )

    def get_market_intelligence(self):
        return requests.get(
            f"{self.base_url}/career-coach/market-intelligence",
            headers=self.headers,
        )

    def get_learning_plan(self):
        return requests.get(
            f"{self.base_url}/career-coach/learning-plan",
            headers=self.headers,
        )

    # ------------------------------------------------------------------ #
    # Phase 8 – Career Strategy  (prefix: /career-strategy)
    # ------------------------------------------------------------------ #

    def get_career_strategy(self):
        return requests.get(
            f"{self.base_url}/career-strategy",
            headers=self.headers,
        )

    def get_strategy_roadmap(self):
        return requests.get(
            f"{self.base_url}/career-strategy/roadmap",
            headers=self.headers,
        )

    def get_weekly_goals(self):
        return requests.get(
            f"{self.base_url}/career-strategy/weekly-goals",
            headers=self.headers,
        )

    def get_monthly_goals(self):
        return requests.get(
            f"{self.base_url}/career-strategy/monthly-goals",
            headers=self.headers,
        )

    def get_strategy_certifications(self):
        return requests.get(
            f"{self.base_url}/career-strategy/certifications",
            headers=self.headers,
        )

    def get_strategy_projects(self):
        return requests.get(
            f"{self.base_url}/career-strategy/projects",
            headers=self.headers,
        )

    def get_strategy_progress(self):
        return requests.get(
            f"{self.base_url}/career-strategy/progress",
            headers=self.headers,
        )

    def update_strategy_progress(self, payload):
        return requests.patch(
            f"{self.base_url}/career-strategy/progress",
            json=payload,
            headers=self.headers,
        )

    def refresh_career_strategy(self):
        return requests.post(
            f"{self.base_url}/career-strategy/refresh",
            headers=self.headers,
        )

api_client = APIClient()