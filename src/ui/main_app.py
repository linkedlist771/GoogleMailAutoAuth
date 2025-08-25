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
            # 侧边栏标题
            st.markdown(f'''
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="color: {Config.THEME['primary_color']}; margin: 0;">
                    {Config.APP_ICON} 设置
                </h2>
            </div>
            ''', unsafe_allow_html=True)
            
            # 邮件数量设置
            st.markdown("📮 **邮件获取设置**")
            max_results = st.number_input(
                "获取邮件数量",
                min_value=1,
                max_value=100,
                value=Config.DEFAULT_MAX_RESULTS,
                step=5,
                help="设置一次获取的最大邮件数量"
            )
            
            st.markdown("")
            
            # 刷新按钮
            refresh_clicked = st.button("🔄 刷新邮件", use_container_width=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # 服务状态
            st.markdown(f"📊 **服务状态**")
            
            if st.session_state.gmail_service:
                st.markdown(f'''
                <div class="metric-card" style="background: linear-gradient(135deg, {Config.THEME['accent_green']}, #28a745); color: white;">
                    <h4 style="margin: 0;">✅ Gmail服务已连接</h4>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="metric-card" style="background: linear-gradient(135deg, {Config.THEME['accent_red']}, #dc3545); color: white;">
                    <h4 style="margin: 0;">❌ Gmail服务未连接</h4>
                </div>
                ''', unsafe_allow_html=True)
            
            # 最后刷新时间
            if st.session_state.last_refresh:
                st.markdown(f'''
                <div class="metric-card">
                    <p style="margin: 0; color: {Config.THEME['text_muted']};"><strong>上次刷新:</strong></p>
                    <h4 style="margin: 0; color: {Config.THEME['primary_color']};">{st.session_state.last_refresh}</h4>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # 关于信息
            st.markdown(f"ℹ️ **关于**")
            st.markdown(f'''
            <div class="metric-card">
                <p style="margin: 0.5rem 0; color: {Config.THEME['text_color']};"><strong>版本:</strong> {Config.VERSION}</p>
                <p style="margin: 0.5rem 0; color: {Config.THEME['text_muted']};">专注于Microsoft验证码管理</p>
                <p style="margin: 0.5rem 0; color: {Config.THEME['text_muted']};">安全、高效、易用</p>
            </div>
            ''', unsafe_allow_html=True)
            
            return refresh_clicked, max_results
    
    def _render_email_list(self, emails: List[Dict]):
        """渲染邮件列表"""
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
        
        # 显示验证码卡片
        for i, entry in enumerate(processed_codes):
            self._render_code_card(entry, i)
    
    def _render_code_card(self, entry: Dict, index: int):
        """渲染单个验证码卡片"""
        theme = Config.THEME
        
        # 选择渐变色彩
        gradients = [
            f"linear-gradient(135deg, {theme['accent_blue']}, {theme['primary_color']})",
            f"linear-gradient(135deg, {theme['accent_green']}, #20c997)",
            f"linear-gradient(135deg, {theme['gradient_start']}, {theme['gradient_end']})",
            f"linear-gradient(135deg, #ff6b6b, #ee5a24)",
            f"linear-gradient(135deg, #a55eea, #8854d0)",
        ]
        gradient = gradients[index % len(gradients)]
        
        # 主卡片容器
        st.markdown(f'''
        <div class="code-main-card" style="
            background: {theme['card_background']};
            border-radius: 20px;
            padding: 0;
            margin: 1.5rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid {theme['border_color']};
            overflow: hidden;
            transition: all 0.3s ease;
        ">
            <!-- 头部渐变背景 -->
            <div style="
                background: {gradient};
                padding: 2rem;
                color: white;
                position: relative;
                overflow: hidden;
            ">
                <!-- 装饰元素 -->
                <div style="
                    position: absolute;
                    top: -50px;
                    right: -50px;
                    width: 100px;
                    height: 100px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 50%;
                "></div>
                <div style="
                    position: absolute;
                    bottom: -30px;
                    left: -30px;
                    width: 60px;
                    height: 60px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 50%;
                "></div>
                
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h2 style="margin: 0; font-size: 3.5rem; font-weight: 700; font-family: {theme['font_mono']}; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{entry['code']}</h2>
                        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">🔍 Microsoft 验证码</p>
                    </div>
                    <div style="text-align: right;">
                        <div style="background: rgba(255,255,255,0.2); border-radius: 50px; padding: 0.5rem 1rem; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.2rem; font-weight: 600;">📊 {entry['count']}</span>
                        </div>
                        <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">接收次数</p>
                    </div>
                </div>
            </div>
            
            <!-- 内容区域 -->
            <div style="padding: 1.5rem;">
        ''', unsafe_allow_html=True)
        
        # 使用列布局显示详细信息
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f'''
            <div style="background: {theme['background_color']}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <h4 style="color: {theme['primary_color']}; margin: 0 0 0.5rem 0; display: flex; align-items: center;">
                    ⏰ 最新时间
                </h4>
                <p style="margin: 0; color: {theme['text_color']}; font-weight: 600;">{entry['latest_date']}</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div style="background: {theme['background_color']}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <h4 style="color: {theme['accent_green']}; margin: 0 0 0.5rem 0; display: flex; align-items: center;">
                    📊 统计信息
                </h4>
                <p style="margin: 0; color: {theme['text_color']}; font-weight: 600;">总计 {entry['count']} 次接收</p>
            </div>
            ''', unsafe_allow_html=True)
        
        # 所有接收时间
        if len(entry['dates']) > 1:
            st.markdown(f'''
            <div style="background: {theme['background_color']}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <h4 style="color: {theme['accent_blue']}; margin: 0 0 1rem 0; display: flex; align-items: center;">
                    📅 所有接收时间
                </h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem;">
            ''', unsafe_allow_html=True)
            
            for date in entry['dates']:
                st.markdown(f'''
                    <div style="background: white; border: 1px solid {theme['border_color']}; border-radius: 8px; padding: 0.5rem; text-align: center;">
                        <span style="color: {theme['text_color']}; font-size: 0.9rem;">{date}</span>
                    </div>
                ''', unsafe_allow_html=True)
            
            st.markdown('</div></div>', unsafe_allow_html=True)
        
        # 邮件详情展开器
        with st.expander(f"📧 查看邮件详情 ({len(entry['emails'])} 封邮件)", expanded=False):
            for i, email in enumerate(entry['emails']):
                st.markdown(f'''
                <div style="background: {theme['card_background']}; border: 1px solid {theme['border_color']}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h4 style="color: {theme['primary_color']}; margin: 0;">邮件 {i+1}</h4>
                        <span style="background: {theme['accent_blue']}; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">
                            {email.get('date_str', '无时间')}
                        </span>
                    </div>
                    
                    <div style="margin-bottom: 0.75rem;">
                        <strong style="color: {theme['text_color']};">主题:</strong>
                        <span style="color: {theme['text_muted']};">{email.get('subject', '无主题')}</span>
                    </div>
                    
                    <div style="margin-bottom: 0.75rem;">
                        <strong style="color: {theme['text_color']};">发件人:</strong>
                        <span style="color: {theme['text_muted']};">{email.get('from', '无发件人')}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                # 显示部分内容
                content = email.get('content', '')[:300]
                if len(email.get('content', '')) > 300:
                    content += "..."
                st.text_area("内容预览:", content, height=120, 
                           key=f"content_{i}_{entry['code']}_{index}")
                
                if i < len(entry['emails']) - 1:
                    st.markdown(f"<hr style='border-color: {theme['border_color']};'>", 
                               unsafe_allow_html=True)
        
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