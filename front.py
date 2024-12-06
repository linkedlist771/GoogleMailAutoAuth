import streamlit as st
import utils
from datetime import datetime
import re

st.set_page_config(
    page_title="Cloudflare Emails",
    page_icon="📧",
    layout="wide"
)

# 自定义滚动容器样式
scrollable_css = """
<style>
.scrollable-container {
    max-height: 400px;
    overflow-y: auto;
    padding-right: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    margin-bottom: 20px;
}
</style>
"""
st.markdown(scrollable_css, unsafe_allow_html=True)

# Initialize session state
st.session_state.service = utils.initialize_gmail_service()
st.session_state.emails = []

def strip_tags(html_content):
    # 去掉所有HTML标签
    text = re.sub(r'<[^>]*>', '', html_content)
    return text.strip()

def main():
    st.title("📧 Cloudflare Notifications")
    st.markdown("### 邮件内容")

    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    # 修改搜索条件
    search_query = "from:noreply@notify.cloudflare.com"
    max_results = 10

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

    # 可滚动容器开始
    st.markdown("<div class='scrollable-container'>", unsafe_allow_html=True)

    # 展示邮件内容
    for email in st.session_state.emails:
        date_str = email['date']
        content = email['content']
        cleaned_text = strip_tags(content)
        lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]

        st.markdown(f"**收到时间:** {date_str}")
        for line in lines:
            st.markdown(f"- {line}")
        st.markdown("---")

    # 可滚动容器结束
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()