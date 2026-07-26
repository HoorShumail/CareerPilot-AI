import streamlit as st

from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.renderers import (
    render_badge_list,
    render_pills,
    render_bullet_list,
    render_section,
    render_learning_roadmap,
    render_verdict,
)

st.set_page_config(page_title="Match Intelligence | CareerPilot AI", page_icon="🎯", layout="wide")


def load_resume_versions():
    """Return a list of (label, version_id) tuples from all uploaded resumes."""
    response = api_client.list_resumes()
    if response.status_code != 200:
        return []
    versions = []
    for resume in response.json():
        for version in resume.get("versions", []):
            label = f"{resume.get('original_filename', 'Resume')} – {version.get('version_type', 'v')}"
            versions.append((label, version.get("id")))
    return versions


def load_jobs():
    """Return a list of (label, job_id) tuples and a lookup dict keyed by job_id."""
    response = api_client.get_jobs()
    if response.status_code != 200:
        return [], {}
    jobs = response.json()
    options = []
    lookup = {}
    for job in jobs:
        label = f"{job.get('title', 'Untitled')} @ {job.get('company', 'Unknown')}"
        options.append((label, job.get("id")))
        lookup[job.get("id")] = job
    return options, lookup


def render_match_details(match: dict) -> None:
    """Render the full breakdown of a single match result."""
    col_score, col_ats = st.columns(2)
    with col_score:
        score = match.get("overall_match_score")
        st.metric("Overall Match Score", f"{score:.1f}%" if score is not None else "N/A")
    with col_ats:
        ats = match.get("ats_score")
        st.metric("ATS Score", f"{ats:.1f}%" if ats is not None else "N/A")

    estimated = match.get("estimated_match_after_learning")
    if estimated is not None:
        st.metric("Estimated Score After Learning", f"{estimated:.1f}%")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        if match.get("matched_skills"):
            with st.expander("✅ Matched Skills", expanded=True):
                render_badge_list(match["matched_skills"], tone="check")

        if match.get("strength_analysis"):
            with st.expander("💪 Strength Analysis"):
                render_badge_list(match["strength_analysis"], tone="green")

        if match.get("interview_preparation"):
            with st.expander("🎤 Interview Preparation"):
                render_bullet_list(match["interview_preparation"])

    with col_right:
        if match.get("missing_skills"):
            with st.expander("❌ Missing Skills", expanded=True):
                render_badge_list(match["missing_skills"], tone="red")

        if match.get("missing_technologies"):
            with st.expander("🔧 Missing Technologies"):
                render_pills(match["missing_technologies"]) if isinstance(match["missing_technologies"], list) else render_section(match["missing_technologies"])

        if match.get("missing_certifications"):
            with st.expander("📜 Missing Certifications"):
                render_pills(match["missing_certifications"]) if isinstance(match["missing_certifications"], list) else render_section(match["missing_certifications"])

    if match.get("experience_gap"):
        with st.expander("📊 Experience Gap"):
            render_section(match["experience_gap"])

    if match.get("education_gap"):
        with st.expander("🎓 Education Gap"):
            render_section(match["education_gap"])

    if match.get("weakness_analysis"):
        with st.expander("⚠️ Weakness Analysis"):
            render_badge_list(match["weakness_analysis"], tone="orange")

    if match.get("resume_improvements"):
        with st.expander("📝 Resume Improvements", expanded=True):
            render_bullet_list(match["resume_improvements"])

    if match.get("priority_learning_roadmap"):
        with st.expander("🗺️ Priority Learning Roadmap"):
            render_learning_roadmap(match["priority_learning_roadmap"])

    if match.get("final_recommendation"):
        with st.expander("🏁 Final Recommendation", expanded=True):
            render_verdict(match["final_recommendation"])


def main():
    render_sidebar()

    if "access_token" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        st.stop()

    st.title("🎯 Match Intelligence")
    st.write("Compare your resume against job descriptions to get AI‑powered match analysis.")

    # ---- Run New Match ---- #
    with st.expander("Run a New Match", expanded=False):
        resume_versions = load_resume_versions()
        job_options, jobs_lookup = load_jobs()

        if not resume_versions:
            st.info("No resume versions found. Upload a resume first in Resume Intelligence.")
        elif not job_options:
            st.info("No jobs found. Add a job first in Job Intelligence.")
        else:
            with st.form("new_match_form"):
                selected_resume = st.selectbox(
                    "Select resume version",
                    options=resume_versions,
                    format_func=lambda item: item[0],
                )
                selected_job = st.selectbox(
                    "Select job",
                    options=job_options,
                    format_func=lambda item: item[0],
                )
                submit = st.form_submit_button("🔍 Compare")

            if submit:
                with st.spinner("Generating match analysis… This may take a moment."):
                    res = api_client.compare_resume_to_job(
                        resume_version_id=selected_resume[1],
                        job_id=selected_job[1],
                    )
                if res.status_code in (200, 201):
                    st.success("Match analysis complete!")
                    render_match_details(res.json())
                else:
                    st.error(f"Match failed: {res.json().get('detail', res.text)}")

    # ---- Match History ---- #
    st.divider()
    st.subheader("Match History")

    with st.spinner("Loading match history…"):
        history_res = api_client.list_matches()

    if history_res.status_code != 200:
        st.error(f"Unable to load match history: {history_res.json().get('detail', history_res.text)}")
        if st.button("Retry"):
            st.rerun()
        st.stop()

    matches = history_res.json()
    if not matches:
        st.info("No match history yet. Run a comparison above to get started.")
        return

    # Load job details for display labels
    _, jobs_lookup = load_jobs()

    for match in matches:
        job = jobs_lookup.get(match.get("job_id"), {})
        job_label = f"{job.get('title', 'Unknown Job')} @ {job.get('company', '')}" if job else match.get("job_id", "Unknown")
        score = match.get("overall_match_score")
        score_str = f"{score:.1f}%" if score is not None else "N/A"

        with st.expander(f"{job_label}  —  Score: {score_str}"):
            render_match_details(match)

            st.caption(f"Match ID: {match.get('id')}  |  Created: {match.get('created_at', 'N/A')}")

            if st.button("🗑️ Delete this match", key=f"del-match-{match.get('id')}"):
                with st.spinner("Deleting…"):
                    del_res = api_client.delete_match(match.get("id"))
                if del_res.status_code == 200:
                    st.success("Match deleted.")
                    st.rerun()
                else:
                    st.error(f"Delete failed: {del_res.json().get('detail', del_res.text)}")


if __name__ == "__main__":
    main()