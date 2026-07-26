import streamlit as st

from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.renderers import render_pills, render_bullet_list, render_section, render_badge_list

st.set_page_config(page_title="Job Intelligence | CareerPilot AI", page_icon="💼", layout="wide")


def render_job_summary(job: dict) -> None:
    st.markdown(f"### {job.get('title', 'Untitled')} at {job.get('company', 'Unknown')}")
    st.write(f"**Job URL:** {job.get('url', 'N/A')}")
    st.write(f"**Location:** {job.get('location', 'N/A')}  ")
    st.write(f"**Experience level:** {job.get('experience_level', 'N/A')}  ")
    st.write(f"**Remote:** {'Yes' if job.get('is_remote') else 'No'}")
    st.divider()

    if job.get("required_skills"):
        st.markdown("**Required skills**")
        st.write(", ".join(job.get("required_skills", {}).get("required_skills", [])))

    if job.get("preferred_skills"):
        st.markdown("**Preferred skills**")
        st.write(", ".join(job.get("preferred_skills", {}).get("preferred_skills", [])))

    st.subheader("AI Insights")

    if job.get("ai_summary"):
        st.markdown("**Executive summary**")
        render_section(job.get("ai_summary"))

    if job.get("ats_keywords"):
        st.markdown("**ATS keywords**")
        keywords = job.get("ats_keywords")
        render_pills(keywords) if isinstance(keywords, list) else render_section(keywords)

    if job.get("hidden_requirements"):
        st.markdown("**Hidden requirements**")
        render_bullet_list(job.get("hidden_requirements"))

    if job.get("interview_focus"):
        st.markdown("**Interview focus areas**")
        render_bullet_list(job.get("interview_focus"))

    if job.get("missing_certifications"):
        st.markdown("**Missing certifications**")
        certs = job.get("missing_certifications")
        render_pills(certs) if isinstance(certs, list) else render_section(certs)

    if job.get("red_flags"):
        st.markdown("**Red flags**")
        render_badge_list(job.get("red_flags"), tone="red")

    if job.get("extracted_keywords"):
        st.markdown("**Extracted keywords**")
        keywords = job.get("extracted_keywords")
        render_pills(keywords) if isinstance(keywords, list) else render_section(keywords)


def load_resume_versions():
    response = api_client.list_resumes()
    if response.status_code != 200:
        st.error("Unable to load resume versions for comparison.")
        return []

    resume_versions = []
    for resume in response.json():
        for version in resume.get("versions", []):
            label = f"{resume.get('original_filename')} - {version.get('version_type')}"
            resume_versions.append((label, version.get("id")))
    return resume_versions


def main():
    render_sidebar()

    if "access_token" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        return

    st.title("Job Intelligence")
    st.write("Create, preview, and analyze job descriptions with AI-powered intelligence.")

    with st.expander("Create a job from raw text"):
        with st.form("job_from_text"):
            title = st.text_input("Job title")
            company = st.text_input("Company")
            url = st.text_input("Job URL")
            raw_description = st.text_area("Job description")
            submit_text = st.form_submit_button("Create job from text")

            if submit_text:
                if not title or not company or not raw_description:
                    st.error("Job title, company, and description are required.")
                else:
                    with st.spinner("Analyzing job description..."):
                        result = api_client.create_job(
                            title=title,
                            company=company,
                            raw_description=raw_description,
                            url=url,
                        )
                    if result.status_code == 201:
                        st.success("Job created successfully.")
                        st.rerun()
                    else:
                        st.error(f"Job creation failed: {result.text}")

    with st.expander("Upload a job PDF"):
        with st.form("job_from_pdf"):
            title = st.text_input("Job title", key="pdf_title")
            company = st.text_input("Company", key="pdf_company")
            url = st.text_input("Job URL", key="pdf_url")
            uploaded_file = st.file_uploader("Job PDF", type=["pdf"])
            submit_file = st.form_submit_button("Upload PDF")

            if submit_file:
                if not title or not company or uploaded_file is None:
                    st.error("Job title, company, and PDF are required.")
                else:
                    with st.spinner("Uploading and parsing PDF..."):
                        result = api_client.upload_job_pdf(
                            uploaded_file.name,
                            uploaded_file.read(),
                            title,
                            company,
                            url,
                        )
                    if result.status_code == 201:
                        st.success("Job uploaded and parsed successfully.")
                        st.rerun()
                    else:
                        st.error(f"Job upload failed: {result.text}")

    st.divider()
    st.subheader("Your Jobs")

    response = api_client.get_jobs()
    if response.status_code != 200:
        st.error("Unable to load saved jobs. Please try again.")
        return

    jobs = response.json()
    if not jobs:
        st.info("No jobs available yet. Add one to get started.")
        return

    resume_versions = load_resume_versions()

    for job in jobs:
        with st.expander(f"{job.get('title', 'Untitled')} @ {job.get('company', 'Unknown')}"):
            left, right = st.columns([2, 1])
            with left:
                render_job_summary(job)
            with right:
                st.markdown("### Actions")
                if st.button("Refresh insights", key=f"refresh-{job.get('id')}"):
                    with st.spinner("Refreshing insights..."):
                        refresh_response = api_client.refresh_job_insights(job.get("id"))
                    if refresh_response.status_code == 200:
                        st.success("Job insights refreshed.")
                        st.rerun()
                    else:
                        st.error(f"Failed to refresh insights: {refresh_response.text}")

                if st.button("Delete job", key=f"delete-{job.get('id')}"):
                    with st.spinner("Deleting job..."):
                        delete_response = api_client.delete_job(job.get("id"))
                    if delete_response.status_code == 200:
                        st.success("Job deleted.")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete job: {delete_response.text}")

                st.markdown(f"**Job ID:** {job.get('id')}  ")
                st.markdown(f"**Created:** {job.get('created_at')}  ")
                st.markdown(f"**Updated:** {job.get('updated_at')}  ")

                if resume_versions:
                    with st.form(f"compare-form-{job.get('id')}"):
                        selected_resume = st.selectbox(
                            "Select resume version",
                            options=resume_versions,
                            format_func=lambda item: item[0] if item else "",
                            key=f"compare_resume_{job.get('id')}",
                        )
                        compare_button = st.form_submit_button("Compare with resume")

                        if compare_button:
                            if not selected_resume:
                                st.error("Select a resume version to compare.")
                            else:
                                with st.spinner("Generating match analysis..."):
                                    comparison = api_client.create_application(
                                        job_id=job.get("id"),
                                        resume_version_id=selected_resume[1],
                                        status="saved",
                                    )
                                if comparison.status_code == 201:
                                    data = comparison.json()
                                    st.success("Match analysis created.")
                                    st.markdown(f"**Match score:** {data.get('match_score', 'N/A')}")
                                    if data.get('gap_analysis'):
                                        render_section(data.get('gap_analysis'))
                                    st.rerun()
                                else:
                                    st.error(f"Failed to compare resume: {comparison.text}")


if __name__ == "__main__":
    main()