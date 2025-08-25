#!/bin/bash
# -*- coding: utf-8 -*-
"""
Microsoft验证码管理器 启动脚本
"""

echo "🔐 Microsoft验证码管理器 - 启动中..."
echo "======================================"

# 检查Python版本
python_version=$(python3 --version 2>/dev/null || python --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ 检测到Python: $python_version"
else
    echo "❌ 错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖包..."
pip_cmd="pip3"
if ! command -v pip3 &> /dev/null; then
    pip_cmd="pip"
fi

if ! $pip_cmd list | grep -q streamlit; then
    echo "⚠️  检测到缺少依赖，正在安装..."
    $pip_cmd install -r requirements.txt
else
    echo "✅ 依赖检查完成"
fi

# 检查配置文件
if [ ! -f "config/credentials.json" ]; then
    echo "⚠️  警告: 未找到 config/credentials.json"
    echo "   请先在Google Cloud Console配置Gmail API并下载凭据文件"
fi

echo "🚀 启动应用..."
echo "======================================"

# 启动应用
if command -v streamlit &> /dev/null; then
    streamlit run app.py
else
    python app.py
fi