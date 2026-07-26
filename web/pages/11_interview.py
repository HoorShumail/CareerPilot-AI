import streamlit as st
from datetime import datetime

from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.renderers import (
    render_card,
    render_skill_section,
    render_empty_state,
)

st.set_page_config(
    page_title="AI Mock Interview | CareerPilot AI",
    page_icon="🎤",
    layout="wide",
)


# ===========================================================
# Session State
# ===========================================================

DEFAULT_STATE = {
    "interview_active": False,
    "interview_finished": False,
    "interview_session_id": None,
    "questions": [],              # list of question dicts
    "current_question_index": 0,  # index into questions list
    "transcript": [],             # list of {role, content} messages
}


def init_state():
    for k, v in DEFAULT_STATE.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ===========================================================
# Overview
# ===========================================================

def render_overview():
    with st.spinner("Loading interview analytics..."):
        response = api_client.get_interview_analytics()

    if response.status_code != 200:
        render_empty_state(
            "No Interview Analytics",
            "Complete your first interview to view statistics.",
            icon="🎤",
        )
        return

    analytics = response.json()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Interviews", analytics.get("total_interviews", 0))
    with col2:
        st.metric("Average Score", f"{analytics.get('average_score', 0)}%")
    with col3:
        st.metric("Best Score", f"{analytics.get('best_score', 0)}%")
    with col4:
        st.metric("Completed", analytics.get("completed_interviews", 0))

    st.divider()

    if analytics.get("strong_skills"):
        st.subheader("💪 Strong Areas")
        render_skill_section({"skills": analytics["strong_skills"]})

    if analytics.get("weak_skills"):
        st.subheader("📚 Improvement Areas")
        render_skill_section({"skills": analytics["weak_skills"]})


# ===========================================================
# Start Interview
# ===========================================================

def render_start_interview():
    st.subheader("Start New Interview")

    with st.form("start_interview_form"):
        interview_type = st.selectbox(
            "Interview Type",
            ["Technical", "Behavioural", "HR", "System Design", "AI Engineer"],
        )
        company = st.text_input("Target Company", placeholder="Google")
        role = st.text_input("Target Role", placeholder="AI Engineer")
        difficulty = st.radio("Difficulty", ["Easy", "Medium", "Hard"], horizontal=True)
        duration = st.slider("Duration (minutes)", 15, 90, 30)

        submit = st.form_submit_button("🚀 Start Interview", use_container_width=True)

    if not submit:
        return

    payload = {
        "interview_type": interview_type,
        "target_company": company,
        "target_role": role,
        "difficulty": difficulty,
        "duration_seconds": duration * 60,   # API expects seconds
    }

    with st.spinner("Preparing interview..."):
        response = api_client.start_interview(payload)

    if response.status_code not in (200, 201):
        st.error(response.json().get("detail", "Unable to start interview."))
        return

    data = response.json()

    st.session_state.interview_active = True
    st.session_state.interview_finished = False
    st.session_state.interview_session_id = data["id"]          # <-- FIXED: use "id"
    st.session_state.questions = data.get("questions", [])
    st.session_state.current_question_index = 0
    st.session_state.transcript = []

    st.rerun()


# ===========================================================
# Active Interview
# ===========================================================

def render_active_interview():
    st.success("Interview in Progress")
    st.caption(f"Session ID: {st.session_state.interview_session_id}")

    questions = st.session_state.questions
    idx = st.session_state.current_question_index

    if idx >= len(questions):
        # No more questions – auto-finish?
        st.info("All questions answered. Click 'Finish Interview' to get your score.")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏁 Finish Interview", use_container_width=True):
                finish_interview()
        with col2:
            st.metric("Questions Answered", len(st.session_state.transcript) // 2)
        return

    current_q = questions[idx]
    question_text = current_q.get("question", "No question text.")
    category = current_q.get("category", "")

    st.divider()
    st.subheader(f"Question {idx + 1} of {len(questions)}")
    if category:
        st.caption(f"Category: {category}")
    st.info(question_text)

    answer = st.chat_input("Type your answer...")

    if answer:
        # Append to transcript
        st.session_state.transcript.append({"role": "assistant", "content": question_text})
        st.session_state.transcript.append({"role": "user", "content": answer})

        # Submit answer
        payload = {
            "question_index": idx,
            "answer": answer,
        }
        with st.spinner("Evaluating answer..."):
            response = api_client.submit_interview_answer(
                st.session_state.interview_session_id,
                payload,
            )

        if response.status_code != 200:
            st.error(response.json().get("detail", "Unable to evaluate answer."))
            return

        data = response.json()
        if data.get("evaluation"):
            with st.expander("AI Evaluation", expanded=True):
                render_card(data["evaluation"])

        # Move to next question
        st.session_state.current_question_index = idx + 1
        st.rerun()

    # Progress & finish button
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏁 Finish Interview", use_container_width=True):
            finish_interview()
    with col2:
        answered = len([t for t in st.session_state.transcript if t["role"] == "user"])
        st.metric("Questions Answered", answered)


def finish_interview():
    response = api_client.finish_interview(st.session_state.interview_session_id)
    if response.status_code == 200:
        st.session_state.interview_finished = True
        st.session_state.interview_active = False
        st.rerun()
    else:
        st.error(response.json().get("detail", "Unable to finish interview."))


# ===========================================================
# Finished Interview
# ===========================================================

def render_finished_interview():
    st.success("Interview Completed")

    with st.spinner("Loading feedback..."):
        response = api_client.get_interview_feedback(st.session_state.interview_session_id)

    if response.status_code != 200:
        st.error("Unable to load interview feedback.")
        return

    feedback = response.json()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", f"{feedback.get('overall_score', 0)}%")
    with col2:
        st.metric("Communication", f"{feedback.get('communication_score', 0)}%")
    with col3:
        st.metric("Technical", f"{feedback.get('technical_score', 0)}%")

    st.divider()

    if feedback.get("strengths"):
        st.subheader("💪 Strengths")
        render_skill_section({"skills": feedback["strengths"]})

    if feedback.get("weaknesses"):
        st.subheader("📚 Areas for Improvement")
        render_skill_section({"skills": feedback["weaknesses"]})

    if feedback.get("recommended_learning"):
        st.subheader("🎯 Recommended Learning")
        for item in feedback["recommended_learning"]:
            st.write(f"• {item}")

    st.divider()

    if st.button("Start Another Interview", use_container_width=True):
        for key in DEFAULT_STATE:
            st.session_state[key] = DEFAULT_STATE[key]
        st.rerun()


# ===========================================================
# History
# ===========================================================

def render_history_tab():
    with st.spinner("Loading history..."):
        response = api_client.get_interview_history()

    if response.status_code != 200:
        render_empty_state("No Interview History", "Complete an interview to see your history.", icon="📜")
        return

    history = response.json()
    if not history:
        render_empty_state("No Interviews", "Start your first AI interview.", icon="🎤")
        return

    for session in history:
        title = session.get("target_role") or session.get("interview_type") or "Interview"
        score = session.get("overall_score", "--")
        date = session.get("completed_at", session.get("created_at", ""))
        with st.expander(f"{title} • {score}%"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Company:** {session.get('target_company', 'N/A')}")
                st.write(f"**Difficulty:** {session.get('difficulty', 'N/A')}")
            with col2:
                st.write(f"**Interview Type:** {session.get('interview_type', 'N/A')}")
                st.write(f"**Completed:** {date}")
            if st.button("View Feedback", key=f"feedback_{session['id']}"):
                st.session_state.selected_feedback = session["id"]
                st.rerun()


# ===========================================================
# Feedback Viewer
# ===========================================================

def render_feedback_view():
    session_id = st.session_state.get("selected_feedback")
    if not session_id:
        return

    with st.spinner("Loading feedback..."):
        response = api_client.get_interview_feedback(session_id)

    if response.status_code != 200:
        st.error("Unable to load feedback.")
        return

    feedback = response.json()
    st.subheader("Interview Feedback")
    render_card(feedback)
    st.divider()
    if st.button("Close Feedback"):
        del st.session_state["selected_feedback"]
        st.rerun()


# ===========================================================
# Analytics
# ===========================================================

def render_analytics_tab():
    with st.spinner("Loading analytics..."):
        response = api_client.get_interview_analytics()

    if response.status_code != 200:
        render_empty_state("Analytics unavailable", "Complete interviews to generate analytics.", icon="📈")
        return

    analytics = response.json()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", analytics.get("total_interviews", 0))
    with col2:
        st.metric("Average Score", f"{analytics.get('average_score', 0)}%")
    with col3:
        st.metric("Best Score", f"{analytics.get('best_score', 0)}%")
    with col4:
        st.metric("Completed", analytics.get("completed_interviews", 0))

    st.divider()

    if analytics.get("score_history"):
        st.subheader("Score Trend")
        st.line_chart(analytics["score_history"])

    if analytics.get("confidence_history"):
        st.subheader("Confidence Trend")
        st.line_chart(analytics["confidence_history"])

    if analytics.get("weak_skills"):
        st.subheader("Weak Skills")
        render_skill_section({"skills": analytics["weak_skills"]})

    if analytics.get("strong_skills"):
        st.subheader("Strong Skills")
        render_skill_section({"skills": analytics["strong_skills"]})


# ===========================================================
# Main
# ===========================================================

def main():
    init_state()
    render_sidebar()

    if "access_token" not in st.session_state:
        st.warning("Please log in first.")
        st.stop()

    st.title("🎤 AI Mock Interview")
    st.write("Practice realistic AI-powered interviews, receive detailed feedback, track your progress, and improve your interview performance over time.")
    st.divider()

    if st.session_state.interview_active:
        render_active_interview()
        return

    if st.session_state.interview_finished:
        render_finished_interview()
        return

    overview_tab, new_tab, history_tab, analytics_tab = st.tabs(
        ["📊 Overview", "🎤 New Interview", "📜 History", "📈 Analytics"]
    )

    with overview_tab:
        render_overview()
    with new_tab:
        render_start_interview()
    with history_tab:
        render_history_tab()
        render_feedback_view()
    with analytics_tab:
        render_analytics_tab()


if __name__ == "__main__":
    main()