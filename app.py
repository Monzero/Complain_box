import streamlit as st
import requests
from datetime import datetime
import base64
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Complaint Box",
    page_icon="📮",
    layout="centered"
)

# Webhook URL from environment variable
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    st.error("⚠️ WEBHOOK_URL environment variable is not set. Please check your .env file.")
    st.stop()

# Header with info button
st.markdown("""
<style>
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    st.title("📮 Complaint Box")
with col2:
    # Add padding to align button with title
    st.markdown("<div style='padding-top: 1.5rem;'>", unsafe_allow_html=True)
    if st.button("How it works", use_container_width=True):
        st.session_state.show_info = not st.session_state.get('show_info', False)
    st.markdown("</div>", unsafe_allow_html=True)

# Show explanation if button was clicked
if st.session_state.get('show_info', False):
    with st.expander("📖 How Complaint Box Works", expanded=True):
        st.markdown("""
        **How our Complaint Box operates:**
        
        1. **Submit Your Complaint**: Drop any complaint that you have about your device
        2. **Attach Invoice**: Attach the invoice or other supporting documents
        3. **AI Agent Processing**: Our AI agent will:
           - Extract all the needful information from your complaint and documents
           - Draft a professional complaint to the customer care email ID
           - *(Future features)*: Make calls and tweet on your behalf
        
        **Beta Version:**
        - In this beta version, we send an email to you with the customer care email ID and the drafted complaint
        
        Simply fill out the form below and let us handle the rest! 🚀
        """)

st.markdown("Please fill out the form below to submit your complaint.")

# Create form
with st.form("complaint_form", clear_on_submit=True):
    # Form fields
    name = st.text_input("Name *", placeholder="Enter your name")
    email = st.text_input("Email *", placeholder="Enter your email address")
    subject = st.text_input("Subject *", placeholder="Brief description of your complaint")
    complaint = st.text_area("Complaint Details *", placeholder="Please provide detailed information about your complaint...", height=150)
    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Attach invoices or other supporting documents (Optional)",
        type=None,  # Accept all file types
        accept_multiple_files=True,
        help="This helps us investigate your complaint faster."
    )
    
    # Display uploaded files info
    if uploaded_files:
        st.info(f"📎 {len(uploaded_files)} file(s) selected")
        for idx, file in enumerate(uploaded_files, 1):
            file_size = len(file.getvalue()) / 1024  # Size in KB
            st.caption(f"{idx}. {file.name} ({file_size:.2f} KB)")
    
    # Submit button
    submitted = st.form_submit_button("Submit Complaint", type="primary")
    
    if submitted:
        # Validation
        if not name or not email or not subject or not complaint:
            st.error("⚠️ Please fill in all required fields (marked with *)")
        else:
            # Prepare data to send
            form_data = {
                "name": name,
                "email": email,
                "subject": subject,
                "complaint": complaint,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "attachments": []
            }
            
            # Process uploaded files
            if uploaded_files:
                for file in uploaded_files:
                    file_content = file.getvalue()
                    file_data = {
                        "filename": file.name,
                        "content_type": file.type,
                        "size_bytes": len(file_content),
                        "content_base64": base64.b64encode(file_content).decode('utf-8')
                    }
                    form_data["attachments"].append(file_data)
            
            try:
                # Show loading spinner
                with st.spinner("Submitting your complaint..."):
                    # Send POST request to webhook
                    response = requests.post(
                        WEBHOOK_URL,
                        json=form_data,
                        timeout=30  # Increased timeout for file uploads
                    )
                    
                    # Check response
                    if response.status_code == 200:
                        st.success("✅ Your complaint has been submitted successfully!")
                        st.balloons()
                    else:
                        st.warning(f"⚠️ Submission received with status code: {response.status_code}")
                        st.info(f"Response: {response.text}")
                        
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Please try again.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ An error occurred while submitting: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("### Need Help?")
st.info("If you encounter any issues, please contact care@issuebot.in")


