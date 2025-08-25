# -*- coding: utf-8 -*-
"""
Microsoft验证码处理模块
专门用于处理Microsoft邮件验证码的提取和解析
"""

import re
from typing import List, Dict, Optional
from datetime import datetime

class MicrosoftCodeExtractor:
    """Microsoft验证码提取器"""
    
    # Microsoft验证码匹配模式
    CODE_PATTERNS = [
        r'Your single-use code is[：:\s]*(\d{6,8})',  # Microsoft英文模式
        r'安全代码[：:]\s*(\d{6,8})',  # 中文模式
        r'Security code[：:]\s*(\d{6,8})',  # 英文模式  
        r'验证码[：:]\s*(\d{6,8})',  # 通用中文
        r'verification code[：:]\s*(\d{6,8})',  # 通用英文
        r'code is[：:\s]*(\d{6,8})',  # 简化英文模式
        r'(?:^|\s)(\d{6})(?:\s|$)',  # 6位数字（独立存在）
        r'(?:^|\s)(\d{8})(?:\s|$)',  # 8位数字（独立存在）
    ]
    
    def __init__(self):
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.CODE_PATTERNS]
    
    def extract_code(self, content: str) -> Optional[str]:
        """从邮件内容中提取验证码"""
        if not content:
            return None
            
        # 按优先级尝试各种模式
        for pattern in self.patterns:
            match = pattern.search(content)
            if match:
                code = match.group(1)
                # 验证码长度检查（Microsoft通常是6-8位）
                if 6 <= len(code) <= 8:
                    return code
        return None
    
    def process_emails(self, emails: List[Dict]) -> List[Dict]:
        """处理邮件列表，提取验证码并组织数据"""
        code_entries = []
        
        for email in emails:
            code = self.extract_code(email.get('content', ''))
            if code:
                try:
                    date_obj = datetime.strptime(email['date'], '%Y-%m-%d %H:%M:%S')
                    code_entries.append({
                        'code': code,
                        'date': date_obj,
                        'date_str': email['date'],
                        'subject': email.get('subject', ''),
                        'from': email.get('from', ''),
                        'content': email.get('content', '')
                    })
                except ValueError:
                    # 日期格式解析失败，跳过
                    continue
        
        # 按日期排序（最新的在前）
        code_entries.sort(key=lambda x: x['date'], reverse=True)
        
        # 合并重复的验证码
        return self._combine_duplicate_codes(code_entries)
    
    def _combine_duplicate_codes(self, code_entries: List[Dict]) -> List[Dict]:
        """合并重复的验证码，保留多个接收时间"""
        combined_entries = []
        current_code = None
        current_data = []
        
        for entry in code_entries:
            if current_code != entry['code']:
                if current_code is not None:
                    combined_entries.append({
                        'code': current_code,
                        'count': len(current_data),
                        'latest_date': current_data[0]['date_str'],
                        'dates': [item['date_str'] for item in current_data],
                        'emails': current_data
                    })
                current_code = entry['code']
                current_data = [entry]
            else:
                current_data.append(entry)
        
        # 添加最后一个条目
        if current_code is not None:
            combined_entries.append({
                'code': current_code,
                'count': len(current_data),
                'latest_date': current_data[0]['date_str'],
                'dates': [item['date_str'] for item in current_data],
                'emails': current_data
            })
        
        return combined_entries
    
    def is_microsoft_email(self, from_address: str) -> bool:
        """检查是否为Microsoft官方邮件"""
        microsoft_domains = [
            'account-security-noreply@accountprotection.microsoft.com',
            'noreply@account.microsoft.com',
            'microsoft-noreply@microsoft.com',
            'noreply@email.teams.microsoft.com'
        ]
        
        if not from_address:
            return False
            
        return any(domain in from_address.lower() for domain in microsoft_domains)

class EmailQueryBuilder:
    """邮件查询构建器"""
    
    @staticmethod
    def build_microsoft_query() -> str:
        """构建Microsoft验证码邮件查询"""
        return "from:account-security-noreply@accountprotection.microsoft.com OR from:noreply@account.microsoft.com"
    
    @staticmethod
    def build_date_range_query(days_back: int = 7) -> str:
        """构建日期范围查询（最近N天）"""
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        return f"after:{start_date.strftime('%Y/%m/%d')} before:{end_date.strftime('%Y/%m/%d')}"