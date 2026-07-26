import streamlit as st

from web.api_client import api_client


def ensure_authenticated():
    if "access_token" not in st.session_state:
        st.warning("Please log in from the home page first.")
        return False
    return True


def main():
    if not ensure_authenticated():
        return

    st.title("Account Settings")
    st.write("Manage security settings for your CareerPilot account.")

    with st.expander("Change password"):
        with st.form("password_reset_form"):
            current_password = st.text_input("Current password", type="password")
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input("Confirm new password", type="password")
            submit = st.form_submit_button("Update password")

            if submit:
                if new_password != confirm_password:
                    st.error("New passwords must match.")
                else:
                    # For Phase 1, use a password reset flow for security.
                    response = api_client.request_password_reset(st.session_state.user.get("email"))
                    if response.status_code == 200:
                        st.success("Password reset email sent if your account exists.")
                    else:
                        st.error("Unable to request password reset.")

    with st.expander("Email verification"):
        st.write("If your email is not verified, request a verification email.")
        if st.button("Send verification email"):
            response = api_client.request_email_verification(st.session_state.user.get("email"))
            if response.status_code == 200:
                st.success("Verification email request sent.")
            else:
                st.error("Unable to send verification email.")

    st.write("---")
    st.write("Note: Password reset and email verification flows are handled by the API.")


if __name__ == "__main__":
    main()
