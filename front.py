# front.py
import threading

import streamlit as st
import utils
from datetime import datetime
import re
import schedule
import time
st.set_page_config(
    page_title="Cloudflare Emails",
    page_icon="📧",
    layout="wide"
)

# Initialize session state
st.session_state.service = utils.initialize_gmail_service()
st.session_state.emails = []

def strip_tags(html_content):
    # 去掉所有HTML标签
    text = re.sub(r'<[^>]*>', '', html_content)
    return text.strip()
def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        time.sleep(1)

def refresh_token_task():
    if 'service' in st.session_state and st.session_state.service is not None:
        utils.refresh_token(st.session_state.service)

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

# Set up the scheduled task
schedule.every(6).days.do(refresh_token_task)

# Start the scheduled tasks in a separate thread
threading.Thread(target=run_scheduled_tasks, daemon=True).start()

def main():
    st.title("📧 Cloudflare Notifications")

    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    # 修改搜索条件
    search_query = "from:noreply@notify.cloudflare.com"
    max_results = 10

    # 刷新按钮
    if st.sidebar.button("刷新邮件 🔄"):
        st.session_state.service = utils.initialize_gmail_service()
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    # 如果还没有邮件则获取一次
    if not st.session_state.emails:
        st.session_state.service = utils.initialize_gmail_service()
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    if not st.session_state.emails:
        st.info("没有找到来自 Cloudflare 的邮件")
        return

    # 展示邮件内容，每封邮件一个独立的可展开区域
    for i, email in enumerate(st.session_state.emails):
        with st.expander(f"📩 {email['date']}", expanded=True):
            content = email['content']
            cleaned_text = strip_tags(content).replace(" ", '')
            lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]

            st.text_area(
                "内容",
                value="\n".join(lines),
                height=300,
                disabled=True,
                key=f"text_area_{i}"
            )

if __name__ == "__main__":
    main()