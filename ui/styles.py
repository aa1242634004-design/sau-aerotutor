"""
沈航智学 AeroTutor — Gemini 风格浅色主题
极简 · 大圆角 · 渐变品牌色 · 悬浮侧边栏
"""

THEME = {
    "bg_primary": "#f8fafd",
    "bg_secondary": "#ffffff",
    "bg_surface": "#f1f4f9",
    "bg_hover": "#e8edf4",
    "text_primary": "#1f1f1f",
    "text_secondary": "#5f6368",
    "text_tertiary": "#80868b",
    "accent_blue": "#4285f4",
    "accent_purple": "#9b59b6",
    "accent_pink": "#f06292",
    "gradient_sparkle": "linear-gradient(135deg, #4285f4 0%, #7c4dff 35%, #e040fb 65%, #ff6e40 100%)",
    "user_bubble_bg": "#e8f0fe",
    "user_bubble_text": "#1f1f1f",
    "ai_bubble_bg": "#ffffff",
    "ai_bubble_text": "#1f1f1f",
    "ai_bubble_border": "rgba(0,0,0,0.06)",
    "input_bg": "#ffffff",
    "input_border": "rgba(0,0,0,0.1)",
    "input_focus_shadow": "rgba(66,133,244,0.25)",
    "chip_bg": "#f1f4f9",
    "chip_hover_bg": "#e4e9f2",
    "chip_text": "#1f1f1f",
    "code_bg": "#1e1e1e",
    "code_text": "#e0e0e0",
    "sidebar_bg": "#f1f4f9",
    "sidebar_hover": "#e4e9f2",
    "sidebar_text": "#1f1f1f",
    "divider": "rgba(0,0,0,0.06)",
    "success": "#0d904f",
    "warning": "#e37400",
    "danger": "#d93025",
    "quiz_card_bg": "#f8fafd",
    "quiz_card_border": "rgba(0,0,0,0.08)",
    "shadow_sm": "0 1px 3px rgba(0,0,0,0.06)",
    "shadow_md": "0 2px 8px rgba(0,0,0,0.08)",
}


def get_css() -> str:
    """生成 CSS"""
    t = THEME
    return f"""<style>
/* ═══════════════ 全局背景 & 字体 ═══════════════ */
.stApp {{
    background: {t['bg_primary']} !important;
    font-family: 'Inter', 'Segoe UI', 'Roboto', -apple-system, sans-serif !important;
}}
.main .block-container {{
    padding: 0 1.5rem 5rem 1.5rem !important;
    max-width: 820px !important;
    margin: 0 auto !important;
}}

/* ═══════════════ 全局文字 ═══════════════ */
.stMarkdown p, .stMarkdown li, .stMarkdown span {{
    color: {t['text_primary']} !important;
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
}}
.stMarkdown strong, .stMarkdown b {{
    color: {t['text_primary']} !important;
    font-weight: 600 !important;
}}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {{
    color: {t['text_primary']} !important;
    font-weight: 600 !important;
}}
.stMarkdown code:not(pre code) {{
    color: {t['text_primary']} !important;
    background: {t['bg_surface']} !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
}}
.stMarkdown a {{
    color: {t['accent_blue']} !important;
    text-decoration: none !important;
}}
.stMarkdown blockquote {{
    border-left: 3px solid {t['accent_blue']} !important;
    background: rgba(66,133,244,0.06) !important;
    padding: 0.5rem 1rem !important;
    border-radius: 0 8px 8px 0 !important;
}}
.stMarkdown table {{
    border-collapse: collapse !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid {t['divider']} !important;
}}
.stMarkdown th {{
    background: {t['bg_surface']} !important;
    padding: 10px 14px !important;
    text-align: left !important;
}}
.stMarkdown td {{
    padding: 8px 14px !important;
    border-bottom: 1px solid {t['divider']} !important;
}}

/* ═══════════════ 代码块 ═══════════════ */
.stMarkdown pre {{
    background: {t['code_bg']} !important;
    border-radius: 14px !important;
    padding: 1rem 1.2rem !important;
    margin: 0.8rem 0 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}}
.stMarkdown pre code {{
    color: {t['code_text']} !important;
    background: transparent !important;
    font-size: 0.85rem !important;
    line-height: 1.65 !important;
}}

/* ═══════════════ 侧边栏 + 悬浮自动展开 ═══════════════ */
section[data-testid="stSidebar"] {{
    background: {t['sidebar_bg']} !important;
    width: 56px !important;
    min-width: 56px !important;
    max-width: 56px !important;
    overflow: visible !important;
    transition: width 0.3s ease, min-width 0.3s ease, max-width 0.3s ease !important;
    border-right: 1px solid {t['divider']} !important;
}}
section[data-testid="stSidebar"]:hover,
section[data-testid="stSidebar"]:focus-within,
section[data-testid="stSidebar"].sb-expanded {{
    width: 320px !important;
    min-width: 320px !important;
    max-width: 320px !important;
    box-shadow: 4px 0 28px rgba(0,0,0,0.12) !important;
}}
/* 收起时：所有内容元素不可见 */
section[data-testid="stSidebar"] > div > div > div {{
    opacity: 0 !important;
    visibility: hidden !important;
    transition: opacity 0.2s ease, visibility 0.2s ease !important;
}}
/* 展开时：恢复可见 */
section[data-testid="stSidebar"]:hover > div > div > div,
section[data-testid="stSidebar"]:focus-within > div > div > div,
section[data-testid="stSidebar"].sb-expanded > div > div > div {{
    opacity: 1 !important;
    visibility: visible !important;
}}
/* 按钮通用样式 */
section[data-testid="stSidebar"] .stButton > button {{
    background: {t['bg_hover']} !important;
    color: {t['text_primary']} !important;
    border: none !important;
    border-radius: 22px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    padding: 0.45rem 1rem !important;
    transition: all 0.2s !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: {t['bg_surface']} !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}}
/* 分割线 */
section[data-testid="stSidebar"] hr {{
    margin: 0.5rem 0 !important;
}}

/* ═══════════════ 欢迎页 ═══════════════ */
.welcome-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
    text-align: center;
    padding: 2rem;
    animation: fadeSlideIn 0.6s ease-out;
}}
.welcome-sparkle-icon {{
    font-size: 2.8rem;
    margin-bottom: 1rem;
    animation: sparkle 3s ease-in-out infinite;
}}
.welcome-title {{
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 0.5rem !important;
    background: {t['gradient_sparkle']} !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}}
.welcome-subtitle {{
    font-size: 1rem !important;
    color: {t['text_secondary']} !important;
    margin-bottom: 2rem !important;
    max-width: 480px !important;
    line-height: 1.6 !important;
}}

/* ═══════════════ 建议 Chip ═══════════════ */
.suggestion-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    justify-content: center;
    max-width: 580px;
    margin: 0 auto;
}}

/* ═══════════════ 对话气泡 ═══════════════ */
[data-testid="stChatMessage"] {{
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0.3rem 0 !important;
}}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) > div:last-child {{
    background: {t['user_bubble_bg']} !important;
    color: {t['user_bubble_text']} !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 0.7rem 1.2rem !important;
    max-width: 75% !important;
    box-shadow: {t['shadow_sm']} !important;
}}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) > div:last-child {{
    background: {t['ai_bubble_bg']} !important;
    color: {t['ai_bubble_text']} !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 0.7rem 1.2rem !important;
    max-width: 85% !important;
    border: 1px solid {t['ai_bubble_border']} !important;
    box-shadow: {t['shadow_sm']} !important;
}}

/* ═══════════════ 底部输入 ═══════════════ */
.stChatInput textarea {{
    background: {t['input_bg']} !important;
    color: {t['text_primary']} !important;
    border: 1px solid {t['input_border']} !important;
    border-radius: 28px !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 1rem !important;
    min-height: 48px !important;
    outline: none !important;
    box-shadow: {t['shadow_md']} !important;
}}
.stChatInput textarea:focus {{
    border-color: {t['accent_blue']} !important;
    box-shadow: 0 0 0 3px {t['input_focus_shadow']}, {t['shadow_md']} !important;
}}
.stChatInput textarea::placeholder {{
    color: {t['text_tertiary']} !important;
}}

/* ═══════════════ 按钮 ═══════════════ */
.stButton > button {{
    background: {t['bg_surface']} !important;
    color: {t['text_primary']} !important;
    border: 1px solid {t['divider']} !important;
    border-radius: 24px !important;
    font-weight: 500 !important;
    font-size: 0.83rem !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.2s ease !important;
}}
.stButton > button:hover {{
    background: {t['bg_hover']} !important;
    border-color: {t['accent_blue']}44 !important;
}}

/* ═══════════════ Expander ═══════════════ */
.stExpander {{
    background: transparent !important;
    border: 1px solid {t['divider']} !important;
    border-radius: 14px !important;
    margin: 0.4rem 0 !important;
}}
.stExpander summary {{
    color: {t['text_primary']} !important;
    font-weight: 500 !important;
}}

/* ═══════════════ 输入框 ═══════════════ */
.stTextInput input, .stTextArea textarea {{
    color: {t['text_primary']} !important;
    background: {t['input_bg']} !important;
    border: 1px solid {t['input_border']} !important;
    border-radius: 14px !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {t['accent_blue']} !important;
    box-shadow: 0 0 0 3px {t['input_focus_shadow']} !important;
}}

/* ═══════════════ 文件上传 ═══════════════ */
.stFileUploader section {{
    background: {t['bg_surface']} !important;
    border: 1px dashed {t['accent_blue']}44 !important;
    border-radius: 14px !important;
}}

/* ═══════════════ Alert ═══════════════ */
.stAlert {{
    border-radius: 14px !important;
    background: {t['bg_secondary']} !important;
    border: 1px solid {t['divider']} !important;
}}

/* ═══════════════ Divider ═══════════════ */
hr, .stDivider {{
    border-color: {t['divider']} !important;
}}

/* ═══════════════ 测验卡片 ═══════════════ */
.quiz-card {{
    background: {t['quiz_card_bg']};
    border: 1px solid {t['quiz_card_border']};
    border-radius: 16px;
    padding: 1.2rem;
    margin: 0.6rem 0;
    box-shadow: {t['shadow_sm']};
}}
.quiz-card .q-title {{
    color: {t['accent_blue']};
    font-weight: 600;
    font-size: 0.82rem;
    margin-bottom: 0.5rem;
}}
.quiz-card .q-text {{
    color: {t['text_primary']};
    font-size: 1rem;
    font-weight: 500;
    line-height: 1.6;
}}
.source-tag {{
    display: inline-block;
    padding: 3px 12px;
    border-radius: 16px;
    font-size: 0.75rem;
    background: {t['chip_bg']};
    color: {t['text_secondary']};
    margin: 3px;
    border: 1px solid {t['divider']};
}}

/* ═══════════════ 翻转闪卡 ═══════════════ */
.flashcard {{
    width: 100%;
    height: 220px;
    perspective: 1000px;
    margin: 0.8rem 0;
}}
.flashcard-check {{
    display: none !important;
}}
.flashcard label {{
    display: block;
    cursor: pointer;
    width: 100%;
    height: 100%;
}}
.flashcard-inner {{
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.6s cubic-bezier(0.4,0,0.2,1);
    transform-style: preserve-3d;
}}
.flashcard-check:checked + label .flashcard-inner {{
    transform: rotateY(180deg);
}}
.flashcard-front, .flashcard-back {{
    position: absolute;
    inset: 0;
    backface-visibility: hidden;
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1.8rem;
    box-sizing: border-box;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}
.flashcard-front {{
    background: linear-gradient(135deg, #ffffff, #f8fafd);
    border: 1.5px solid rgba(66,133,244,0.2);
}}
.flashcard-back {{
    background: linear-gradient(135deg, #f8fafd, #faf5ff);
    border: 1.5px solid rgba(156,39,176,0.2);
    transform: rotateY(180deg);
}}
.flashcard-front .card-topic {{
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: {t['accent_blue']};
    margin-bottom: 0.8rem;
}}
.flashcard-front .card-title {{
    font-size: 1.3rem;
    font-weight: 700;
    color: {t['text_primary']};
    line-height: 1.4;
}}
.flashcard-front .card-flip-hint {{
    font-size: 0.7rem;
    color: {t['text_tertiary']};
    margin-top: 1.2rem;
    opacity: 0.6;
}}
.flashcard-back .card-explain {{
    font-size: 0.95rem;
    line-height: 1.75;
    color: {t['text_primary']};
    text-align: left;
    width: 100%;
}}

/* ═══════════════ 播客 / 航线卡片 ═══════════════ */
.podcast-card {{
    background: {t['bg_secondary']};
    border-radius: 16px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    border-left: 4px solid {t['accent_purple']};
    box-shadow: {t['shadow_sm']};
}}
.podcast-card p {{
    color: {t['text_primary']} !important;
    margin: 0.3rem 0;
    line-height: 1.7;
}}
.podcast-card .teacher {{
    color: {t['accent_blue']} !important;
    font-weight: 600;
}}
.podcast-card .student {{
    color: {t['accent_purple']} !important;
    font-weight: 600;
}}
.path-card {{
    background: {t['bg_secondary']};
    border-radius: 16px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    border-left: 4px solid {t['accent_blue']};
    line-height: 1.7;
    box-shadow: {t['shadow_sm']};
}}
.path-card p, .path-card li, .path-card strong {{
    color: {t['text_primary']} !important;
}}

/* ═══════════════ 统计条 ═══════════════ */
.stats-bar {{
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    margin: 0.5rem 0;
}}
.stats-item {{
    background: {t['bg_secondary']};
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
    text-align: center;
    min-width: 60px;
    flex: 1;
    border: 1px solid {t['divider']};
}}
.stats-item .stat-num {{
    font-size: 1.3rem;
    font-weight: 700;
    color: {t['accent_blue']};
}}
.stats-item .stat-label {{
    font-size: 0.68rem;
    color: {t['text_secondary']};
    margin-top: 0.15rem;
    font-weight: 500;
}}

/* ═══════════════ 动效 ═══════════════ */
@keyframes fadeSlideIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes sparkle {{
    0%, 100% {{ opacity: 0.6; transform: scale(1); }}
    50% {{ opacity: 1; transform: scale(1.08); }}
}}
.streaming-cursor::after {{
    content: '|';
    animation: blinkCursor 0.8s infinite;
    color: {t['accent_blue']};
}}
@keyframes blinkCursor {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0; }}
}}

/* ═══════════════ 响应式 ═══════════════ */
@media (max-width: 768px) {{
    .main .block-container {{
        padding: 0 0.8rem 5rem 0.8rem !important;
    }}
    .welcome-title {{
        font-size: 1.6rem !important;
    }}
    .flashcard {{
        height: 170px;
    }}
}}
</style>"""
