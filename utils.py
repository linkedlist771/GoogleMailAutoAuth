# utils.py
import os.path
import base64
import time
import httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
import datetime
from email.utils import parsedate_to_datetime
import traceback
from bs4 import BeautifulSoup

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def initialize_gmail_service():
    """Initialize and return Gmail service"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"刷新令牌失败: {e}")
                os.remove('token.json')
                return None
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"认证过程出错: {e}")
                return None

    return create_service_with_retry(creds)

def clean_html_content(html_content):
    """Clean HTML content and extract text"""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(separator='\n', strip=True)

def get_email_body(payload):
    """递归提取邮件正文"""
    body = ''
    if 'parts' in payload:
        for part in payload['parts']:
            body += get_email_body(part)
    else:
        data = payload.get('body', {}).get('data')
        if data:
            text = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('utf-8', errors='ignore')
            body += text
    return body

def get_emails(service, query="", max_results=20):
    """Get emails with optional query"""
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results,
            includeSpamTrash=False
        ).execute()
        messages = results.get('messages', [])
        if not messages:
            return []

        detailed_messages = []
        for message in messages:
            details = get_email_details(service, message['id'])
            if details:
                # Clean HTML content
                details['content'] = clean_html_content(details['content'])
                detailed_messages.append(details)

        detailed_messages.sort(key=lambda x: x['internalDate'], reverse=True)
        return detailed_messages

    except Exception as e:
        print(f"获取邮件列表时出错: {e}")
        traceback.print_exc()
        return []

def get_email_details(service, email_id):
    """Get email details"""
    try:
        msg = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        # print(msg)
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '无主题')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '无日期')
        from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), '无发件人')
        
        try:
            parsed_date = parsedate_to_datetime(date)
            formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_date = date

        internalDate = int(msg.get('internalDate', '0'))

        content = get_email_body(msg['payload'])

        return {
            'id': email_id,
            'subject': subject,
            'date': formatted_date,
            'from': from_email,
            'content': content or '无内容',
            'internalDate': internalDate
        }
    except Exception as e:
        print(f"获取邮件详情时出错: {e}")
        traceback.print_exc()
        return None

def create_service_with_retry(creds) -> Resource:
    """Create Gmail service with retry mechanism"""
    for attempt in range(3):
        try:
            http = httplib2.Http(timeout=60)
            authed_http = AuthorizedHttp(creds, http=http)
            service = build('gmail', 'v1', http=authed_http, cache_discovery=False)
            return service
        except Exception as e:
            if attempt == 2:
                raise
            print(f"创建服务失败，5秒后重试... ({attempt + 1}/3)")
            time.sleep(5)


if __name__ == "__main__":
    search_query = "from:noreply@poe.com"

    service = initialize_gmail_service()
    res =  get_emails(service, search_query, 100)
    print(res)
