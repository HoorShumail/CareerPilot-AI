import streamlit as st

from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.renderers import render_forecast, render_learning_plan

st.set_page_config(page_title="AI Career Coach | CareerPilot AI", page_icon="🤖", layout="wide")


def render_coach_response(data: dict) -> None:
    """Display a coach response (chat / advice / action plan / goals)."""
    st.markdown("### 💬 Response")
    st.write(data.get("message", ""))

    confidence = data.get("confidence")
    if confidence is not None:
        st.metric("Confidence", f"{confidence:.0%}")

    action_items = data.get("action_items", [])
    if action_items:
        st.markdown("**Action Items**")
        for item in action_items:
            st.write(f"• {item}")

    if data.get("conversation_id"):
        st.caption(f"Conversation ID: {data['conversation_id']}")
    if data.get("generated_at"):
        st.caption(f"Generated: {data['generated_at']}")


def render_chat_tab():
    with st.form("coach_chat_form"):
        message = st.text_area("Message", placeholder="Ask anything about your career…")
        conv_id = st.text_input("Conversation ID (optional)", help="Leave blank to start a new conversation")
        submit = st.form_submit_button("💬 Send")

    if submit:
        if not message.strip():
            st.warning("Please enter a message.")
            return
        with st.spinner("Thinking…"):
            res = api_client.coach_chat(message, conversation_id=conv_id or None)
        if res.status_code in (200, 201):
            render_coach_response(res.json())
        else:
            st.error(f"Chat error: {res.json().get('detail', res.text)}")


def render_advice_tab():
    with st.form("coach_advice_form"):
        question = st.text_area("Question", placeholder="e.g. Should I switch from backend to ML engineering?")
        conv_id = st.text_input("Conversation ID (optional)", key="advice_conv")
        submit = st.form_submit_button("🎓 Get Advice")

    if submit:
        if not question.strip():
            st.warning("Please enter a question.")
            return
        with st.spinner("Generating career advice…"):
            res = api_client.coach_advice(question, conversation_id=conv_id or None)
        if res.status_code in (200, 201):
            render_coach_response(res.json())
        else:
            st.error(f"Advice error: {res.json().get('detail', res.text)}")


def render_action_plan_tab():
    with st.form("coach_action_plan_form"):
        goal = st.text_area("Goal", placeholder="e.g. Get promoted to Senior Engineer within 12 months")
        conv_id = st.text_input("Conversation ID (optional)", key="plan_conv")
        submit = st.form_submit_button("📋 Generate Action Plan")

    if submit:
        if not goal.strip():
            st.warning("Please enter a goal.")
            return
        with st.spinner("Building action plan…"):
            res = api_client.coach_action_plan(goal, conversation_id=conv_id or None)
        if res.status_code in (200, 201):
            render_coach_response(res.json())
        else:
            st.error(f"Action plan error: {res.json().get('detail', res.text)}")


def render_goals_tab():
    with st.form("coach_goals_form"):
        goals_text = st.text_area(
            "Goals (one per line)",
            placeholder="Learn Kubernetes\nGet AWS certification\nBuild a portfolio project",
        )
        conv_id = st.text_input("Conversation ID (optional)", key="goals_conv")
        submit = st.form_submit_button("🎯 Analyze Goals")

    if submit:
        goals = [g.strip() for g in goals_text.strip().splitlines() if g.strip()]
        if not goals:
            st.warning("Please enter at least one goal.")
            return
        with st.spinner("Analyzing goals…"):
            res = api_client.coach_goals(goals, conversation_id=conv_id or None)
        if res.status_code in (200, 201):
            render_coach_response(res.json())
        else:
            st.error(f"Goals error: {res.json().get('detail', res.text)}")


def render_forecast_tab():
    with st.spinner("Loading career forecast…"):
        res = api_client.get_career_forecast()

    if res.status_code == 404:
        st.info("No forecast available yet. Upload a resume and build your career profile first.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load forecast: {res.json().get('detail', res.text)}")
        return

    data = res.json()

    if data.get("summary"):
        st.markdown(f"**Summary:** {data['summary']}")

    if data.get("generated_at"):
        st.caption(f"Generated: {data['generated_at']}")

    forecasts = data.get("forecasts", [])
    if not forecasts:
        st.info("No forecast items available.")
        return

    render_forecast(forecasts)


def render_market_intelligence_tab():
    with st.spinner("Loading market intelligence…"):
        res = api_client.get_market_intelligence()

    if res.status_code == 404:
        st.info("No market intelligence available yet.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load market intelligence: {res.json().get('detail', res.text)}")
        return

    data = res.json()
    if data.get("generated_at"):
        st.caption(f"Generated: {data['generated_at']}")

    sections = [
        ("demanded_skills", "🔥 In‑Demand Skills"),
        ("technologies", "💻 Technologies"),
        ("certifications", "📜 Certifications"),
        ("frameworks", "🧩 Frameworks"),
        ("ai_tools", "🤖 AI Tools"),
        ("cloud_providers", "☁️ Cloud Providers"),
        ("programming_languages", "🐍 Programming Languages"),
        ("trends", "📈 Trends"),
    ]

    cols = st.columns(2)
    for i, (key, label) in enumerate(sections):
        items = data.get(key, [])
        with cols[i % 2]:
            with st.expander(label, expanded=True):
                if items:
                    for item in items:
                        st.write(f"• {item}")
                else:
                    st.write("No data.")


def render_learning_plan_tab():
    with st.spinner("Loading learning plan…"):
        res = api_client.get_learning_plan()

    if res.status_code == 404:
        st.info("No learning plan available yet.")
        return
    if res.status_code != 200:
        st.error(f"Unable to load learning plan: {res.json().get('detail', res.text)}")
        return

    data = res.json()
    if data.get("generated_at"):
        st.caption(f"Generated: {data['generated_at']}")

    render_learning_plan(data)


def main():
    render_sidebar()

    if "access_token" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        st.stop()

    st.title("🤖 AI Career Coach")
    st.write("Get personalised career guidance, action plans, forecasts, and market intelligence.")

    tab_chat, tab_advice, tab_plan, tab_goals, tab_forecast, tab_market, tab_learn = st.tabs(
        ["Chat", "Career Advice", "Action Plan", "Goals", "Forecast", "Market Intelligence", "Learning Plan"]
    )

    with tab_chat:
        render_chat_tab()
    with tab_advice:
        render_advice_tab()
    with tab_plan:
        render_action_plan_tab()
    with tab_goals:
        render_goals_tab()
    with tab_forecast:
        render_forecast_tab()
    with tab_market:
        render_market_intelligence_tab()
    with tab_learn:
        render_learning_plan_tab()


if __name__ == "__main__":
    main()