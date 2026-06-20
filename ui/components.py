"""
沈航智学 AeroTutor — Gemini 风格 Generative UI 组件
欢迎页 · 建议 Chip · 测验卡片 · 翻转闪卡 · 知识播客 · 速查摘要 · 学习航线 · 统计条
"""
import streamlit as st
from ui.styles import THEME

t = THEME


# ════════════════════════════════════════════
# 欢迎页（Gemini 风格星火渐变大标题）
# ════════════════════════════════════════════
def render_welcome_screen():
    """Gemini 风格欢迎页：居中的星火渐变大标题 + 副标题"""
    st.markdown(f"""
    <div class="welcome-container">
        <div class="welcome-sparkle-icon">✨</div>
        <h1 class="welcome-title">沈航智学 AeroTutor</h1>
        <p class="welcome-subtitle">
            多知识库隔离 · 自适应学习助教<br>
            用 AI 辅助你的航空航天课程学习
        </p>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════
# 建议问题 Chip（可点击药丸按钮）
# ════════════════════════════════════════════
def render_suggestion_chips(suggestions: list[tuple[str, str]]) -> str | None:
    """
    渲染建议问题 Chip 行。
    suggestions: [(显示文本, 实际query), ...]
    返回被点击的 query，无点击返回 None。
    """
    st.markdown('<div class="suggestion-chips">', unsafe_allow_html=True)

    clicked = None
    cols = st.columns(len(suggestions))
    for i, (label, query) in enumerate(suggestions):
        with cols[i]:
            if st.button(label, key=f"suggest_{i}", use_container_width=True):
                clicked = query

    st.markdown('</div>', unsafe_allow_html=True)
    return clicked


# ════════════════════════════════════════════
# 答案溯源标签
# ════════════════════════════════════════════
def render_source_tags(sources: list[dict]):
    if not sources:
        return
    tags = "".join(
        f'<span class="source-tag">📄 {s["kb_name"]} · {s["file_name"]}</span>'
        for s in sources[:6]
    )
    st.markdown(f'<div style="margin:0.5rem 0;">{tags}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════
# 测验卡片
# ════════════════════════════════════════════
def render_quiz_card(quiz_data: dict, quiz_key: str = "", vault=None,
                     llm_config: dict = None):
    """交互式测验卡片（Gemini 圆角卡片风格）。传入 vault 可自动收录错题，传入 llm_config 用于 AI 批改。"""
    if not quiz_data or not quiz_data.get("questions"):
        return

    st.markdown(f"### 📝 {quiz_data.get('title', '知识测验')}")

    # 防止重复保存错题
    if "saved_wrong_qids" not in st.session_state:
        st.session_state.saved_wrong_qids = set()

    for i, q in enumerate(quiz_data["questions"]):
        qid = f"{quiz_key}_q{i}"
        save_key = f"{quiz_key}_{i}"
        st.markdown(f"""
        <div class="quiz-card">
            <div class="q-title">第{i+1}题 · {q.get('topic', '')} · {q.get('difficulty', '').upper()}</div>
            <div class="q-text">{q['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        if q["type"] == "choice":
            options = q.get("options", [])
            user_answer = st.radio(
                "你的答案",
                options,
                key=qid,
                index=None,
                format_func=lambda x: x,
            )
            if user_answer:
                correct_letter = q["answer"].strip().upper()
                user_letter = user_answer[0].upper() if user_answer else ""
                if user_letter == correct_letter:
                    st.success(f"✅ 正确！{q.get('explanation', '')}")
                else:
                    st.error(f"❌ 正确答案是 {correct_letter}。{q.get('explanation', '')}")
                    # 自动收录错题
                    if vault and save_key not in st.session_state.saved_wrong_qids:
                        vault.add_wrong_answer(
                            question=q["question"],
                            student_answer=user_answer,
                            correct_answer=q["answer"],
                            topic=q.get("topic", ""),
                            explanation=q.get("explanation", ""),
                        )
                        st.session_state.saved_wrong_qids.add(save_key)
        else:
            user_answer = st.text_area("你的答案", key=qid, placeholder="输入你的回答...",
                                       height=100)
            if user_answer:
                col_ref, col_grade = st.columns([1, 1])
                with col_ref:
                    with st.expander("📋 查看参考答案"):
                        st.info(q.get("answer", "无参考答案"))
                        st.caption(q.get("explanation", ""))
                with col_grade:
                    if st.button("✍️ AI 批改", key=f"grade_{qid}", use_container_width=True):
                        with st.spinner("AI 批改中..."):
                            grade_result = _auto_grade(q["question"], q.get("answer", ""), user_answer, llm_config)
                            if grade_result:
                                total = grade_result.get("total_score", 0)
                                max_s = grade_result.get("max_score", 20)
                                pct = total / max_s * 100 if max_s else 0
                                color = "#0d904f" if pct >= 80 else ("#e37400" if pct >= 50 else "#d93025")
                                st.markdown(f"### 得分：<span style='color:{color}'>{total}/{max_s}</span>", unsafe_allow_html=True)
                                for pt in grade_result.get("points", []):
                                    icon = "✅" if pt.get("score", 0) >= pt.get("max", 1) else "⚠️"
                                    st.caption(f"{icon} {pt.get('content', '')} — {pt.get('comment', '')}（{pt.get('score', 0)}/{pt.get('max', 1)}）")
                                st.info(grade_result.get("feedback", ""))
                                # 得分低于 60% 自动收录错题
                                if vault and pct < 60 and save_key not in st.session_state.saved_wrong_qids:
                                    vault.add_wrong_answer(
                                        question=q["question"],
                                        student_answer=user_answer,
                                        correct_answer=q.get("answer", ""),
                                        topic=q.get("topic", ""),
                                        explanation=grade_result.get("feedback", q.get("explanation", "")),
                                    )
                                    st.session_state.saved_wrong_qids.add(save_key)
                            else:
                                st.warning("批改服务暂时不可用，请参考标准答案自评。")
        st.divider()


# ════════════════════════════════════════════
# 2D 翻转闪卡
# ════════════════════════════════════════════
def render_flashcard(card: dict, idx: int, on_review=None):
    """纯 CSS 翻转闪卡"""
    flip_id = f"flip_{idx}"
    topic = card.get('topic', '')
    front = card.get('front', '')
    back = card.get('back', '')
    st.markdown(f"""
    <div class="flashcard">
        <input type="checkbox" id="{flip_id}" class="flashcard-check">
        <label for="{flip_id}">
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <div class="card-topic">{topic}</div>
                    <div class="card-title">{front}</div>
                    <div class="card-flip-hint">点击翻转</div>
                </div>
                <div class="flashcard-back">
                    <div class="card-explain">{back}</div>
                </div>
            </div>
        </label>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════
# 知识播客
# ════════════════════════════════════════════
def render_podcast(script: str):
    """双人对话播客卡片（Gemini 圆角 + 左侧色条）"""
    if not script:
        return
    lines = script.strip().split("\n")
    st.markdown("### 🎙️ 知识播客")
    html = '<div class="podcast-card">'
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "王教授" in line or "👨‍🏫" in line:
            html += f'<p class="teacher">{line}</p>'
        elif "小明" in line or "🧑‍🎓" in line:
            html += f'<p class="student">{line}</p>'
        else:
            html += f'<p style="color:{t["text_secondary"]};font-style:italic;">{line}</p>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ════════════════════════════════════════════
# 速查摘要
# ════════════════════════════════════════════
def render_quick_summary(summary: dict, kb_name: str = ""):
    """速查摘要（Chip 标签组 + 建议）"""
    if not summary:
        return
    st.markdown(f"### ⚡ {kb_name or ''} 速查摘要")

    core = summary.get("core_concepts", [])
    if core:
        st.markdown("**🔑 核心概念**")
        for c in core:
            st.markdown(f"- {c}")

    formulas = summary.get("key_formulas", [])
    if formulas:
        st.markdown("**📐 必会公式**")
        for f in formulas:
            st.markdown(f"- `{f}`")

    mistakes = summary.get("common_mistakes", [])
    if mistakes:
        st.markdown("**⚠️ 常见误区**")
        for m in mistakes:
            st.markdown(f"- ❌ {m}")

    review = summary.get("suggested_review", "")
    if review:
        st.info(f"💡 {review}")


# ════════════════════════════════════════════
# 学习航线
# ════════════════════════════════════════════
def render_learning_path(path_text: str):
    """学习航线时间线（左侧色条卡片）"""
    if not path_text:
        return
    st.markdown(f'<div class="path-card">{path_text}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════
# 学习统计条
# ════════════════════════════════════════════
def render_stats_bar(stats: dict):
    """Gemini 风格统计条"""
    items = [
        ("🔥 连续复习", str(stats.get("streak_days", 0)), "天"),
        ("📝 完成测验", str(stats.get("total_quizzes", 0)), "次"),
        ("🃏 复习闪卡", str(stats.get("total_cards_reviewed", 0)), "次"),
        ("❌ 错题本", str(stats.get("wrong_count", 0)), "道"),
        ("📊 诊断报告", str(stats.get("diagnosis_count", 0)), "次"),
    ]
    html = '<div class="stats-bar">'
    for label, num, unit in items:
        html += f"""
        <div class="stats-item">
            <div class="stat-num">{num}<span style="font-size:0.8rem;color:{t['text_secondary']};">{unit}</span></div>
            <div class="stat-label">{label}</div>
        </div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ════════════════════════════════════════════
# 自动批改（动态 LLM 配置）
# ════════════════════════════════════════════
def _get_grader_llm(llm_config: dict):
    """获取批改专用的 LLM 实例（temperature=0 确保评分一致）"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        base_url=llm_config.get("base_url", ""),
        api_key=llm_config.get("api_key", ""),
        model=llm_config.get("model", ""),
        temperature=0.0,
        max_tokens=512,
        timeout=30,
    )


def _auto_grade(question: str, reference_answer: str, student_answer: str,
                llm_config: dict = None) -> dict:
    """对简答题进行 AI 批改"""
    from modules.quiz_engine import QuizEngine
    from config import LLM_CONFIG
    try:
        cfg = llm_config or LLM_CONFIG
        llm = _get_grader_llm(cfg)
        engine = QuizEngine(llm)
        return engine.grade_answer(question, reference_answer, student_answer)
    except Exception:
        return {}
