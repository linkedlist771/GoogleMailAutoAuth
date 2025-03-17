# front.py
import threading
import html

import streamlit as st
import utils
from datetime import datetime, timedelta
import re
import schedule
import time
st.set_page_config(
    page_title="Poe Verification Codes",
    page_icon="📧",
    layout="wide"
)

# Initialize session state
st.session_state.service = utils.initialize_gmail_service()
st.session_state.emails = []

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
    st.title("📧 Verification Codes")
    st.markdown("### 美国时间 (UTC-4)")

    # 添加切换按钮
    email_source = st.sidebar.radio(
        "选择邮件来源",
        ["Poe", "Microsoft"],
        format_func=lambda x: "Poe验证码" if x == "Poe" else "Microsoft验证码"
    )

    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    # 根据选择设置不同的搜索条件
    search_query = "from:noreply@poe.com" if email_source == "Poe" else "from:account-security-noreply@accountprotection.microsoft.com"
    max_results = 10

    if st.sidebar.button("刷新邮件 🔄"):
        st.session_state.service = utils.initialize_gmail_service()
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    if not st.session_state.emails:
        st.session_state.service = utils.initialize_gmail_service()
        st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)

    if not st.session_state.emails:
        st.info(f"没有找到{'Poe' if email_source == 'Poe' else 'Microsoft'}验证码邮件")
        return

    if email_source == "Poe":
        display_poe_codes(st.session_state.emails)
    else:
        display_microsoft_codes(st.session_state.emails)

# 添加新的函数来显示Microsoft邮件
def display_microsoft_codes(emails):
    for email in emails:
        with st.container():
            st.markdown("---")
            st.markdown(f"**收到时间:** {email['date']}")
            # 解码并显示原始内容
            content = html.unescape(email['content'])
            st.markdown(content, unsafe_allow_html=True)

# 将原来的显示逻辑移到新函数中
def display_poe_codes(emails):
    # # 只展示一个居中的#h1 : POE 自动验证码已经取消， 如果需要自动验证，连续群主登记使用
    # st.markdown("""
    # <div style='background-color: #f0f2f6;
    #             padding: 20px;
    #             border-radius: 10px;
    #             text-align: center;
    #             font-size: 24px;
    #             font-color: red;
    #             font-weight: bold;
    #             margin: 10px 0;'>
    #     POE 自动验证码已经取消， 如果登录官网使用，连续群主登记使用
    # </div>
    # """, unsafe_allow_html=True)
    # return
    combined_entries = process_emails(emails)
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
