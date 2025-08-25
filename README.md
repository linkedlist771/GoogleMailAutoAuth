# 🔐 Microsoft验证码管理器

一个专业、安全的Microsoft验证码自动获取和管理工具。通过Gmail API智能识别并展示Microsoft发送的验证码邮件，让您的账户验证过程更加便捷。

## ✨ 主要特性

- 🎯 **专注Microsoft**: 专门针对Microsoft验证码邮件进行优化
- 🇨🇳 **中文界面**: 完全中文化的用户界面，操作简单直观  
- 🔒 **安全可靠**: 基于官方Gmail API，确保数据安全
- 🚀 **智能识别**: 自动提取和解析验证码，支持多种格式
- 📊 **历史管理**: 显示验证码接收历史和详细信息
- ⚡ **实时刷新**: 支持实时获取最新的验证码邮件
- 🔄 **自动维护**: 自动刷新访问令牌，无需手动干预

## 🏗️ 项目结构

```
Microsoft验证码管理器/
├── app.py                          # 主入口文件
├── requirements.txt                 # 依赖包列表
├── README.md                       # 项目说明
├── config/                         # 配置文件目录
│   ├── credentials.json           # Google API凭据文件
│   └── token.json                 # 访问令牌文件
├── src/                           # 源代码目录
│   ├── __init__.py
│   ├── core/                      # 核心功能模块
│   │   ├── __init__.py
│   │   ├── gmail_service.py       # Gmail服务封装
│   │   └── microsoft_extractor.py # Microsoft验证码提取器
│   ├── ui/                        # 用户界面模块
│   │   ├── __init__.py
│   │   └── main_app.py           # 主界面应用
│   └── utils/                     # 工具模块
│       ├── __init__.py
│       └── config.py             # 配置管理
└── demos/                         # 演示文件
    └── (清理后无关文件)
```

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装Python 3.8或更高版本：

```bash
python --version
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置Google API

1. 访问[Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用Gmail API
4. 创建OAuth 2.0凭据
5. 下载凭据文件并重命名为`credentials.json`
6. 将`credentials.json`放入`config/`目录

### 4. 运行应用

```bash
# 方式1: 直接运行
python app.py

# 方式2: 使用Streamlit命令
streamlit run app.py
```

### 5. 首次授权

首次运行时，应用会自动打开浏览器进行Google账户授权。完成授权后，程序会自动保存访问令牌。

## 🖥️ 使用说明

### 主界面功能

1. **实时时间显示**: 显示当前北京时间
2. **智能验证码提取**: 自动从Microsoft邮件中提取验证码
3. **历史记录管理**: 查看验证码接收历史和详细信息
4. **一键刷新**: 点击刷新按钮获取最新邮件

### 侧边栏设置

- **获取邮件数量**: 设置每次获取的邮件数量（1-100封）
- **服务状态**: 显示Gmail服务连接状态
- **刷新时间**: 显示最后一次刷新的时间
- **版本信息**: 显示应用版本和说明

### 验证码卡片

每个验证码以精美卡片形式展示：
- 🔢 **验证码**: 大字体显示6-8位验证码
- 📊 **接收次数**: 显示该验证码接收的总次数
- ⏰ **时间信息**: 显示最新接收时间和所有历史时间
- 📧 **邮件详情**: 可展开查看完整邮件内容

## ⚙️ 配置选项

### 支持的Microsoft邮件地址

应用自动识别以下Microsoft官方邮件地址：
- `account-security-noreply@accountprotection.microsoft.com`
- `noreply@account.microsoft.com` 
- `microsoft-noreply@microsoft.com`
- `noreply@email.teams.microsoft.com`

### 自定义配置

可在`src/utils/config.py`中修改：
- 邮件查询数量
- 令牌刷新频率
- UI主题色彩
- 支持的发件人列表

## 🔧 技术特性

- **异步处理**: 支持后台异步获取邮件，不阻塞界面
- **智能重试**: 网络异常时自动重试，确保服务稳定
- **内容清理**: 自动清理HTML标签，提取纯文本内容
- **日期解析**: 智能解析多种日期格式
- **错误处理**: 完善的错误处理和用户提示

## 🛡️ 安全说明

- ✅ 仅使用只读权限访问Gmail
- ✅ 凭据文件本地存储，不会上传到任何服务器
- ✅ 基于官方Google API，安全可靠
- ✅ 支持OAuth 2.0安全认证流程
- ✅ 自动令牌刷新，无需存储密码

## 📋 系统要求

- **Python**: 3.8或更高版本
- **操作系统**: Windows、macOS、Linux
- **网络**: 能够访问Google服务
- **浏览器**: 用于OAuth授权（仅首次使用）

## 🐛 问题排查

### 常见问题

1. **Gmail服务连接失败**
   - 检查`config/credentials.json`是否存在且有效
   - 确认网络能访问Google服务
   - 重新进行OAuth授权

2. **无法找到验证码**
   - 确认Microsoft确实发送了验证码邮件
   - 检查邮件是否在垃圾箱中
   - 增加获取邮件数量

3. **令牌过期**
   - 应用会自动刷新令牌
   - 如持续出现问题，删除`config/token.json`重新授权

## 📄 更新日志

### v1.0.0 (2024-12-25)
- 🎉 初始发布版本
- ✨ 专注Microsoft验证码管理
- 🇨🇳 完全中文化界面
- 🔒 基于Gmail API的安全认证
- 📱 响应式Web界面设计
- 🔄 自动令牌刷新功能

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进这个项目！

---

**注意**: 本工具仅用于管理您自己的Microsoft验证码邮件，请遵守相关法律法规和服务条款。