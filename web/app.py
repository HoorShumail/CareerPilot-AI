import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import streamlit as st

from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.ui_helpers import inject_custom_css

st.set_page_config(page_title="CareerPilot AI", page_icon="🚀", layout="wide")


def _hide_default_page_nav():
    """Hide Streamlit's auto-generated page list in the sidebar — navigation
    is handled explicitly by render_sidebar() / the buttons on this page."""
    st.markdown(
        "<style>[data-testid='stSidebarNav'] { display: none; }</style>",
        unsafe_allow_html=True,
    )


def _inject_landing_css():
    st.markdown(
        """
        <style>
        .cp-landing-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 5rem 1rem 3rem 1rem;
            text-align: center;
        }
        .cp-landing-badge {
            display: inline-block;
            padding: 0.35rem 0.9rem;
            border-radius: 999px;
            background: #EEF2FF;
            color: #4338CA;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            letter-spacing: 0.02em;
        }
        .cp-landing-title {
            font-size: 3rem;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 0.5rem;
            line-height: 1.15;
        }
        .cp-landing-subtitle {
            font-size: 1.15rem;
            color: #475569;
            max-width: 560px;
            margin: 0 auto 2.5rem auto;
            line-height: 1.6;
        }
        div[data-testid="stButton"] > button {
            border-radius: 10px;
            height: 3rem;
            font-weight: 600;
            font-size: 1rem;
            width: 100%;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(79, 70, 229, 0.18);
        }
        /* Show the three-dot menu on the landing page */
        #MainMenu {
            visibility: visible !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_already_signed_in():
    render_sidebar()
    st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
    st.success("You're already signed in.")
    st.write("Use the sidebar to jump back into your dashboard.")


def render_landing():
    _hide_default_page_nav()
    inject_custom_css()
    _inject_landing_css()

    st.markdown(
        """
        <div class="cp-landing-wrap">
            <div class="cp-landing-badge">🚀 AI CAREER INTELLIGENCE</div>
            <div class="cp-landing-title">CareerPilot AI</div>
            <div class="cp-landing-subtitle">
                Your AI-powered career co-pilot — resume intelligence, job matching,
                market insights, and a personal career coach, all in one place.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, col_mid, _ = st.columns([1.3, 1, 1.3])
    with col_mid:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Log In", key="landing_login_btn", type="primary", use_container_width=True):
                st.switch_page("pages/01_Login.py")
        with c2:
            if st.button("Create Account", key="landing_register_btn", use_container_width=True):
                st.switch_page("pages/02_Register.py")

    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    feat_cols = st.columns(3)
    features = [
        ("🧬", "Career Digital Twin", "A living profile of your skills, strengths, and growth trajectory."),
        ("🎯", "Match Intelligence", "See exactly how your resume stacks up against any job description."),
        ("🤖", "AI Career Coach", "Get personalised advice, action plans, and market intelligence on demand."),
    ]
    for col, (icon, title, desc) in zip(feat_cols, features):
        with col:
            with st.container(border=True):
                st.markdown(f"**{icon} {title}**")
                st.write(desc)


def main():
    if "access_token" in st.session_state:
        render_already_signed_in()
        return

    render_landing()


if __name__ == "__main__":
    main()