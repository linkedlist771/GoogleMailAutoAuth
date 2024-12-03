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

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
POLLING_INTERVAL = 2  # 轮询间隔（秒）


def create_service_with_retry(creds) -> Resource:
    """创建 Gmail 服务，带重试机制和自定义超时时间"""
    for attempt in range(3):
        try:
            # 设置自定义超时时间为60秒
            http = httplib2.Http(timeout=60)
            authed_http = AuthorizedHttp(creds, http=http)
            service = build('gmail', 'v1', http=authed_http, cache_discovery=False)
            return service
        except Exception as e:
            if attempt == 2:
                raise
            print(f"创建服务失败，5秒后重试... ({attempt + 1}/3)")
            time.sleep(5)


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


def get_recent_emails(service, query, max_results=10):
    """获取最新的几封邮件"""
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results,
            includeSpamTrash=False  # 如果需要包括垃圾邮件和已删除邮件，将其设置为True
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            print("未找到任何邮件。")
            return []

        detailed_messages = []
        for message in messages:
            details = get_email_details(service, message['id'])
            if details:
                detailed_messages.append(details)

        # 按 internalDate 降序排序
        detailed_messages.sort(key=lambda x: x['internalDate'], reverse=True)
        return detailed_messages[:5]  # 返回最新的5条

    except Exception as e:
        print(f"获取邮件列表时出错: {e}")
        traceback.print_exc()
        return []


def get_email_details(service, email_id):
    """获取邮件详细信息"""
    try:
        msg = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '无主题')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '无日期')
        from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), '无发件人')

        internalDate = int(msg.get('internalDate', '0'))  # 毫秒级时间戳

        # 获取邮件内容
        content = get_email_body(msg['payload'])

        return {
            'id': email_id,
            'subject': subject,
            'date': date,
            'from': from_email,
            'content': content or '无内容',
            'internalDate': internalDate
        }
    except Exception as e:
        print(f"获取邮件详情时出错: {e}")
        traceback.print_exc()
        return None


def main():
    """持续监听并显示最新的5封邮件"""
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
                return
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"认证过程出错: {e}")
                return

    try:
        service = create_service_with_retry(creds)
        query = 'from:noreply@poe.com'  # 根据需要调整查询条件
        processed_ids = set()

        print(f"开始监听符合查询条件 '{query}' 的新邮件...")
        print(f"轮询间隔: {POLLING_INTERVAL} 秒")

        while True:
            try:
                recent_emails = get_recent_emails(service, query)

                # 检查是否有新邮件
                current_ids = {msg['id'] for msg in recent_emails}
                new_ids = current_ids - processed_ids

                if new_ids:
                    print("\n" + "=" * 50)
                    print(f"发现新邮件! 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("最新的5封邮件：")
                    print("=" * 50)

                    for i, msg in enumerate(recent_emails, 1):
                        print(f"\n{i}. 主题: {msg['subject']}")
                        print(f"   发件人: {msg['from']}")
                        print(f"   时间: {msg['date']}")
                        print(f"   内容:\n{msg['content']}\n")
                        print("-" * 50)
                    processed_ids = current_ids

                time.sleep(POLLING_INTERVAL)
                print(".", end="", flush=True)

            except HttpError as error:
                if error.resp.status in [429, 500, 503]:
                    print(f"\nAPI错误，等待后重试: {error}")
                    time.sleep(POLLING_INTERVAL * 2)
                else:
                    print(f"\n发生异常错误: {error}")
                    traceback.print_exc()
                    break
            except Exception as e:
                print(f"\n发生错误: {e}")
                traceback.print_exc()
                break

    except KeyboardInterrupt:
        print("\n\n监听已停止")
    except Exception as error:
        print(f"\n发生错误: {error}")
        traceback.print_exc()


if __name__ == '__main__':
    main()