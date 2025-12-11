import os
import base64
from datetime import datetime
from io import BytesIO
from typing import List

import requests
import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field, ValidationError

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

# Validation models
class Attachment(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str | None = None
    size_bytes: int = Field(le=5 * 1024 * 1024)  # 5 MB limit
    content_base64: str


class ComplaintSubmission(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(min_length=3, max_length=200)
    complaint: str = Field(min_length=10, max_length=2000)
    priority: str = Field(pattern="^(Low|Medium|High|Urgent)$")
    timestamp: str
    attachments: List[Attachment] = Field(default_factory=list, min_length=1)


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

# Ensure default values live in session state so they persist after errors
for key, default in {
    "name_input": "",
    "email_input": "",
    "subject_input": "",
    "complaint_input": "",
    "priority_input": "Low",
}.items():
    st.session_state.setdefault(key, default)


def clear_form_state():
    st.session_state.name_input = ""
    st.session_state.email_input = ""
    st.session_state.subject_input = ""
    st.session_state.complaint_input = ""
    st.session_state.priority_input = "Low"
    st.session_state.uploaded_files = None


# Create form
with st.form("complaint_form", clear_on_submit=False):
    # Form fields with persistent state via keys
    name = st.text_input("Name *", placeholder="Enter your name", key="name_input")
    email = st.text_input("Email *", placeholder="Enter your email address", key="email_input")
    subject = st.text_input("Subject *", placeholder="Brief description of your complaint", key="subject_input")
    complaint = st.text_area("Complaint Details *", placeholder="Please provide detailed information about your complaint...", height=150, key="complaint_input")
    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"], key="priority_input")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Attach invoices or other supporting documents (Required)",
        type=None,  # Accept all file types
        accept_multiple_files=True,
        help="Required: at least one supporting document so we can process your complaint.",
        key="uploaded_files",
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
        # Early required-field check
        if not name or not email or not subject or not complaint:
            st.error("⚠️ Please fill in all required fields (marked with *)")
        elif not uploaded_files:
            st.error("⚠️ Please attach at least one supporting document (required).")
        else:
            # Prepare base form data
            form_data = {
                "name": name.strip(),
                "email": email.strip(),
                "subject": subject.strip(),
                "complaint": complaint.strip(),
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "attachments": []
            }

            # Process uploaded files with size guard (5 MB per file)
            file_errors = []
            max_file_size = 5 * 1024 * 1024  # 5 MB
            if uploaded_files:
                for file in uploaded_files:
                    file_content = file.getvalue()
                    if len(file_content) > max_file_size:
                        file_errors.append(f"❌ {file.name} exceeds 5 MB limit.")
                        continue
                    file_data = {
                        "filename": file.name,
                        "content_type": file.type,
                        "size_bytes": len(file_content),
                        "content_base64": base64.b64encode(file_content).decode("utf-8"),
                    }
                    form_data["attachments"].append(file_data)

            if file_errors:
                st.error("\n".join(file_errors))
            elif len(form_data["attachments"]) == 0:
                st.error("⚠️ Please attach at least one supporting document (required).")
            else:
                try:
                    # Validate payload with Pydantic
                    validated = ComplaintSubmission(**form_data)

                    # Show loading spinner
                    with st.spinner("Submitting your complaint..."):
                        response = requests.post(
                            WEBHOOK_URL,
                            json=validated.model_dump(),
                            timeout=30  # Increased timeout for file uploads
                        )

                    # Check response
                    if response.status_code == 200:
                        st.success("✅ Your complaint has been submitted successfully!")
                        st.balloons()
                        clear_form_state()  # Reset form after success
                    else:
                        st.warning(f"⚠️ Submission received with status code: {response.status_code}")
                        st.info(f"Response: {response.text}")

                except ValidationError as ve:
                    # Display validation errors in a user-friendly list
                    errors = []
                    for err in ve.errors():
                        loc = " -> ".join(str(part) for part in err["loc"])
                        errors.append(f"{loc}: {err['msg']}")
                    st.error("Validation issues:\n" + "\n".join(errors))
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


