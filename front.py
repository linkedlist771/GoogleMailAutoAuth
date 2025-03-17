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
    
    # Use a more prominent container for the time display
    with st.container():
        current_time = datetime.now() - timedelta(hours=4)  # UTC-4
        st.subheader(f"🕒 Current Time (UTC-4): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Move email source selection to a more prominent position with better styling
    st.sidebar.title("Settings")
    email_source = st.sidebar.radio(
        "Select Email Source",
        ["Poe", "Microsoft"],
        format_func=lambda x: "Poe Verification Codes" if x == "Poe" else "Microsoft Verification Codes",
        index=0
    )

    # Add a divider in the sidebar
    st.sidebar.divider()
    
    # Better refresh button with status indicator
    if st.sidebar.button("🔄 Refresh Emails", use_container_width=True):
        with st.sidebar.status("Refreshing emails...", expanded=True) as status:
            st.session_state.service = utils.initialize_gmail_service()
            st.session_state.emails = utils.get_emails(st.session_state.service, 
                                                      "from:noreply@poe.com" if email_source == "Poe" else 
                                                      "from:account-security-noreply@accountprotection.microsoft.com", 
                                                      10)
            status.update(label="Refresh complete!", state="complete")

    if st.session_state.service is None:
        st.error("Gmail service initialization failed. Please check your credentials.")
        return

    # Set search query based on selection
    search_query = "from:noreply@poe.com" if email_source == "Poe" else "from:account-security-noreply@accountprotection.microsoft.com"
    max_results = 10

    # Initialize emails if not already done
    if not st.session_state.emails:
        with st.status("Loading emails...", expanded=True) as status:
            st.session_state.service = utils.initialize_gmail_service()
            st.session_state.emails = utils.get_emails(st.session_state.service, search_query, max_results)
            status.update(label="Emails loaded!", state="complete")

    if not st.session_state.emails:
        st.info(f"No {'Poe' if email_source == 'Poe' else 'Microsoft'} verification code emails found")
        return

    # Display a header for the results section
    st.header(f"{'Poe' if email_source == 'Poe' else 'Microsoft'} Verification Codes")
    st.divider()
    
    # Display emails based on selection
    if email_source == "Poe":
        display_poe_codes(st.session_state.emails)
    else:
        display_microsoft_codes(st.session_state.emails)

def display_microsoft_codes(emails):
    for i, email in enumerate(emails):
        with st.expander(f"Email received: {email['date']}", expanded=(i==0)):
            # Decode and display original content
            content = html.unescape(email['content'])
            st.markdown(content, unsafe_allow_html=True)
            st.divider()

def display_poe_codes(emails):
    combined_entries = process_emails(emails)
    
    # Use tabs for better organization if there are multiple codes
    if len(combined_entries) > 1:
        tabs = st.tabs([f"Code: {entry['code']}" for entry in combined_entries])
        
        for i, tab in enumerate(tabs):
            with tab:
                display_poe_code_entry(combined_entries[i])
    else:
        # If only one code, display it directly
        for entry in combined_entries:
            display_poe_code_entry(entry)

def display_poe_code_entry(entry):
    # Use a card-like container for each code
    with st.container():
        # Display the code in a prominent way
        st.markdown(f"## Verification Code")
        
        # Use metric for a nice display of the code
        st.metric(label="", value=entry['code'])
        
        # Display timestamps in a clean table
        st.subheader("Received Times")
        
        # Convert the dates to a DataFrame for better display
        import pandas as pd
        df = pd.DataFrame({"Received At": entry['dates']})
        st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
