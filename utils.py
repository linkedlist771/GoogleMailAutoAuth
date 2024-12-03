from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        print("未找到token.json文件。")
        return

    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        print(results)
        labels = results.get('labels', [])
        if not labels:
            print('未找到任何标签。')
        else:
            print('标签列表：')
            for label in labels:
                print(label['name'])
    except Exception as e:
        print(f'发生错误: {e}')

if __name__ == '__main__':
    main()