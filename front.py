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
st.session_state.service = utils.initialize_gmail_service()
st.session_state.emails = []


def extract_verification_code(content):
    # Try matching both English and Chinese format
    en_match = re.search(r'Your Poe verification code is:[\s\S]*?(\d{6})', content)
    cn_match = re.search(r'您的Poe验证码是：[\s\S]*?(\d{6})', content)

    if en_match:
        return en_match.group(1)
    elif cn_match:
        return cn_match.group(1)
    return None


def main():
    st.title("📧 Poe Verification Codes")
    st.markdown("# 下面的时间为美国时间")
    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    search_query = "from:noreply@poe.com"
    max_results = 10

    if st.sidebar.button("刷新邮件"):
        st.session_state.service = utils.initialize_gmail_service()
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    # Load emails if not already loaded
    if not st.session_state.emails:
        st.session_state.service = utils.initialize_gmail_service()
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    if not st.session_state.emails:
        st.info("没有找到Poe验证码邮件")
        return

    # Create columns for better layout
    col1, col2 = st.columns(2)

    # Display emails in two columns
    for idx, email in enumerate(st.session_state.emails):
        code = extract_verification_code(email['content'])
        if code:
            with (col1 if idx % 2 == 0 else col2):
                with st.container():
                    st.markdown(f"""
                    ### 验证码: {code}
                    - **时间:** {email['date']}
                    ---
                    """)


if __name__ == "__main__":
    main()
