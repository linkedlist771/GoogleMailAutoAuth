import streamlit as st
import utils
from datetime import datetime
import re

st.set_page_config(
    page_title="Cloudflare Emails",
    page_icon="📧",
    layout="wide"
)

# Add custom CSS for scrollable container
st.markdown("""
    <style>
    .scrollable-container {
        height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .email-item {
        background-color: white;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    </style>
""", unsafe_allow_html=True)

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

    # Create a scrollable container
    scroll_container = st.container()

    with scroll_container:
        st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)

        # 展示邮件内容
        for email in st.session_state.emails:
            date_str = email['date']
            content = email['content']
            cleaned_text = strip_tags(content)

            # 将邮件内容按行分割
            lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]

            # Create an email item
            st.markdown('<div class="email-item">', unsafe_allow_html=True)
            st.markdown(f"**收到时间:** {date_str}")
            # 使用 Markdown 列表展示每行信息
            for line in lines:
                st.markdown(f"- {line}")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
