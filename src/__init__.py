# -*- coding: utf-8 -*-
"""
Microsoft验证码管理器

一个专业的Microsoft验证码管理工具，通过Gmail API自动获取并管理Microsoft账户验证码。

主要功能:
- 自动获取Microsoft验证码邮件
- 智能解析验证码内容
- 用户友好的中文界面
- 验证码历史管理
- 自动令牌刷新

使用方法:
    python app.py
    或
    streamlit run app.py
"""

__version__ = "1.0.0"
__author__ = "Microsoft Code Manager Team"
__description__ = "专业的Microsoft验证码管理工具"

import sys
import os

# 确保项目根目录在Python路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)