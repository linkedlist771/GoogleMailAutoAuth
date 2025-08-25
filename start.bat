@echo off
chcp 65001 >nul
title Microsoft验证码管理器

echo.
echo 🔐 Microsoft验证码管理器 - 启动中...
echo ======================================

:: 检查Python版本
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version') do echo ✅ 检测到Python: %%i
)

:: 检查依赖
echo.
echo 📦 检查依赖包...
pip list | findstr streamlit >nul
if %errorlevel% neq 0 (
    echo ⚠️  检测到缺少依赖，正在安装...
    pip install -r requirements.txt
) else (
    echo ✅ 依赖检查完成
)

:: 检查配置文件
if not exist "config\credentials.json" (
    echo.
    echo ⚠️  警告: 未找到 config\credentials.json
    echo    请先在Google Cloud Console配置Gmail API并下载凭据文件
)

echo.
echo 🚀 启动应用...
echo ======================================
echo.

:: 启动应用
streamlit run app.py
if %errorlevel% neq 0 (
    python app.py
)

pause