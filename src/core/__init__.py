# -*- coding: utf-8 -*-
"""
Microsoft验证码管理器 - 核心模块
"""

__version__ = "1.0.0"
__author__ = "Microsoft Code Manager"
__description__ = "专业的Microsoft验证码管理工具"

from .gmail_service import GmailService
from .microsoft_extractor import MicrosoftCodeExtractor, EmailQueryBuilder

__all__ = ['GmailService', 'MicrosoftCodeExtractor', 'EmailQueryBuilder']