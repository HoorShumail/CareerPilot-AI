import streamlit as st
from web.components.sidebar import render_sidebar

st.set_page_config(page_title="Dashboard | CareerPilot AI", page_icon="📊", layout="wide")

def dashboard():
    if "access_token" not in st.session_state:
        st.warning("Please log in from the Home page first.")
        return
        
    render_sidebar()
    
    st.title("📊 Career Dashboard")
    st.write("Welcome to your Career Intelligence Hub.")
    
    # Placeholder metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Readiness Score", value="72%", delta="5%")
    with col2:
        st.metric(label="Applications", value="23", delta="2")
    with col3:
        st.metric(label="Mock Int. Score", value="8.1", delta="0.4")
    with col4:
        st.metric(label="Skill Gaps", value="4", delta="-1")
        
    st.divider()
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Recent Activity")
        st.info("Optimized resume for Google ML Eng role")
        st.info("Mock interview completed: System Design")
        st.success("Completed Docker Certification")
        
    with col_b:
        st.subheader("Upcoming Targets")
        st.warning("Apply to 3 ML roles this week")
        st.warning("Complete Advanced Kubernetes module")

dashboard()
