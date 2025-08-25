# -*- coding: utf-8 -*-
"""
主界面模块
基于Streamlit的Microsoft验证码管理界面
"""

import streamlit as st
import threading
import time
import schedule
from datetime import datetime, timedelta
from typing import List, Dict

# 本地导入
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.gmail_service import GmailService
from core.microsoft_extractor import MicrosoftCodeExtractor, EmailQueryBuilder
from utils.config import Config

class MicrosoftCodeApp:
    """Microsoft验证码应用主类"""
    
    def __init__(self):
        self.config = Config()
        self.gmail_service = None
        self.code_extractor = MicrosoftCodeExtractor()
        self.query_builder = EmailQueryBuilder()
        
        # 确保配置目录存在
        Config.ensure_config_dir()
        
        # 初始化Streamlit页面配置
        st.set_page_config(**Config.PAGE_CONFIG)
        
        # 加载自定义CSS
        self._load_custom_css()
        
        # 初始化session state
        self._init_session_state()
        
        # 启动后台任务
        self._start_background_tasks()
    
    def _load_custom_css(self):
        """加载自定义CSS样式"""
        theme = Config.THEME
        custom_css = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
        
        /* 全局样式 */
        .stApp {{
            background-color: {theme['background_color']};
            font-family: {theme['font']};
        }}
        
        /* 主标题样式 */
        .main-title {{
            background: linear-gradient(135deg, {theme['gradient_start']}, {theme['gradient_end']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0;
            letter-spacing: -0.02em;
        }}
        
        /* 时间显示样式 */
        .time-display {{
            background: {theme['card_background']};
            border-radius: 16px;
            padding: 1rem 2rem;
            text-align: center;
            box-shadow: 0 2px 10px {theme['shadow_color']};
            border: 1px solid {theme['border_color']};
            margin: 1rem 0;
        }}
        
        /* 侧边栏样式 */
        .css-1d391kg {{
            background-color: {theme['sidebar_background']} !important;
        }}
        
        /* 按钮样式 */
        .stButton > button {{
            background: linear-gradient(135deg, {theme['primary_color']}, {theme['accent_blue']});
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 120, 212, 0.3);
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 120, 212, 0.4);
        }}
        
        /* 成功消息样式 */
        .stSuccess {{
            background-color: {theme['accent_green']};
            color: white;
            border-radius: 12px;
            padding: 1rem;
            border: none;
        }}
        
        /* 错误消息样式 */
        .stError {{
            background-color: {theme['accent_red']};
            color: white;
            border-radius: 12px;
            padding: 1rem;
            border: none;
        }}
        
        /* 信息消息样式 */
        .stInfo {{
            background-color: {theme['accent_blue']};
            color: white;
            border-radius: 12px;
            padding: 1rem;
            border: none;
        }}
        
        /* 警告消息样式 */
        .stWarning {{
            background-color: {theme['accent_yellow']};
            color: #333;
            border-radius: 12px;
            padding: 1rem;
            border: none;
        }}
        
        /* 指标卡片样式 */
        .metric-card {{
            background: {theme['card_background']};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 10px {theme['shadow_color']};
            border: 1px solid {theme['border_color']};
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        
        /* 分隔线样式 */
        hr {{
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent, {theme['border_color']}, transparent);
            margin: 2rem 0;
        }}
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)
    
    def _init_session_state(self):
        """初始化session state"""
        if 'gmail_service' not in st.session_state:
            st.session_state.gmail_service = None
        if 'emails' not in st.session_state:
            st.session_state.emails = []
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = None
        if 'service_initialized' not in st.session_state:
            st.session_state.service_initialized = False
    
    def _start_background_tasks(self):
        """启动后台定时任务"""
        # 设置令牌刷新任务
        schedule.every(Config.TOKEN_REFRESH_INTERVAL_DAYS).days.do(self._refresh_token_task)
        
        # 在单独线程中运行定时任务
        if not hasattr(st.session_state, 'background_thread_started'):
            threading.Thread(target=self._run_scheduled_tasks, daemon=True).start()
            st.session_state.background_thread_started = True
    
    def _run_scheduled_tasks(self):
        """运行定时任务"""
        while True:
            schedule.run_pending()
            time.sleep(3600)  # 每小时检查一次
    
    def _refresh_token_task(self):
        """刷新令牌任务"""
        if st.session_state.gmail_service:
            st.session_state.gmail_service.refresh_token()
    
    def _initialize_gmail_service(self) -> bool:
        """初始化Gmail服务"""
        if st.session_state.service_initialized:
            return st.session_state.gmail_service is not None
        
        try:
            gmail_service = GmailService(
                Config.CREDENTIALS_FILE, 
                Config.TOKEN_FILE
            )
            service = gmail_service.initialize()
            
            if service:
                st.session_state.gmail_service = gmail_service
                st.session_state.service_initialized = True
                return True
            else:
                st.session_state.gmail_service = None
                st.session_state.service_initialized = True
                return False
                
        except Exception as e:
            st.error(f"初始化Gmail服务时发生错误: {str(e)}")
            st.session_state.gmail_service = None
            st.session_state.service_initialized = True
            return False
    
    def _fetch_emails(self, max_results: int = None) -> List[Dict]:
        """获取邮件"""
        if not st.session_state.gmail_service:
            return []
        
        max_results = max_results or Config.DEFAULT_MAX_RESULTS
        query = Config.get_microsoft_query()
        
        try:
            return st.session_state.gmail_service.get_emails(query, max_results)
        except Exception as e:
            st.error(f"获取邮件时发生错误: {str(e)}")
            return []
    
    def _render_header(self):
        """渲染页面头部"""
        # 主标题
        st.markdown(f'<h1 class="main-title">{Config.APP_ICON} {Config.APP_NAME}</h1>', 
                   unsafe_allow_html=True)
        
        # 显示当前时间（北京时间）
        current_time = datetime.now() + timedelta(hours=8)
        time_str = current_time.strftime('%Y年%m月%d日 %H:%M:%S')
        
        st.markdown(f'''
        <div class="time-display">
            <h3 style="margin: 0; color: {Config.THEME['text_color']};">
                🕰️ 当前时间: {time_str} (北京时间)
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        # 添加分隔线
        st.markdown("<hr>", unsafe_allow_html=True)
    
    def _render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            # 侧边栏标题 - 更现代的设计
            st.markdown(f'''
            <div style="
                background: linear-gradient(135deg, {Config.THEME['primary_color']}, {Config.THEME['accent_blue']});
                border-radius: 16px;
                padding: 1.5rem;
                text-align: center;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 15px rgba(0, 120, 212, 0.2);
            ">
                <div style="
                    width: 50px;
                    height: 50px;
                    background: rgba(255,255,255,0.2);
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 0.8rem auto;
                    font-size: 1.5rem;
                ">{Config.APP_ICON}</div>
                <h2 style="
                    color: white;
                    margin: 0;
                    font-size: 1.3rem;
                    font-weight: 600;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.1);
                ">Microsoft 验证码管理器</h2>
                <p style="
                    color: rgba(255,255,255,0.9);
                    margin: 0.5rem 0 0 0;
                    font-size: 0.9rem;
                ">安全、高效、易用</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # 邮件获取设置区域
            st.markdown(f'''
            <div style="
                background: {Config.THEME['card_background']};
                border-radius: 12px;
                padding: 1.2rem;
                margin-bottom: 1rem;
                border: 1px solid {Config.THEME['border_color']};
            ">
                <h3 style="
                    margin: 0 0 1rem 0;
                    color: {Config.THEME['text_color']};
                    font-size: 1rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                ">📥 邮件获取设置</h3>
            </div>
            ''', unsafe_allow_html=True)
            max_results = st.number_input(
                "获取邮件数量",
                min_value=1,
                max_value=100,
                value=Config.DEFAULT_MAX_RESULTS,
                step=5,
                help="设置一次获取的最大邮件数量"
            )
            
            # 刷新按钮 - 更美观的设计
            st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)
            refresh_clicked = st.button(
                "🔄 刷新邮件", 
                use_container_width=True,
                help="点击获取最新的Microsoft验证码邮件"
            )
            
            # 服务状态区域
            st.markdown(f'''
            <div style="
                background: {Config.THEME['card_background']};
                border-radius: 12px;
                padding: 1.2rem;
                margin: 1.5rem 0;
                border: 1px solid {Config.THEME['border_color']};
            ">
                <h3 style="
                    margin: 0 0 1rem 0;
                    color: {Config.THEME['text_color']};
                    font-size: 1rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                ">📊 服务状态</h3>
            ''', unsafe_allow_html=True)
            
           
            
            # 最后刷新时间显示
            if st.session_state.last_refresh:
                st.markdown(f'''
                <div style="
                    background: linear-gradient(135deg, #e3f2fd, #ffffff);
                    border: 1px solid #bbdefb;
                    border-radius: 8px;
                    padding: 0.8rem;
                    text-align: center;
                ">
                    <div style="
                        color: {Config.THEME['text_muted']};
                        font-size: 0.8rem;
                        margin-bottom: 0.2rem;
                    ">上次刷新</div>
                    <div style="
                        color: {Config.THEME['primary_color']};
                        font-weight: 600;
                        font-size: 0.95rem;
                    ">{st.session_state.last_refresh}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)  # 关闭服务状态区域
            
            # 关于信息区域
            st.markdown(f'''
            <div style="
                background: {Config.THEME['card_background']};
                border-radius: 12px;
                padding: 1.2rem;
                margin-top: 1.5rem;
                border: 1px solid {Config.THEME['border_color']};
                text-align: center;
            ">
                <h3 style="
                    margin: 0 0 1rem 0;
                    color: {Config.THEME['text_color']};
                    font-size: 1rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                ">ℹ️ 关于</h3>
                
                <div style="
                    background: linear-gradient(135deg, #f8f9fa, #ffffff);
                    border-radius: 8px;
                    padding: 1rem;
                    border: 1px solid {Config.THEME['border_color']};
                ">
                    <div style="
                        color: {Config.THEME['text_color']};
                        font-weight: 600;
                        margin-bottom: 0.5rem;
                    ">版本: {Config.VERSION}</div>
                    
                    <div style="
                        color: {Config.THEME['text_muted']};
                        font-size: 0.9rem;
                        line-height: 1.4;
                        margin: 0.5rem 0;
                    ">专为Microsoft验证码管理</div>
                    
                    <div style="
                        display: flex;
                        justify-content: center;
                        gap: 1rem;
                        margin-top: 0.8rem;
                    ">
                        <span style="
                            background: {Config.THEME['accent_green']};
                            color: white;
                            padding: 0.3rem 0.6rem;
                            border-radius: 12px;
                            font-size: 0.8rem;
                        ">安全</span>
                        <span style="
                            background: {Config.THEME['accent_blue']};
                            color: white;
                            padding: 0.3rem 0.6rem;
                            border-radius: 12px;
                            font-size: 0.8rem;
                        ">高效</span>
                        <span style="
                            background: {Config.THEME['primary_color']};
                            color: white;
                            padding: 0.3rem 0.6rem;
                            border-radius: 12px;
                            font-size: 0.8rem;
                        ">易用</span>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            return refresh_clicked, max_results
    
    def _render_email_list(self, emails: List[Dict]):
        """渲染邮件列表 - 简化版本，只显示时间和验证码"""
        if not emails:
            st.markdown(f'''
            <div class="metric-card" style="text-align: center; padding: 2rem;">
                <h2 style="color: {Config.THEME['text_muted']}; margin: 1rem 0;">📭</h2>
                <h3 style="color: {Config.THEME['text_muted']}; margin: 0;">暂无Microsoft验证码邮件</h3>
                <p style="color: {Config.THEME['text_muted']}; margin: 0.5rem 0;">点击刷新按钮获取最新邮件</p>
            </div>
            ''', unsafe_allow_html=True)
            return
        
        # 处理邮件，提取验证码
        processed_codes = self.code_extractor.process_emails(emails)
        
        if not processed_codes:
            st.markdown(f'''
            <div class="metric-card" style="text-align: center; padding: 2rem;">
                <h2 style="color: {Config.THEME['warning_color']}; margin: 1rem 0;">📮</h2>
                <h3 style="color: {Config.THEME['warning_color']}; margin: 0;">未找到有效的验证码</h3>
                <p style="color: {Config.THEME['text_muted']}; margin: 0.5rem 0;">请检查邮件内容或尝试更新查询条件</p>
            </div>
            ''', unsafe_allow_html=True)
            return
        
        # 标题和统计
        st.markdown(f'''
        <div style="text-align: center; margin: 2rem 0;">
            <h1 style="color: {Config.THEME['primary_color']}; margin: 0;">🔐 Microsoft验证码</h1>
            <p style="color: {Config.THEME['text_muted']}; margin: 0.5rem 0; font-size: 1.2rem;">共找到 <strong>{len(processed_codes)}</strong> 个验证码</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # 显示简化的验证码列表
        for i, entry in enumerate(processed_codes):
            self._render_simple_code_card(entry, i)
    
    def _render_simple_code_card(self, entry: Dict, index: int):
        """渲染简化的验证码卡片 - 只显示时间和验证码"""
        theme = Config.THEME
        
        # 简化的验证码卡片
        st.markdown(f'''
        <div style="
            background: {theme['card_background']};
            border: 1px solid {theme['border_color']};
            border-radius: 12px;
            margin: 1rem 0;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transition: all 0.2s ease;
        " class="email-card">
            
            <!-- 验证码显示区域 -->
            <div style="text-align: center; margin-bottom: 1rem;">
                <h1 style="
                    margin: 0 0 0.5rem 0;
                    font-size: 3.5rem;
                    font-weight: 800;
                    font-family: JetBrains Mono, Consolas, Monaco, monospace;
                    color: {theme['primary_color']};
                    letter-spacing: 0.1em;
                    cursor: pointer;
                    user-select: all;
                " class="code-display" title="点击选中验证码">{entry['code']}</h1>
                
                <p style="
                    margin: 0;
                    color: {theme['text_muted']};
                    font-size: 1.1rem;
                    font-weight: 500;
                ">六位安全验证码</p>
            </div>
            
            <!-- 时间信息 -->
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <div style="flex: 1;">
                    <span style="
                        color: {theme['text_color']};
                        font-weight: 600;
                        font-size: 0.95rem;
                    ">{entry['latest_date']}</span>
                    <span style='margin-left: 0.5rem; background: #4CAF50; color: white; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.7rem;'>最新</span>
                </div>
                
                <div style="text-align: right;">
                    <div style="
                        background: {theme['accent_blue']};
                        color: white;
                        padding: 0.3rem 0.8rem;
                        border-radius: 20px;
                        font-size: 0.85rem;
                        font-weight: 500;
                        margin-bottom: 0.3rem;
                    ">{entry['count']} 封邮件</div>
                </div>
            </div>
            
        ''', unsafe_allow_html=True)
        
        # 如果有多个时间记录，显示时间列表
        if len(entry['dates']) > 1:
            st.markdown(f'''
            <div style="
                background: #f8f9fa;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="
                    margin: 0 0 0.8rem 0;
                    color: {theme['text_color']};
                    font-size: 1rem;
                    font-weight: 600;
                ">📅 接收时间记录</h4>
            ''', unsafe_allow_html=True)
            
            # 显示所有时间记录
            for i, date in enumerate(entry['dates']):
                is_latest = (i == 0)
                st.markdown(f'''
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    padding: 0.5rem;
                    margin-bottom: 0.3rem;
                    background: {"linear-gradient(135deg, #e3f2fd, #ffffff)" if is_latest else "white"};
                    border-radius: 6px;
                    {"border-left: 3px solid " + theme['primary_color'] if is_latest else ""};
                ">
                    <div style="flex: 1;">
                        <span style="
                            color: {theme['text_color']};
                            font-weight: {"600" if is_latest else "500"};
                            font-size: 0.9rem;
                        ">{date}</span>
                        {"<span style='margin-left: 0.5rem; background: #4CAF50; color: white; padding: 0.1rem 0.4rem; border-radius: 8px; font-size: 0.7rem;'>最新</span>" if is_latest else ""}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 邮件详情展开器
        with st.expander(f"📧 查看邮件内容 ({len(entry['emails'])} 封)", expanded=False):
            for i, email in enumerate(entry['emails']):
                content = email.get('content', '未找到邮件内容')
                
                st.markdown(f'''
                <div style="
                    background: white;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 0.9rem;
                    line-height: 1.6;
                    color: {theme['text_color']};
                ">
                    <div style="
                        font-size: 0.8rem;
                        color: {theme['text_muted']};
                        margin-bottom: 0.5rem;
                        padding-bottom: 0.5rem;
                        border-bottom: 1px solid #f0f0f0;
                    ">{email.get('date_str', '未知时间')}</div>
                    
                    <pre style="
                        background: #f8f9fa;
                        padding: 1rem;
                        border-radius: 6px;
                        overflow-x: auto;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 0.85rem;
                        line-height: 1.4;
                        color: #333;
                        border: 1px solid #e9ecef;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        margin: 0;
                    "><code>{content}</code></pre>
                </div>
                ''', unsafe_allow_html=True)
        
        # 关闭主卡片
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_code_card(self, entry: Dict, index: int):
        """渲染单个验证码卡片"""
        theme = Config.THEME
        
        # 添加CSS改进邮件卡片的hover效果
        st.markdown(f'''
        <style>
        .email-card:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }}
        .code-display {{
            user-select: all;
            cursor: pointer;
        }}
        .code-display:hover {{
            transform: scale(1.05);
        }}
        </style>
        ''', unsafe_allow_html=True)
        
        # 邮件主题风格的设计
        st.markdown(f'''
        <div class="email-card" style="
            background: {theme['card_background']};
            border: 1px solid {theme['border_color']};
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transition: all 0.2s ease;
        ">
            <!-- 邮件头部 -->
            <div style="
                background: linear-gradient(135deg, #f8f9fa, #ffffff);
                padding: 1.2rem 1.5rem;
                border-bottom: 1px solid {theme['border_color']};
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <!-- 验证码图标 -->
                    <div style="
                        width: 48px;
                        height: 48px;
                        background: linear-gradient(135deg, {theme['primary_color']}, {theme['accent_blue']});
                        border-radius: 10px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 1.5rem;
                        font-weight: bold;
                    ">🔐</div>
                    
                    <div>
                        <h3 style="
                            margin: 0;
                            font-size: 1.1rem;
                            font-weight: 600;
                            color: {theme['text_color']};
                        ">Microsoft 安全验证码</h3>
                        <p style="
                            margin: 0.2rem 0 0 0;
                            color: {theme['text_muted']};
                            font-size: 0.9rem;
                        ">来自 Microsoft 安全团队</p>
                    </div>
                </div>
                
                <div style="text-align: right;">
                    <div style="
                        background: {theme['accent_blue']};
                        color: white;
                        padding: 0.3rem 0.8rem;
                        border-radius: 20px;
                        font-size: 0.85rem;
                        font-weight: 500;
                        margin-bottom: 0.3rem;
                    ">{entry['count']} 封邮件</div>
                    <p style="
                        margin: 0;
                        color: {theme['text_muted']};
                        font-size: 0.8rem;
                    ">最新: {entry['latest_date']}</p>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        # 验证码主要内容区域
        st.markdown(f'''
            <!-- 验证码显示区域 -->
            <div style="padding: 1.5rem;">
                <div style="
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border-radius: 12px;
                    padding: 2rem;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                    margin-bottom: 1.5rem;
                ">
                    <!-- 背景装饰 -->
                    <div style="
                        position: absolute;
                        top: -20px;
                        right: -20px;
                        width: 80px;
                        height: 80px;
                        background: rgba(255,255,255,0.1);
                        border-radius: 50%;
                    "></div>
                    
                    <h1 style="
                        margin: 0 0 0.5rem 0;
                        font-size: 3.5rem;
                        font-weight: 800;
                        font-family: {theme.get('font_mono', 'monospace')};
                        color: white;
                        letter-spacing: 0.1em;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    " class="code-display" title="点击选中验证码">{entry['code']}</h1>
                    
                    <p style="
                        margin: 0;
                        color: rgba(255,255,255,0.9);
                        font-size: 1.1rem;
                        font-weight: 500;
                    ">六位安全验证码</p>
                    
                    <!-- 复制提示和统计信息 -->
                    <div style="
                        background: rgba(255,255,255,0.2);
                        border: 1px solid rgba(255,255,255,0.3);
                        border-radius: 8px;
                        padding: 0.7rem 1.2rem;
                        margin-top: 1rem;
                        display: inline-flex;
                        align-items: center;
                        gap: 1rem;
                        cursor: pointer;
                        font-size: 0.9rem;
                        color: white;
                    ">
                        <span>📋 点击上方数字选中复制</span>
                        <div style="
                            background: rgba(255,255,255,0.2);
                            padding: 0.2rem 0.6rem;
                            border-radius: 12px;
                            font-weight: 600;
                        ">共 {entry['count']} 次使用</div>
                    </div>
                </div>
        ''', unsafe_allow_html=True)
        
        # 时间线样式的接收记录
        st.markdown(f'''
                <!-- 接收记录时间线 -->
                <div style="
                    background: #f8f9fa;
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-bottom: 1rem;
                ">
                    <h4 style="
                        margin: 0 0 1rem 0;
                        color: {theme['primary_color']};
                        font-size: 1.1rem;
                        font-weight: 600;
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    ">📅 接收时间记录</h4>
        ''', unsafe_allow_html=True)
        
        # 显示最多前5个时间，如果超过5个则显示"查看更多"
        display_dates = entry['dates'][:5]
        remaining_count = len(entry['dates']) - 5
        
        for i, date in enumerate(display_dates):
            is_latest = (i == 0)
            st.markdown(f'''
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 1rem;
                        padding: 0.8rem;
                        margin-bottom: 0.5rem;
                        background: {"linear-gradient(135deg, #e3f2fd, #ffffff)" if is_latest else "white"};
                        border: 1px solid {theme['border_color']};
                        border-radius: 8px;
                        {"border-left: 4px solid " + theme['primary_color'] if is_latest else ""};
                    ">
                        <div style="
                            width: 8px;
                            height: 8px;
                            background: {theme['primary_color'] if is_latest else theme['text_muted']};
                            border-radius: 50%;
                            flex-shrink: 0;
                        "></div>
                        
                        <div style="flex: 1;">
                            <span style="
                                color: {theme['text_color']};
                                font-weight: {"600" if is_latest else "500"};
                                font-size: 0.95rem;
                            ">{date}</span>
                            {"<span style='margin-left: 0.5rem; background: #4CAF50; color: white; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.7rem;'>最新</span>" if is_latest else ""}
                        </div>
                    </div>
            ''', unsafe_allow_html=True)
        
        if remaining_count > 0:
            st.markdown(f'''
                    <div style="
                        text-align: center;
                        padding: 0.5rem;
                        color: {theme['text_muted']};
                        font-size: 0.9rem;
                    ">还有 {remaining_count} 条记录...</div>
            ''')
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 邮件内容展开器 - 简化显示
        with st.expander(f"📧 查看邮件内容 ({len(entry['emails'])} 封)", expanded=False):
            for i, email in enumerate(entry['emails']):
                # 只显示邮件内容，去掉复杂的头部
                content = email.get('content', '未找到邮件内容')
                
                st.markdown(f'''
                <div style="
                    background: white;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 0.9rem;
                    line-height: 1.6;
                    color: {theme['text_color']};
                ">
                    <div style="
                        font-size: 0.8rem;
                        color: {theme['text_muted']};
                        margin-bottom: 0.5rem;
                        padding-bottom: 0.5rem;
                        border-bottom: 1px solid #f0f0f0;
                    ">{email.get('date_str', '未知时间')}</div>
                    
                    <pre style="
                        background: #f8f9fa;
                        padding: 1rem;
                        border-radius: 6px;
                        overflow-x: auto;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 0.85rem;
                        line-height: 1.4;
                        color: #333;
                        border: 1px solid #e9ecef;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        margin: 0;
                    "><code>{content}</code></pre>
                </div>
                ''', unsafe_allow_html=True)
        
        # 关闭主卡片
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def run(self):
        """运行应用"""
        # 渲染头部
        self._render_header()
        
        # 渲染侧边栏并获取用户操作
        refresh_clicked, max_results = self._render_sidebar()
        
        # 初始化Gmail服务
        if not self._initialize_gmail_service():
            st.markdown(f'''
            <div class="metric-card" style="background: linear-gradient(135deg, {Config.THEME['accent_red']}, #dc3545); color: white; padding: 2rem; text-align: center;">
                <h2 style="margin: 0 0 1rem 0;">⚠️ 无法连接到Gmail服务</h2>
                <p style="margin: 0; opacity: 0.9;">请检查以下设置以解决问题</p>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown(f'''
            <div class="metric-card" style="margin-top: 1rem;">
                <h3 style="color: {Config.THEME['primary_color']}; margin: 0 0 1rem 0;">🔧 解决步骤：</h3>
                
                <div style="background: {Config.THEME['background_color']}; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h4 style="color: {Config.THEME['accent_blue']}; margin: 0 0 0.5rem 0;">📁 1. 检查文件</h4>
                    <p style="margin: 0; color: {Config.THEME['text_color']};">确保 <code>config/credentials.json</code> 文件存在且有效</p>
                </div>
                
                <div style="background: {Config.THEME['background_color']}; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h4 style="color: {Config.THEME['accent_green']}; margin: 0 0 0.5rem 0;">🌐 2. 检查网络</h4>
                    <p style="margin: 0; color: {Config.THEME['text_color']};">确认网络连接正常，可以访问Google服务</p>
                </div>
                
                <div style="background: {Config.THEME['background_color']}; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h4 style="color: {Config.THEME['accent_yellow']}; margin: 0 0 0.5rem 0; color: #333;">🔑 3. API权限</h4>
                    <p style="margin: 0; color: {Config.THEME['text_color']};">确认Google API权限设置正确</p>
                </div>
                
                <hr style="margin: 1.5rem 0; border-color: {Config.THEME['border_color']};">
                
                <h3 style="color: {Config.THEME['primary_color']}; margin: 0 0 1rem 0;">🚀 首次使用设置：</h3>
                
                <ol style="color: {Config.THEME['text_color']}; margin: 0; padding-left: 1.5rem;">
                    <li style="margin: 0.5rem 0;">在Google Cloud Console创建项目</li>
                    <li style="margin: 0.5rem 0;">启用Gmail API</li>
                    <li style="margin: 0.5rem 0;">下载credentials.json文件到config目录</li>
                    <li style="margin: 0.5rem 0;">重新启动应用程序</li>
                </ol>
            </div>
            ''', unsafe_allow_html=True)
            return
        
        # 处理刷新操作
        if refresh_clicked:
            with st.spinner("🔄 正在获取邮件..."):
                st.session_state.emails = self._fetch_emails(max_results)
                st.session_state.last_refresh = datetime.now().strftime('%H:%M:%S')
            
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, {Config.THEME['accent_green']}, #28a745); color: white; border-radius: 12px; padding: 1rem; margin: 1rem 0; text-align: center;">
                <h4 style="margin: 0;">✅ 成功获取 {len(st.session_state.emails)} 封邮件</h4>
            </div>
            ''', unsafe_allow_html=True)
        
        # 初始加载
        if not st.session_state.emails and not refresh_clicked:
            with st.spinner("📥 正在加载初始数据..."):
                st.session_state.emails = self._fetch_emails(max_results)
                if st.session_state.emails:
                    st.session_state.last_refresh = datetime.now().strftime('%H:%M:%S')
        
        # 渲染邮件列表
        self._render_email_list(st.session_state.emails)

def main():
    """主函数"""
    app = MicrosoftCodeApp()
    app.run()

if __name__ == "__main__":
    main()