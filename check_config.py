#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证工具
用于检查Microsoft验证码管理器的配置是否正确
"""

import os
import json
import sys

def check_config():
    """检查配置文件"""
    print("🔍 配置检查工具")
    print("=" * 30)
    
    # 检查目录结构
    print("\n📁 检查目录结构...")
    required_dirs = ["config", "src", "src/core", "src/ui", "src/utils"]
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (缺失)")
    
    # 检查必要文件
    print("\n📄 检查必要文件...")
    required_files = [
        "app.py",
        "requirements.txt", 
        "src/core/gmail_service.py",
        "src/core/microsoft_extractor.py",
        "src/ui/main_app.py",
        "src/utils/config.py"
    ]
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} (缺失)")
    
    # 检查配置文件
    print("\n⚙️ 检查配置文件...")
    
    # credentials.json
    cred_file = "config/credentials.json"
    if os.path.exists(cred_file):
        try:
            with open(cred_file, 'r') as f:
                cred_data = json.load(f)
            
            if 'installed' in cred_data or 'web' in cred_data:
                print("✅ config/credentials.json (格式正确)")
            else:
                print("⚠️  config/credentials.json (格式可能有误)")
        except json.JSONDecodeError:
            print("❌ config/credentials.json (JSON格式错误)")
        except Exception as e:
            print(f"❌ config/credentials.json (读取失败: {e})")
    else:
        print("⚠️  config/credentials.json (未找到 - 首次运行需要)")
    
    # token.json
    token_file = "config/token.json"
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            if 'token' in token_data and 'refresh_token' in token_data:
                print("✅ config/token.json (格式正确)")
            else:
                print("⚠️  config/token.json (格式可能有误)")
        except json.JSONDecodeError:
            print("❌ config/token.json (JSON格式错误)")
        except Exception as e:
            print(f"❌ config/token.json (读取失败: {e})")
    else:
        print("ℹ️  config/token.json (未找到 - 首次授权后自动生成)")
    
    # 检查Python包
    print("\n📦 检查Python依赖...")
    required_packages = [
        "streamlit",
        "google-auth-oauthlib", 
        "google-auth-httplib2",
        "google-api-python-client",
        "beautifulsoup4",
        "schedule"
    ]
    
    try:
        import pkg_resources
        installed_packages = {pkg.project_name.lower(): pkg.version 
                            for pkg in pkg_resources.working_set}
        
        for package in required_packages:
            if package.lower() in installed_packages:
                print(f"✅ {package} ({installed_packages[package.lower()]})")
            else:
                print(f"❌ {package} (未安装)")
    except ImportError:
        print("⚠️  无法检查包版本，请确保已安装requirements.txt中的依赖")
    
    print("\n" + "=" * 30)
    print("✨ 配置检查完成!")
    
    # 提供建议
    print("\n💡 使用建议:")
    if not os.path.exists("config/credentials.json"):
        print("1. 请在Google Cloud Console配置Gmail API")
        print("2. 下载OAuth 2.0凭据文件并保存为config/credentials.json")
    
    print("3. 运行 'python app.py' 或 'streamlit run app.py' 启动应用")
    print("4. 首次运行时会自动打开浏览器进行授权")

if __name__ == "__main__":
    try:
        check_config()
    except KeyboardInterrupt:
        print("\n\n❌ 检查被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        sys.exit(1)