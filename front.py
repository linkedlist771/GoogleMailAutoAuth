# front.py
import streamlit as st
import utils
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Gmail Reader",
    page_icon="📧",
    layout="wide"
)

# Initialize session state
if 'service' not in st.session_state:
    st.session_state.service = utils.initialize_gmail_service()


def main():
    st.title("📧 Gmail Reader")

    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    # Sidebar controls
    st.sidebar.header("搜索过滤")
    search_query = st.sidebar.text_input("搜索关键词", value="")

    time_filter = st.sidebar.selectbox(
        "时间过滤",
        ["全部", "今天", "最近3天", "最近7天", "最近30天"]
    )

    max_results = st.sidebar.slider("显示邮件数量", 5, 50, 20)

    # Apply time filter to search query
    if time_filter != "全部":
        days_map = {
            "今天": 1,
            "最近3天": 3,
            "最近7天": 7,
            "最近30天": 30
        }
        days = days_map[time_filter]
        date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
        search_query += f" after:{date}"

    # Refresh button
    if st.sidebar.button("刷新邮件"):
        st.experimental_rerun()

    # Get emails
    emails = utils.get_emails(st.session_state.service, search_query, max_results)

    if not emails:
        st.info("没有找到符合条件的邮件")
        return

    # Display emails
    for email in emails:
        with st.expander(f"📩 {email['subject']}", expanded=False):
            col1, col2 = st.columns([2, 3])

            with col1:
                st.write("**发件人：**", email['from'])
                st.write("**时间：**", email['date'])

            with col2:
                st.write("**内容：**")
                st.text_area("", email['content'], height=200, key=email['id'])

            st.divider()


if __name__ == "__main__":
    main()
