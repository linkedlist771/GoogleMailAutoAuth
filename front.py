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
    
    # Add a cleaner header with current time
    current_time = datetime.now() - timedelta(hours=4)  # UTC-4
    st.subheader(f"Current US Time (UTC-4): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Move email source selector to the sidebar
    with st.sidebar:
        st.markdown("### Email Source")
        email_source = st.radio(
            "",
            ["Poe", "Microsoft"],
            format_func=lambda x: "Poe Verification Codes" if x == "Poe" else "Microsoft Verification Codes",
            horizontal=False
        )
        
        # Add refresh button to sidebar
        refresh = st.button("🔄 Refresh Emails", use_container_width=True)

    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    # Set search query based on selection
    search_query = "from:noreply@poe.com" if email_source == "Poe" else "from:account-security-noreply@accountprotection.microsoft.com"
    max_results = 10

    # Handle refresh button click
    if refresh:
        with st.spinner("Fetching emails..."):
            # Show a loading placeholder
            loading_placeholder = st.empty()
            loading_placeholder.markdown("""
            <div style="display: flex; justify-content: center; margin: 50px 0;">
                <div style="text-align: center;">
                    <div class="stSpinner">
                        <div></div><div></div><div></div><div></div>
                    </div>
                    <p style="margin-top: 20px; font-size: 16px; color: #666;">
                        Loading emails, please wait...
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Fetch emails
            st.session_state.service = utils.initialize_gmail_service()
            st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)
            
            # Clear loading placeholder
            loading_placeholder.empty()

    # Initial load of emails if needed
    if not st.session_state.emails:
        with st.spinner("Loading initial data..."):
            loading_placeholder = st.empty()
            loading_placeholder.markdown("""
            <div style="display: flex; justify-content: center; margin: 50px 0;">
                <div style="text-align: center;">
                    <div class="stSpinner">
                        <div></div><div></div><div></div><div></div>
                    </div>
                    <p style="margin-top: 20px; font-size: 16px; color: #666;">
                        Loading initial data...
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.service = utils.initialize_gmail_service()
            st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)
            
            loading_placeholder.empty()

    if not st.session_state.emails:
        st.info(f"No {email_source} verification code emails found")
        return

    # Display a divider before showing emails
    st.markdown("---")
    
    # Display selected email source as a header
    st.header(f"{email_source} Verification Codes")
    
    if email_source == "Poe":
        display_poe_codes(st.session_state.emails)
    else:
        display_microsoft_codes(st.session_state.emails)

def display_microsoft_codes(emails):
    # Sort emails by date (newest first)
    sorted_emails = sorted(emails, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    
    for email in sorted_emails:
        with st.expander(f"Email received: {email['date']}", expanded=True):
            # Create a card-like container for each email
            st.markdown("""
            <style>
            .email-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown(f"<div class='email-card'>", unsafe_allow_html=True)
                # Decode and display original content
                content = html.unescape(email['content'])
                st.markdown(content, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

def display_poe_codes(emails):
    combined_entries = process_emails(emails)
    
    # Use Streamlit's built-in card component
    for entry in combined_entries:
        with st.container():
            # Create a nicer card layout
            st.markdown("""
            <style>
            .code-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='code-card'>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Use Streamlit's metric component for verification code
                st.metric("Verification Code", entry['code'])
            
            with col2:
                st.subheader("Received Times:")
                for date in entry['dates']:
                    st.text(f"• {date}")
            
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
