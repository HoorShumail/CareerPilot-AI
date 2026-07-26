import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import streamlit as st

from web.api_client import api_client
from web.components.ui_helpers import inject_custom_css, inject_password_manager_fix

st.set_page_config(page_title="Create Account | CareerPilot AI", page_icon="✨", layout="centered")


def _hide_default_page_nav():
    st.markdown(
        "<style>[data-testid='stSidebarNav'] { display: none; }</style>",
        unsafe_allow_html=True,
    )


def _inject_auth_css():
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 440px;
            margin: 0 auto;
            padding-top: 4rem;
            padding-bottom: 2rem;
        }

        .cp-auth-title { font-size: 1.6rem; font-weight: 700; color:#0F172A; margin-bottom: 0.15rem; }
        .cp-auth-subtitle { font-size: 0.95rem; color:#64748B; margin-bottom: 1.5rem; }
        .cp-auth-footer { text-align:center; font-size: 0.9rem; color:#64748B; margin-top: 0.75rem; }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
            width: 100%;
            border-radius: 10px;
            height: 2.9rem;
            font-weight: 600;
            margin-top: 0.4rem;
        }

        [data-testid="stTextInputRootIcon"],
        [data-testid="stTextInputRootIcon"] * ,
        span[data-testid="stIconMaterial"] {
            font-family: 'Material Symbols Rounded' !important;
        }

        [data-testid="InputInstructions"] {
        display: none !important;
        }
        #MainMenu {
    visibility: visible !important;
}

        </style>
        """,
        unsafe_allow_html=True,
    )


def _friendly_register_error(res) -> str:
    try:
        detail = res.json().get("detail")
        if detail:
            return str(detail)
    except Exception:
        pass
    return "We couldn't create your account. Please try again."


def render_register_page():
    _hide_default_page_nav()
    inject_custom_css()
    _inject_auth_css()

    with st.container(border=True):
        st.markdown('<div class="cp-auth-title">Create your account</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="cp-auth-subtitle">Join CareerPilot AI and start building your career strategy.</div>',
            unsafe_allow_html=True,
        )

        with st.form("register_form"):
            full_name = st.text_input("Full Name", placeholder="Jane Doe", key="register_name")
            email = st.text_input("Email", placeholder="you@example.com", key="register_email")
            password = st.text_input(
                "Password", type="password", placeholder="********", key="register_password"
            )
            confirm_password = st.text_input(
                "Confirm Password", type="password", placeholder="********", key="register_confirm"
            )
            submit = st.form_submit_button("Register", type="primary")

        if submit:
            if not full_name or not email or not password or not confirm_password:
                st.error("Please fill in all fields to create your account.")
            elif password != confirm_password:
                st.error("The passwords you entered do not match.")
            else:
                with st.spinner("Creating your account..."):
                    res = api_client.register(email, password, full_name)
                if res.status_code == 201:
                    st.success("Your account has been created successfully. You can now sign in.")
                    st.page_link("pages/01_Login.py", label="Continue to Log In ->", icon="🔐")
                else:
                    st.error(_friendly_register_error(res))

        st.markdown('<div class="cp-auth-footer">Already have an account?</div>', unsafe_allow_html=True)
        st.page_link("pages/01_Login.py", label="Log in ->", icon="🔐")

    st.write("")
    _, back_col, _ = st.columns([1, 1, 1])
    with back_col:
        if st.button("<- Back to Home", key="register_back_home", use_container_width=True):
            st.switch_page("app.py")

    inject_password_manager_fix()


def main():
    if "access_token" in st.session_state:
        st.info("You're already signed in.")
        st.page_link("app.py", label="Go to Home", icon="🏠")
        return
    render_register_page()


if __name__ == "__main__":
    main()