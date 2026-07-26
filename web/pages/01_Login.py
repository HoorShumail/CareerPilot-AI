import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import streamlit as st
import streamlit.components.v1 as components

from web.api_client import api_client
from web.components.ui_helpers import inject_custom_css, inject_password_manager_fix

st.set_page_config(page_title="Log In | CareerPilot AI", page_icon="🔐", layout="centered")


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
        .cp-forgot-link { text-align:right; margin-top:-0.5rem; margin-bottom:0.5rem; font-size:0.85rem; }
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
        #MainMenu {
    visibility: visible !important;
}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _fix_password_autofill():
    components.html(
        """
        <script>
        const doc = window.parent.document;
        function patchPasswordField() {
            const inputs = doc.querySelectorAll('input[type="password"]');
            inputs.forEach((el) => {
                el.setAttribute('autocomplete', 'current-password');
                el.setAttribute('name', 'current-password');
            });
        }
        patchPasswordField();
        const observer = new MutationObserver(patchPasswordField);
        observer.observe(doc.body, { childList: true, subtree: true });
        setTimeout(() => observer.disconnect(), 3000);
        </script>
        """,
        height=0,
        width=0,
    )


def _friendly_login_error(res) -> str:
    if res.status_code in (401, 400):
        return "Incorrect email or password. Please check your credentials and try again."
    try:
        detail = res.json().get("detail")
        if detail:
            return str(detail)
    except Exception:
        pass
    return "Something went wrong while signing you in. Please try again."


def render_login_page():
    _hide_default_page_nav()
    inject_custom_css()
    _inject_auth_css()
    _fix_password_autofill()

    with st.container(border=True):
        st.markdown('<div class="cp-auth-title">Welcome back</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="cp-auth-subtitle">Sign in to continue to CareerPilot AI.</div>',
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input(
                "Password", type="password", placeholder="********", key="login_password"
            )

            st.markdown(
                '<div class="cp-forgot-link">'
                '<span style="color:#4F46E5; cursor:pointer;">Forgot password?</span>'
                "</div>",
                unsafe_allow_html=True,
            )

            submit = st.form_submit_button("Log In", type="primary")

        if submit:
            if not email or not password:
                st.error("Please enter both your email and password.")
            else:
                with st.spinner("Signing you in..."):
                    res = api_client.login(email, password)
                if res.status_code == 200:
                    api_client.get_me()
                    st.success("Signed in successfully.")
                    st.rerun()
                else:
                    st.error(_friendly_login_error(res))

        st.markdown('<div class="cp-auth-footer">Don\'t have an account?</div>', unsafe_allow_html=True)
        st.page_link("pages/02_Register.py", label="Create one ->", icon="✨")

    st.write("")
    _, back_col, _ = st.columns([1, 1, 1])
    with back_col:
        if st.button("<- Back to Home", key="login_back_home", use_container_width=True):
            st.switch_page("app.py")

    inject_password_manager_fix()


def main():
    if "access_token" in st.session_state:
        st.info("You're already signed in.")
        st.page_link("app.py", label="Go to Home", icon="🏠")
        return
    render_login_page()


if __name__ == "__main__":
    main()