# -*- coding: utf-8 -*-
"""
Gmail服务核心模块
提供Gmail API的初始化和邮件获取功能
"""

import os
import base64
import time
import httplib2
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
import traceback

# Gmail API权限范围
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    """Gmail服务类，封装Gmail API操作"""
    
    def __init__(self, credentials_file: str = 'config/credentials.json', 
                 token_file: str = 'config/token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def initialize(self) -> Optional[Resource]:
        """初始化Gmail服务"""
        creds = self._load_credentials()
        if not creds:
            return None
            
        self.service = self._create_service_with_retry(creds)
        return self.service
        
    def _load_credentials(self) -> Optional[Credentials]:
        """加载或获取新的凭据"""
        creds = None
        
        # 尝试从token文件加载现有凭据
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                print(f"加载现有凭据失败: {e}")
                
        # 检查凭据有效性
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self._save_credentials(creds)
                    print("凭据刷新成功")
                except Exception as e:
                    print(f"刷新凭据失败: {e}")
                    creds = None
                    
            # 如果刷新失败或没有可用凭据，进行新的授权流程
            if not creds:
                creds = self._perform_oauth_flow()
                
        return creds
        
    def _perform_oauth_flow(self) -> Optional[Credentials]:
        """执行OAuth授权流程"""
        try:
            if not os.path.exists(self.credentials_file):
                print(f"凭据文件 {self.credentials_file} 不存在")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file,
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            # 使用本地服务器进行授权
            creds = flow.run_local_server(
                port=0, 
                access_type='offline', 
                prompt='consent'
            )
            
            self._save_credentials(creds)
            print("新的授权流程完成")
            return creds
            
        except Exception as e:
            print(f"OAuth授权过程出错: {e}")
            return None
            
    def _save_credentials(self, creds: Credentials):
        """保存凭据到文件"""
        try:
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"保存凭据失败: {e}")
            
    def _create_service_with_retry(self, creds: Credentials) -> Optional[Resource]:
        """创建Gmail服务，包含重试机制"""
        for attempt in range(3):
            try:
                http = httplib2.Http(timeout=60)
                authed_http = AuthorizedHttp(creds, http=http)
                service = build('gmail', 'v1', http=authed_http, cache_discovery=False)
                return service
            except Exception as e:
                if attempt == 2:
                    print(f"创建Gmail服务失败: {e}")
                    return None
                print(f"创建服务失败，5秒后重试... ({attempt + 1}/3)")
                time.sleep(5)
                
    def get_emails(self, query: str = "", max_results: int = 20) -> List[Dict]:
        """获取邮件列表"""
        if not self.service:
            print("Gmail服务未初始化")
            return []
            
        try:
            results = self.service.users().messages().list(
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
                details = self._get_email_details(message['id'])
                if details:
                    detailed_messages.append(details)
                    
            # 按日期排序（最新的在前）
            detailed_messages.sort(key=lambda x: x['internalDate'], reverse=True)
            return detailed_messages
            
        except Exception as e:
            print(f"获取邮件列表时出错: {e}")
            traceback.print_exc()
            return []
            
    def _get_email_details(self, email_id: str) -> Optional[Dict]:
        """获取邮件详细信息"""
        try:
            msg = self.service.users().messages().get(
                userId='me', 
                id=email_id, 
                format='full'
            ).execute()
            
            headers = msg['payload'].get('headers', [])
            subject = self._get_header_value(headers, 'subject') or '无主题'
            date = self._get_header_value(headers, 'date') or '无日期'
            from_email = self._get_header_value(headers, 'from') or '无发件人'
            
            # 格式化日期
            try:
                parsed_date = parsedate_to_datetime(date)
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_date = date
                
            internal_date = int(msg.get('internalDate', '0'))
            content = self._get_email_body(msg['payload'])
            
            # 清理HTML内容
            clean_content = self._clean_html_content(content)
            
            return {
                'id': email_id,
                'subject': subject,
                'date': formatted_date,
                'from': from_email,
                'content': clean_content or '无内容',
                'internalDate': internal_date
            }
            
        except Exception as e:
            print(f"获取邮件详情时出错: {e}")
            return None
            
    def _get_header_value(self, headers: List[Dict], name: str) -> Optional[str]:
        """从邮件头中获取指定字段的值"""
        for header in headers:
            if header.get('name', '').lower() == name.lower():
                return header.get('value')
        return None
        
    def _get_email_body(self, payload: Dict) -> str:
        """递归提取邮件正文"""
        body = ''
        if 'parts' in payload:
            for part in payload['parts']:
                body += self._get_email_body(part)
        else:
            data = payload.get('body', {}).get('data')
            if data:
                try:
                    text = base64.urlsafe_b64decode(
                        data.encode('UTF-8')
                    ).decode('utf-8', errors='ignore')
                    body += text
                except Exception as e:
                    print(f"解码邮件内容失败: {e}")
        return body
        
    def _clean_html_content(self, html_content: str) -> str:
        """清理HTML内容并提取文本"""
        if not html_content:
            return ""
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator='\n', strip=True)
        except Exception as e:
            print(f"清理HTML内容失败: {e}")
            return html_content
            
    def refresh_token(self):
        """刷新访问令牌"""
        if not self.service:
            print("Gmail服务未初始化")
            return
            
        try:
            # 进行简单的API调用来测试和刷新令牌
            self.service.users().getProfile(userId='me').execute()
            print("令牌刷新成功")
        except Exception as e:
            print(f"令牌刷新失败: {e}")