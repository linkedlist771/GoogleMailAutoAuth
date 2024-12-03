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
            with st.container():
                col1, col2 = st.columns([1, 3])

                with col1:
                    st.markdown(f"""
                    <div style='background-color: #f0f2f6; 
                                padding: 20px; 
                                border-radius: 10px; 
                                text-align: center;
                                font-size: 24px;
                                font-weight: bold;
                                margin: 10px 0;'>
                        {entry['code']}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown("""
                    <style>
                        .time-container {
                            background-color: #ffffff;
                            padding: 10px;
                            border-radius: 5px;
                            margin: 10px 0;
                        }
                        .time-header {
                            color: #666;
                            font-size: 14px;
                            margin-bottom: 5px;
                        }
                        .time-list {
                            color: #333;
                            font-size: 12px;
                            margin: 0;
                            padding-left: 15px;
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="time-container">
                        <div class="time-header">收到时间:</div>
                        <ul class="time-list">
                            {''.join([f"<li>{date}</li>" for date in entry['dates']])}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<hr style='margin: 15px 0; border-color: #eee;'>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
