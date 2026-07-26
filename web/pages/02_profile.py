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

    if "user" not in st.session_state:
        api_client.get_me()

    user = st.session_state.get("user", {})

    st.title("Profile")
    st.write("Manage your profile details and public account information.")

    st.markdown("**Account Summary**")
    st.write(f"- **Email:** {user.get('email', '—')} ")
    st.write(f"- **Role:** {user.get('role', 'user')} ")
    st.write(f"- **Email verified:** {'Yes' if user.get('email_verified') else 'No'}")
    st.write(f"- **Joined:** {user.get('created_at', '—')}")
    st.write("---")

    with st.form("profile_form"):
        full_name = st.text_input("Full name", value=user.get("full_name", ""))
        avatar_url = st.text_input("Avatar URL", value=user.get("avatar_url", ""))
        submit = st.form_submit_button("Update profile")

        if submit:
            payload = {"full_name": full_name, "avatar_url": avatar_url}
            response = api_client.update_profile(**payload)
            if response.status_code == 200:
                st.success("Profile updated successfully.")
                api_client.get_me()
                st.rerun()
            else:
                st.error(f"Unable to update profile: {response.json().get('detail', 'Unknown error')}")

    if user.get("preferences"):
        st.write("---")
        st.markdown("**Preferences**")
        st.json(user.get("preferences"))


if __name__ == "__main__":
    main()
