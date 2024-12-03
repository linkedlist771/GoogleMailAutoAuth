import streamlit as st
import utils
from datetime import datetime, timedelta
import re

st.set_page_config(
    page_title="Poe Verification Codes",
    page_icon="📧",
    layout="wide"
)

# Initialize session state
# if 'service' not in st.session_state:
st.session_state.service = utils.initialize_gmail_service()

# if 'emails' not in st.session_state:
st.session_state.emails = []


def extract_verification_code(content):
    # Extract code from HTML content using regex
    match = re.search(r'Your Poe verification code is:[\s\S]*?(\d{6})', content)
    if match:
        return match.group(1)
    return None


def main():
    st.title("📧 Poe Verification Codes")

    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    # Set fixed search parameters for Poe verification emails
    search_query = "from:noreply@poe.com subject:verification"
    max_results = 10

    # Refresh button
    if st.sidebar.button("刷新邮件"):
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    # If emails haven't been loaded yet, load them
    if not st.session_state.emails:
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    if not st.session_state.emails:
        st.info("没有找到Poe验证码邮件")
        return

    # Display emails in a cleaner format
    for email in st.session_state.emails:
        code = extract_verification_code(email['content'])
        if code:
            with st.container():
                st.markdown(f"""
                ### 验证码: {code}
                - **时间:** {email['date']}
                """)
                st.divider()


if __name__ == "__main__":
    main()
