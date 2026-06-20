"""
复习智库面板 — Gemini 风格
错题本 / 闪卡集 / 诊断报告 / 学习航线 / 速查摘要 / 统计
"""
import streamlit as st
from ui.components import render_flashcard, render_stats_bar
from ui.styles import THEME

t = THEME


def render_vault_panel(vault):
    """渲染复习智库面板（Gemini 圆角卡片风格）"""
    st.markdown("### 🧠 复习智库")
    st.caption("你的错题本、闪卡、诊断报告和学习航线")

    # 统计条
    stats = vault.get_stats()
    render_stats_bar(stats)

    st.divider()

    # Tab 子面板
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["❌ 错题本", "🃏 闪卡集", "📊 诊断报告", "🧭 学习航线", "⚡ 速查摘要"]
    )

    # ── Tab 1: 错题本 ──
    with tab1:
        wrong_answers = vault.get_wrong_answers()
        if not wrong_answers:
            st.info("还没有错题记录。在做测验时答错的题目会自动收录到这里。")
        for wa in wrong_answers:
            with st.expander(f"Q{wa['id']}: {wa['question'][:60]}... （已复习 {wa['review_count']} 次）"):
                st.markdown(f"**题目**：{wa['question']}")
                st.markdown(f"**你的答案**：{wa['student_answer']}")
                st.markdown(f"**正确答案**：{wa['correct_answer']}")
                st.caption(f"📖 {wa['explanation']}")
                st.caption(f"🏷️ {wa['topic']} | 添加于 {wa['added_at']}")
                if st.button("✅ 已复习（+1）", key=f"review_wa_{wa['id']}"):
                    vault.mark_reviewed(wa["id"])
                    st.rerun()

    # ── Tab 2: 闪卡集 ──
    with tab2:
        cards = vault.get_flashcards()
        if not cards:
            st.info("还没有闪卡。在聊天中让 AI 帮你生成吧！")
        for i, card in enumerate(reversed(cards)):
            render_flashcard(card, i)

    # ── Tab 3: 诊断报告 ──
    with tab3:
        latest = vault.get_latest_diagnosis()
        if not latest:
            st.info("还没有诊断报告。在聊天中发送「分析我的薄弱点」来生成第一份报告。")
        else:
            st.caption(f"📅 {latest.get('created_at', '')}")
            data = latest.get("data", {})
            st.markdown(f"**📊 整体评估**：{data.get('overall_assessment', '')}")

            st.markdown("**🟡 薄弱知识点**")
            for wp in data.get("weak_points", []):
                st.markdown(f"- {wp['topic']} — {wp.get('evidence', '')}")

            st.markdown("**🟢 已掌握**")
            for sp in data.get("strong_points", []):
                st.markdown(f"- {sp['topic']}")

            st.markdown("**🔴 知识盲区**")
            for gp in data.get("gaps", []):
                st.markdown(f"- {gp['topic']} — {gp.get('suggestion', '')}")

    # ── Tab 4: 学习航线 ──
    with tab4:
        path = vault.get_latest_path()
        if not path:
            st.info("还没有学习航线。它会随诊断报告一起自动生成。")
        else:
            st.caption(f"📅 {path.get('created_at', '')}")
            st.markdown(path.get("content", ""))

    # ── Tab 5: 速查摘要 ──
    with tab5:
        summaries = vault._data.get("quick_summaries", [])
        if not summaries:
            st.info("还没有速查摘要。在聊天中发送「帮我总结知识库重点」来生成。")
        for s in reversed(summaries):
            with st.expander(f"⚡ {s.get('kb_name', '')} — {s.get('created_at', '')}"):
                data = s.get("data", {})
                for key, val in data.items():
                    if isinstance(val, list):
                        st.markdown(f"**{key}**")
                        for v in val:
                            st.markdown(f"- {v}")
                    else:
                        st.markdown(f"**{key}**：{val}")
