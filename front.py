import streamlit as st
import utils
from datetime import datetime
import re

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
    for email in st.session_state.emails:
        with st.expander(f"📩 {email['date']}", expanded=True):
            content = email['content']
            cleaned_text = strip_tags(content).replace(" ", '')
            lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]

            # 将邮件内容显示在一个text_area中，并设置高度(可根据需要调整)
            st.text_area("内容", value="\n".join(lines), height=300, disabled=True)

if __name__ == "__main__":
    main()