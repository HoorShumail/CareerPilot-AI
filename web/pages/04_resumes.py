import streamlit as st
from web.api_client import api_client
from web.components.sidebar import render_sidebar
from web.components.renderers import render_resume_content

st.set_page_config(page_title="Resume Intelligence | CareerPilot AI", page_icon="📄", layout="wide")


def ensure_authenticated():
    if "access_token" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        return False
    return True


def main():
    render_sidebar()

    if not ensure_authenticated():
        return

    st.title("📄 Resume Intelligence")
    st.write("Upload and manage your resume versions, extract structured resume data, and download your latest files.")

    with st.expander("Upload a new resume"):
        uploaded_file = st.file_uploader(
            "Choose a PDF or Word document",
            type=["pdf", "docx", "doc"],
            help="Resume files are parsed and stored with version history.",
        )

        if uploaded_file is not None:
            if st.button("Upload resume"):
                with st.spinner("Uploading resume..."):
                    result = api_client.upload_resume_bytes(
                        uploaded_file.name,
                        uploaded_file.read(),
                        uploaded_file.type,
                    )
                if result.status_code == 201:
                    st.success("Resume uploaded successfully.")
                    st.rerun()
                else:
                    st.error(f"Upload failed: {result.text}")

    st.divider()

    st.subheader("Your resumes")
    response = api_client.list_resumes()
    if response.status_code != 200:
        st.error("Unable to load resumes. Please try again.")
        return

    resumes = response.json()
    if not resumes:
        st.info("No resumes uploaded yet. Upload one to get started.")
        return

    for resume in resumes:
        with st.expander(f"{resume.get('original_filename')} ({resume.get('created_at')})"):
            st.markdown(f"**File type:** {resume.get('file_type')}  ")
            st.markdown(f"**Parsed name:** {resume.get('parsed_content', {}).get('name', 'Unknown')}  ")
            st.markdown(f"**Email:** {resume.get('parsed_content', {}).get('email', 'Unknown')}  ")
            st.markdown(f"**Phone:** {resume.get('parsed_content', {}).get('phone', 'Unknown')}  ")

            versions = resume.get("versions", [])
            if versions:
                st.markdown(f"**Versions:** {len(versions)}")
                for version in versions:
                    with st.expander(f"Version {version.get('id')} ({version.get('version_type')})"):
                        st.write(version.get("source_description") or "No description.")
                        render_resume_content(version.get("content"))
            else:
                st.info("No version history available.")

            download_response = api_client.download_resume(resume.get("id"))
            if download_response.status_code == 200:
                st.download_button(
                    label="Download file",
                    data=download_response.content,
                    file_name=resume.get("original_filename"),
                    mime=resume.get("file_type"),
                    key=f"download-{resume.get('id')}",
                )
            else:
                st.error("Unable to fetch resume download.")


if __name__ == "__main__":
    main()