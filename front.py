import streamlit as st
import utils
from datetime import datetime, timedelta
import re
from operator import itemgetter

st.set_page_config(
    page_title="Poe Verification Codes",
    page_icon="📧",
    layout="wide"
)

# Initialize session state
st.session_state.service = utils.initialize_gmail_service()
st.session_state.emails = []


def extract_verification_code(content):
    en_match = re.search(r'Your Poe verification code is:[\s\S]*?(\d{6})', content)
    cn_match = re.search(r'您的Poe验证码是：[\s\S]*?(\d{6})', content)

    if en_match:
        return en_match.group(1)
    elif cn_match:
        return cn_match.group(1)
    return None


def process_emails(emails):
    # Extract codes and dates
    code_entries = []
    for email in emails:
        code = extract_verification_code(email['content'])
        if code:
            code_entries.append({
                'code': code,
                'date': datetime.strptime(email['date'], '%Y-%m-%d %H:%M:%S'),
                'date_str': email['date']
            })

    # Sort by date (newest first)
    code_entries.sort(key=lambda x: x['date'], reverse=True)

    # Combine duplicate codes
    combined_entries = []
    current_code = None
    current_dates = []

    for entry in code_entries:
        if current_code != entry['code']:
            if current_code is not None:
                combined_entries.append({
                    'code': current_code,
                    'dates': current_dates.copy()
                })
            current_code = entry['code']
            current_dates = [entry['date_str']]
        else:
            current_dates.append(entry['date_str'])

    if current_code is not None:
        combined_entries.append({
            'code': current_code,
            'dates': current_dates
        })

    return combined_entries


def main():
    st.title("📧 Poe Verification Codes")
    st.markdown("### 美国时间 (UTC-4)")

    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    search_query = "from:noreply@poe.com"
    max_results = 10

    if st.sidebar.button("刷新邮件 🔄"):
        st.session_state.service = utils.initialize_gmail_service()
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    if not st.session_state.emails:
        st.session_state.service = utils.initialize_gmail_service()
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    if not st.session_state.emails:
        st.info("没有找到Poe验证码邮件")
        return

    combined_entries = process_emails(st.session_state.emails)

    # Create a container with custom CSS for scrolling
    scroll_container = st.container()
    with scroll_container:
        for entry in combined_entries:
            with st.expander(f"验证码: {entry['code']}", expanded=True):
                dates_text = "\n".join([f"- {date}" for date in entry['dates']])
                st.markdown(f"""
                **收到时间:**
                {dates_text}
                """)
                st.button(f"复制验证码 {entry['code']}", key=f"copy_{entry['code']}",
                          on_click=lambda code=entry['code']: st.write(f'验证码 {code} 已复制到剪贴板'))


if __name__ == "__main__":
    main()
