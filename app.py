#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Microsoft验证码管理器 - 主入口文件

这是一个专门用于管理Microsoft账户验证码的应用程序。
通过Gmail API自动获取并显示Microsoft发送的验证码邮件。

使用方法:
    python app.py

或者使用Streamlit运行:
    streamlit run app.py

作者: 
版本: 1.0.0
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 导入主应用
from ui.main_app import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"应用启动失败: {e}")
        sys.exit(1)