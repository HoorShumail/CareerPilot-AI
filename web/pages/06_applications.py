import streamlit as st
from datetime import datetime

from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.renderers import render_section, render_badge_list, render_recommendations

st.set_page_config(page_title="Applications | CareerPilot AI", page_icon="🧾", layout="wide")

STATUS_OPTIONS = [
    "saved",
    "applied",
    "screening",
    "interview",
    "offer",
    "rejected",
]


def build_resume_labels(resumes: list[dict]) -> list[tuple[str, dict]]:
    resume_versions = []
    for resume in resumes:
        for version in resume.get("versions", []):
            label = f"{resume.get('original_filename')} - {version.get('version_type')}"
            resume_versions.append((label, version))
    return resume_versions


def render_application_card(application: dict, job: dict, resume_label: str) -> None:
    st.markdown(f"### {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')}")
    st.write(f"**Status:** {application.get('status', 'N/A')}  ")
    st.write(f"**Applied date:** {application.get('applied_date', 'N/A')}  ")
    st.write(f"**Match score:** {application.get('match_score', 'N/A')}  ")
    st.write(f"**Resume version:** {resume_label}")
    st.divider()

    if application.get('gap_analysis'):
        st.markdown("**Gap analysis**")
        render_section(application.get('gap_analysis'))

    if application.get('skills_match'):
        st.markdown("**Skills match**")
        render_section(application.get('skills_match'))

    if application.get('recruiter_notes'):
        st.markdown("**Notes**")
        st.write(application.get('recruiter_notes').get('content', ''))

    if application.get('strengths'):
        st.markdown("**Strengths**")
        render_badge_list(application.get('strengths'), tone="green")

    if application.get('learning_recommendations'):
        st.markdown("**Learning recommendations**")
        render_recommendations(application.get('learning_recommendations'))


def main():
    render_sidebar()

    if "access_token" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        return

    st.title("Application Tracker")
    st.write("Track applications, refresh match scores, and update status and notes.")

    with st.spinner("Loading application data..."):
        jobs_response = api_client.get_jobs()
        resumes_response = api_client.list_resumes()
        applications_response = api_client.get_applications()

    if jobs_response.status_code != 200:
        st.error("Unable to load jobs.")
        return
    if resumes_response.status_code != 200:
        st.error("Unable to load resumes.")
        return
    if applications_response.status_code != 200:
        st.error("Unable to load applications.")
        return

    jobs = jobs_response.json()
    resumes = resumes_response.json()
    applications = applications_response.json()

    jobs_by_id = {job["id"]: job for job in jobs}
    resume_versions = build_resume_labels(resumes)
    version_lookup = {version[1]["id"]: version[0] for version in resume_versions}

    with st.expander("Create new application"):
        with st.form("create_application"):
            selected_job = st.selectbox(
                "Job",
                options=[(job.get("title"), job.get("id")) for job in jobs],
                format_func=lambda x: f"{x[0]}" if x else "",
            )
            resume_choice = st.selectbox(
                "Resume version",
                options=resume_versions,
                format_func=lambda item: item[0] if item else "",
            )
            status = st.selectbox("Status", STATUS_OPTIONS, index=0)
            applied_date = st.date_input("Applied date", value=datetime.today())
            create_button = st.form_submit_button("Create application")

            if create_button:
                if not selected_job or not resume_choice:
                    st.error("Please select a job and resume version.")
                else:
                    version_id = resume_choice[1]["id"]
                    with st.spinner("Creating application..."):
                        result = api_client.create_application(
                            job_id=selected_job[1],
                            resume_version_id=version_id,
                            status=status,
                            applied_date=applied_date.isoformat(),
                        )
                    if result.status_code == 201:
                        st.success("Application created successfully.")
                        st.rerun()
                    else:
                        st.error(f"Failed to create application: {result.text}")

    st.divider()
    st.subheader("Your applications")

    filter_col, sort_col, search_col = st.columns(3)
    with filter_col:
        status_filter = st.selectbox("Filter by status", options=["all"] + STATUS_OPTIONS)
    with sort_col:
        sort_option = st.selectbox("Sort by", ["Applied date", "Match score"])
    with search_col:
        search_query = st.text_input("Search jobs or companies")

    filtered_apps = []
    for app in applications:
        job = jobs_by_id.get(app.get("job_id"), {})
        if status_filter != "all" and app.get("status") != status_filter:
            continue
        if search_query:
            search_lower = search_query.lower()
            if search_lower not in job.get("title", "").lower() and search_lower not in job.get("company", "").lower():
                continue
        filtered_apps.append((app, job))

    if sort_option == "Match score":
        filtered_apps.sort(key=lambda pair: pair[0].get("match_score") or 0, reverse=True)
    else:
        filtered_apps.sort(key=lambda pair: pair[0].get("applied_date") or "", reverse=True)

    if not filtered_apps:
        st.info("No applications match the selected filters.")
        return

    for application, job in filtered_apps:
        with st.expander(f"{job.get('title', 'Unknown')} — {application.get('status', 'N/A').title()}"):
            resume_label = version_lookup.get(application.get("resume_version_id"), "Unknown version")
            render_application_card(application, job, resume_label)

            cols = st.columns([1, 1, 1])
            with cols[0]:
                if st.button("Refresh match", key=f"refresh-{application.get('id')}"):
                    with st.spinner("Refreshing match analysis..."):
                        response = api_client.match_application(application.get("id"))
                    if response.status_code == 200:
                        st.success("Match analysis refreshed.")
                        st.rerun()
                    else:
                        st.error(f"Failed to refresh match: {response.text}")
            with cols[1]:
                if st.button("Delete application", key=f"delete-{application.get('id')}"):
                    with st.spinner("Deleting application..."):
                        response = api_client.delete_application(application.get("id"))
                    if response.status_code == 200:
                        st.success("Application deleted.")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete application: {response.text}")
            with cols[2]:
                with st.form(f"update-app-{application.get('id')}"):
                    status_option = st.selectbox(
                        "Update status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(application.get("status", "saved")),
                        key=f"status-{application.get('id')}",
                    )
                    notes = st.text_area(
                        "Notes",
                        value=(application.get("notes") or {}).get("content", "") if isinstance(application.get("notes"), dict) else "",
                        key=f"notes-{application.get('id')}",
                    )
                    submitted = st.form_submit_button("Save changes")
                    if submitted:
                        payload = {"status": status_option}
                        if notes:
                            payload["notes"] = {"content": notes}
                        with st.spinner("Saving application updates..."):
                            response = api_client.update_application(application.get("id"), payload)
                        if response.status_code == 200:
                            st.success("Application updated.")
                            st.rerun()
                        else:
                            st.error(f"Unable to update application: {response.text}")


if __name__ == "__main__":
    main()