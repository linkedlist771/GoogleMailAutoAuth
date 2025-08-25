# -*- coding: utf-8 -*-
"""
配置管理模块
集中管理应用程序配置
"""

import os
from typing import Dict, Any

class Config:
    """应用程序配置类"""
    
    # 应用基本信息
    APP_NAME = "Microsoft验证码管理器"
    APP_ICON = "🔐"
    VERSION = "1.0.0"
    
    # 文件路径配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
    TOKEN_FILE = os.path.join(CONFIG_DIR, "token.json")
    
    # Gmail API配置
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # UI配置
    PAGE_CONFIG = {
        "page_title": APP_NAME,
        "page_icon": APP_ICON,
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    # 邮件查询配置
    DEFAULT_MAX_RESULTS = 40
    DEFAULT_DAYS_BACK = 7
    
    # Microsoft邮件配置
    MICROSOFT_SENDERS = [
        'account-security-noreply@accountprotection.microsoft.com',
        'noreply@account.microsoft.com',
        'microsoft-noreply@microsoft.com',
        'noreply@email.teams.microsoft.com'
    ]
    
    # 令牌刷新配置
    TOKEN_REFRESH_INTERVAL_DAYS = 6
    
    # UI主题配置
    THEME = {
        'primary_color': '#0078d4',  # Microsoft蓝色
        'secondary_color': '#6c757d',
        'success_color': '#28a745',
        'warning_color': '#ffc107',
        'error_color': '#dc3545',
        'background_color': '#f8f9fa',
        'card_background': '#ffffff',
        'sidebar_background': '#f1f3f4',
        'text_color': '#2c3e50',
        'text_muted': '#6c757d',
        'border_color': '#e9ecef',
        'shadow_color': 'rgba(0, 0, 0, 0.1)',
        'gradient_start': '#667eea',
        'gradient_end': '#764ba2',
        'accent_blue': '#4285f4',
        'accent_green': '#34a853',
        'accent_red': '#ea4335',
        'accent_yellow': '#fbbc05',
        'font': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        'font_mono': 'JetBrains Mono, Consolas, Monaco, monospace'
    }
    
    @classmethod
    def ensure_config_dir(cls):
        """确保配置目录存在"""
        os.makedirs(cls.CONFIG_DIR, exist_ok=True)
    
    @classmethod 
    def get_microsoft_query(cls) -> str:
        """获取Microsoft邮件查询字符串"""
        senders = ' OR '.join([f'from:{sender}' for sender in cls.MICROSOFT_SENDERS])
        return f"({senders})"
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            'app_name': cls.APP_NAME,
            'app_icon': cls.APP_ICON,
            'version': cls.VERSION,
            'credentials_file': cls.CREDENTIALS_FILE,
            'token_file': cls.TOKEN_FILE,
            'max_results': cls.DEFAULT_MAX_RESULTS,
            'days_back': cls.DEFAULT_DAYS_BACK,
            'microsoft_query': cls.get_microsoft_query(),
            'theme': cls.THEME
        }