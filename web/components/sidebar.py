import streamlit as st

def render_sidebar():

    def inject_custom_css():
        import os
        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles", "custom.css")
        print(f"CSS path: {css_path}")  # debug
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
                print(f"CSS loaded, length: {len(css_content)}")  # debug
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        else:
            print("CSS file NOT found!")  # debug

    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
                <h2 style="font-weight: 700; color: #6366F1; margin: 0; font-size: 1.5rem;">🚀 CareerPilot AI</h2>
                <p style="font-size: 0.8rem; color: #64748B; margin-top: 0.2rem;">Career Intelligence Platform</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        user = st.session_state.get("user")
        if "access_token" in st.session_state and user:
            # User Info Card
            full_name = user.get('full_name', 'User')
            email = user.get('email', '')
            role = user.get('role', 'user').capitalize()
            
            st.markdown(
                f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
                    <div style="font-weight: 600; color: #0F172A; font-size: 0.95rem;">👤 {full_name}</div>
                    <div style="font-size: 0.75rem; color: #64748B;">{email}</div>
                    <span class="cp-badge cp-badge-indigo" style="margin-top: 0.4rem; font-size: 0.7rem;">{role}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # --- SECTION 1: OVERVIEW ---
            st.markdown('<div class="sidebar-category">Overview</div>', unsafe_allow_html=True)
            st.page_link("app.py", label="Home", icon="🏠")
            st.page_link("pages/01_dashboard.py", label="Dashboard", icon="📊")
            
            # --- SECTION 2: JOB SEARCH ENGINE ---
            st.markdown('<div class="sidebar-category">Job Search Engine</div>', unsafe_allow_html=True)
            st.page_link("pages/04_resumes.py", label="Resume Intelligence", icon="📄")
            st.page_link("pages/05_jobs.py", label="Job Intelligence", icon="💼")
            st.page_link("pages/06_applications.py", label="Application Tracker", icon="🧾")
            st.page_link("pages/07_match_intelligence.py", label="Match Intelligence", icon="🎯")
            
            # --- SECTION 3: CAREER INTELLIGENCE AI ---
            st.markdown('<div class="sidebar-category">Career Intelligence AI</div>', unsafe_allow_html=True)
            st.page_link("pages/08_career_twin.py", label="Career Digital Twin", icon="🧬")
            st.page_link("pages/09_career_coach.py", label="AI Career Coach", icon="🤖")
            st.page_link("pages/10_career_strategy.py", label="Career Strategy", icon="🗺️")
            st.page_link("pages/11_interview.py", label="AI Mock Interview", icon="🎤")
            
            # --- SECTION 4: ACCOUNT ---
            st.markdown('<div class="sidebar-category">Account</div>', unsafe_allow_html=True)
            st.page_link("pages/02_profile.py", label="Profile", icon="👤")
            st.page_link("pages/03_account_settings.py", label="Account Settings", icon="⚙️")
            
            st.divider()
            
            if st.button("Logout", use_container_width=True, key="sidebar_logout"):
                for key in ["access_token", "refresh_token", "user"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        else:
            st.info("Log in or register to access career intelligence tools.")