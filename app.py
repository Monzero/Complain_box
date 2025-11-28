import streamlit as st
import requests
from datetime import datetime
import base64
from io import BytesIO

# Configure page
st.set_page_config(
    page_title="Complaint Box",
    page_icon="📮",
    layout="centered"
)

# Webhook URL
WEBHOOK_URL = "https://supermon.app.n8n.cloud/webhook/9fdecbd1-6485-46a9-a323-d5b6f0215015"

# Title
st.title("📮 Complaint Box")
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
        "Attach Files (Optional)",
        type=None,  # Accept all file types
        accept_multiple_files=True,
        help="You can attach multiple files to support your complaint"
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
st.info("If you encounter any issues, please contact support.")


