import streamlit as st

from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.renderers import (
    render_career_summary,
    render_skill_section,
    render_badge_list,
    render_experience,
    render_education,
    render_section,
    render_timeline,
    render_recommendations,
    render_learning_roadmap,
)

st.set_page_config(page_title="Career Digital Twin | CareerPilot AI", page_icon="🧬", layout="wide")


def render_profile_tab():
    """Profile overview pulled from the Career Twin API."""
    with st.spinner("Loading career profile…"):
        res = api_client.get_career_profile()

    if res.status_code == 404:
        st.info("No career profile found yet. Click **Refresh Profile** below to generate one from your resumes.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load profile: {res.json().get('detail', res.text)}")
        return

    profile = res.json()

    # Key metrics row
    cols = st.columns(4)
    with cols[0]:
        st.metric("Experience Level", profile.get("experience_level", "N/A"))
    with cols[1]:
        ai_score = profile.get("ai_maturity_score")
        st.metric("AI Maturity", f"{ai_score:.0f}%" if ai_score is not None else "N/A")
    with cols[2]:
        conf = profile.get("confidence_score")
        st.metric("Confidence", f"{conf:.0f}%" if conf is not None else "N/A")
    with cols[3]:
        readiness = profile.get("readiness_score") or profile.get("overall_readiness_score")
        st.metric("Readiness", f"{readiness:.0f}%" if readiness is not None else "N/A")

    st.divider()

    if profile.get("career_summary"):
        with st.expander("📋 Career Summary", expanded=True):
            render_career_summary(profile["career_summary"])

    col_left, col_right = st.columns(2)
    with col_left:
        if profile.get("skills"):
            with st.expander("🛠️ Skills", expanded=True):
                render_skill_section(profile["skills"])
        if profile.get("strongest_skills"):
            with st.expander("💪 Strongest Skills"):
                render_badge_list(profile["strongest_skills"], tone="green")
        if profile.get("preferred_roles"):
            with st.expander("🎯 Preferred Roles"):
                render_section(profile["preferred_roles"])
        if profile.get("experience_summary"):
            with st.expander("💼 Experience Summary"):
                render_experience(profile["experience_summary"])

    with col_right:
        if profile.get("weakest_skills"):
            with st.expander("⚠️ Weakest Skills"):
                render_badge_list(profile["weakest_skills"], tone="orange")
        if profile.get("preferred_industries"):
            with st.expander("🏭 Preferred Industries"):
                render_section(profile["preferred_industries"])
        if profile.get("education_summary"):
            with st.expander("🎓 Education Summary"):
                render_education(profile["education_summary"])
        if profile.get("certifications"):
            with st.expander("📜 Certifications"):
                render_section(profile["certifications"])

    # Additional data
    for key, label in [
        ("salary_expectations", "💰 Salary Expectations"),
        ("remote_preference", "🏠 Remote Preference"),
        ("skill_intelligence", "🧠 Skill Intelligence"),
        ("growth_summary", "📈 Growth Summary"),
        ("career_gap_analysis", "🔍 Career Gap Analysis"),
    ]:
        if profile.get(key):
            with st.expander(label):
                render_section(profile[key])


def render_timeline_tab():
    """Show career profile snapshots over time."""
    with st.spinner("Loading timeline…"):
        res = api_client.get_career_timeline()

    if res.status_code == 404:
        st.info("No timeline snapshots available yet.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load timeline: {res.json().get('detail', res.text)}")
        return

    snapshots = res.json()
    if not snapshots:
        st.info("No timeline snapshots recorded yet. Refresh your profile to create the first one.")
        return

    render_timeline(snapshots)


def render_strengths_tab():
    with st.spinner("Loading strengths…"):
        res = api_client.get_career_strengths()

    if res.status_code == 404:
        st.info("No strengths analysis available. Refresh your profile to generate one.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load strengths: {res.json().get('detail', res.text)}")
        return

    data = res.json()
    if not data:
        st.info("No strengths data available.")
        return
    render_badge_list(data, tone="green")


def render_weaknesses_tab():
    with st.spinner("Loading weaknesses…"):
        res = api_client.get_career_weaknesses()

    if res.status_code == 404:
        st.info("No weaknesses analysis available. Refresh your profile to generate one.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load weaknesses: {res.json().get('detail', res.text)}")
        return

    data = res.json()
    if not data:
        st.info("No weaknesses data available.")
        return
    render_badge_list(data, tone="orange")


def render_recommendations_tab():
    with st.spinner("Loading recommendations…"):
        res = api_client.get_career_recommendations()

    if res.status_code == 404:
        st.info("No recommendations available yet. Refresh your profile to generate them.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load recommendations: {res.json().get('detail', res.text)}")
        return

    data = res.json()
    if not data:
        st.info("No recommendation data available.")
        return
    render_recommendations(data)


def render_learning_roadmap_tab():
    with st.spinner("Loading learning roadmap…"):
        res = api_client.get_learning_roadmap()

    if res.status_code == 404:
        st.info("No learning roadmap available yet. Refresh your profile to generate one.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load roadmap: {res.json().get('detail', res.text)}")
        return

    data = res.json()
    if not data:
        st.info("No roadmap data available.")
        return
    render_learning_roadmap(data)


def main():
    render_sidebar()

    if "access_token" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        st.stop()

    st.title("🧬 Career Digital Twin")
    st.write("Your AI‑powered career profile — strengths, weaknesses, skills evolution, and personalised recommendations.")

    # Refresh button at the top
    if st.button("🔄 Refresh Profile"):
        with st.spinner("Regenerating career profile from your latest data… This may take a moment."):
            res = api_client.refresh_career_profile()
        if res.status_code in (200, 201):
            st.success("Career profile refreshed successfully!")
            st.rerun()
        else:
            st.error(f"Refresh failed: {res.json().get('detail', res.text)}")

    tab_profile, tab_timeline, tab_strengths, tab_weaknesses, tab_recs, tab_roadmap = st.tabs(
        ["Profile", "Timeline", "Strengths", "Weaknesses", "Recommendations", "Learning Roadmap"]
    )

    with tab_profile:
        render_profile_tab()
    with tab_timeline:
        render_timeline_tab()
    with tab_strengths:
        render_strengths_tab()
    with tab_weaknesses:
        render_weaknesses_tab()
    with tab_recs:
        render_recommendations_tab()
    with tab_roadmap:
        render_learning_roadmap_tab()


if __name__ == "__main__":
    main()