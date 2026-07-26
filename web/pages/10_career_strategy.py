import streamlit as st

from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.renderers import (
    render_skill_section,
    render_recommendations,
    render_progress_snapshot,
    render_roadmap_section,
    render_card,
)

st.set_page_config(page_title="Career Strategy | CareerPilot AI", page_icon="🗺️", layout="wide")


def render_overview_tab():
    with st.spinner("Loading career strategy…"):
        res = api_client.get_career_strategy()

    if res.status_code == 404:
        st.info("No career strategy generated yet. Click **Refresh Strategy** to create one.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load strategy: {res.json().get('detail', res.text)}")
        return

    strategy = res.json()

    # Key metrics
    cols = st.columns(3)
    with cols[0]:
        st.metric("Strategy Version", strategy.get("strategy_version", "N/A"))
    with cols[1]:
        st.metric("Refresh Count", strategy.get("refresh_count", 0))
    with cols[2]:
        st.caption(f"Generated: {strategy.get('generated_at', 'N/A')}")
        st.caption(f"Last Refreshed: {strategy.get('last_refreshed_at', 'N/A')}")

    st.divider()

    if strategy.get("skill_gap_analysis"):
        with st.expander("🔍 Skill Gap Analysis", expanded=True):
            render_skill_section(strategy["skill_gap_analysis"])

    if strategy.get("recommendations"):
        with st.expander("💡 Recommendations", expanded=True):
            render_recommendations(strategy["recommendations"])

    if strategy.get("progress_snapshot"):
        with st.expander("📊 Progress Snapshot"):
            render_progress_snapshot(strategy["progress_snapshot"])


def render_roadmap_tab():
    with st.spinner("Loading roadmap…"):
        res = api_client.get_strategy_roadmap()

    if res.status_code == 404:
        st.info("No roadmap available yet. Generate a strategy first.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load roadmap: {res.json().get('detail', res.text)}")
        return

    data = res.json()
    if not data:
        st.info("No roadmap data available.")
        return

    render_roadmap_section(data)


def render_goals_list(fetch_func, label):
    """Generic renderer for weekly / monthly goals."""
    with st.spinner(f"Loading {label}…"):
        res = fetch_func()

    if res.status_code == 404:
        st.info(f"No {label} available yet.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load {label}: {res.json().get('detail', res.text)}")
        return

    goals = res.json()
    if not goals:
        st.info(f"No {label} defined yet.")
        return

    for i, goal in enumerate(goals):
        if isinstance(goal, dict):
            with st.expander(goal.get("title") or goal.get("goal") or f"Goal {i + 1}"):
                render_card(goal)
        else:
            st.write(f"• {goal}")


def render_certifications_tab():
    with st.spinner("Loading certification recommendations…"):
        res = api_client.get_strategy_certifications()

    if res.status_code == 404:
        st.info("No certification recommendations available yet.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load certifications: {res.json().get('detail', res.text)}")
        return

    certs = res.json()
    if not certs:
        st.info("No certification recommendations yet.")
        return

    for cert in certs:
        if isinstance(cert, dict):
            name = cert.get("name", "Unknown Certification")
            priority = cert.get("priority", "")
            with st.expander(f"📜 {name} {'  `' + priority + '`' if priority else ''}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Provider:** {cert.get('provider', 'N/A')}")
                    st.write(f"**Difficulty:** {cert.get('difficulty', 'N/A')}")
                with col2:
                    st.write(f"**Study Time:** {cert.get('estimated_study_time', 'N/A')}")
                    st.write(f"**Priority:** {cert.get('priority', 'N/A')}")
                if cert.get("reason"):
                    st.write(f"**Reason:** {cert['reason']}")
        else:
            st.write(f"• {cert}")


def render_projects_tab():
    with st.spinner("Loading project recommendations…"):
        res = api_client.get_strategy_projects()

    if res.status_code == 404:
        st.info("No project recommendations available yet.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load projects: {res.json().get('detail', res.text)}")
        return

    projects = res.json()
    if not projects:
        st.info("No project recommendations yet.")
        return

    for proj in projects:
        if isinstance(proj, dict):
            title = proj.get("title", "Untitled Project")
            difficulty = proj.get("difficulty", "")
            with st.expander(f"🔨 {title} {'  `' + difficulty + '`' if difficulty else ''}"):
                if proj.get("description"):
                    st.write(proj["description"])
                col1, col2 = st.columns(2)
                with col1:
                    if proj.get("skills_gained"):
                        st.write("**Skills gained:** " + ", ".join(proj["skills_gained"]))
                    if proj.get("technologies"):
                        st.write("**Technologies:** " + ", ".join(proj["technologies"]))
                with col2:
                    st.write(f"**Duration:** {proj.get('estimated_duration', 'N/A')}")
                    st.write(f"**Resume Value:** {proj.get('resume_value', 'N/A')}")
        else:
            st.write(f"• {proj}")


def render_progress_tab():
    with st.spinner("Loading progress…"):
        res = api_client.get_strategy_progress()

    if res.status_code == 404:
        st.info("No progress data available yet. Generate a strategy first.")
    elif res.status_code != 200:
        st.error(f"Unable to load progress: {res.json().get('detail', res.text)}")
    else:
        data = res.json()
        if data:
            render_progress_snapshot(data)
        else:
            st.info("No progress data recorded yet.")

    st.divider()
    st.subheader("Update Progress")

    with st.form("update_progress_form"):
        completed_skills = st.text_area(
            "Completed Skills (comma‑separated)",
            placeholder="Python, Docker, Kubernetes",
        )
        completed_certs = st.text_area(
            "Completed Certifications (comma‑separated)",
            placeholder="AWS SAA, CKA",
        )
        completed_projects = st.text_area(
            "Completed Projects (comma‑separated)",
            placeholder="Portfolio Website, ML Pipeline",
        )
        progress_pct = st.slider("Progress %", 0, 100, 0)
        submit = st.form_submit_button("💾 Save Progress")

    if submit:
        payload = {}
        if completed_skills.strip():
            payload["completed_skills"] = [s.strip() for s in completed_skills.split(",") if s.strip()]
        if completed_certs.strip():
            payload["completed_certifications"] = [s.strip() for s in completed_certs.split(",") if s.strip()]
        if completed_projects.strip():
            payload["completed_projects"] = [s.strip() for s in completed_projects.split(",") if s.strip()]
        if progress_pct > 0:
            payload["progress_percent"] = float(progress_pct)

        if not payload:
            st.warning("Please fill in at least one field to update progress.")
            return

        with st.spinner("Saving progress…"):
            update_res = api_client.update_strategy_progress(payload)
        if update_res.status_code in (200, 201):
            st.success("Progress updated successfully!")
            st.rerun()
        else:
            st.error(f"Update failed: {update_res.json().get('detail', update_res.text)}")


def main():
    render_sidebar()

    if "access_token" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        st.stop()

    st.title("🗺️ Career Strategy")
    st.write("Your AI‑generated career roadmap with goals, certifications, projects, and progress tracking.")

    # Refresh button
    if st.button("🔄 Refresh Strategy"):
        with st.spinner("Regenerating career strategy… This may take a moment."):
            res = api_client.refresh_career_strategy()
        if res.status_code in (200, 201):
            st.success("Career strategy refreshed!")
            st.rerun()
        else:
            st.error(f"Refresh failed: {res.json().get('detail', res.text)}")

    tab_overview, tab_roadmap, tab_weekly, tab_monthly, tab_certs, tab_projects, tab_progress = st.tabs(
        ["Overview", "Roadmap", "Weekly Goals", "Monthly Goals", "Certifications", "Projects", "Progress"]
    )

    with tab_overview:
        render_overview_tab()
    with tab_roadmap:
        render_roadmap_tab()
    with tab_weekly:
        render_goals_list(api_client.get_weekly_goals, "weekly goals")
    with tab_monthly:
        render_goals_list(api_client.get_monthly_goals, "monthly goals")
    with tab_certs:
        render_certifications_tab()
    with tab_projects:
        render_projects_tab()
    with tab_progress:
        render_progress_tab()


if __name__ == "__main__":
    main()