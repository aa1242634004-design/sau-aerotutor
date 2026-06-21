"""
沈航智学 AeroTutor — Gemini 风格 UI
====================================
Google Gemini 网页版风格：极简 · 大圆角 · 悬浮输入 · 星火渐变
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="沈航智学 AeroTutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto",
)

from config import AGENT_NAME, AGENT_SLOGAN, SCHOOL_NAME, PROVIDER_PRESETS
from modules.kb_manager import KnowledgeBaseManager
from modules.rag_engine import RAGEngine
from modules.chat_agent import ChatAgent
from modules.vault import ReviewVault
from modules.user_settings import UserSettings, PROVIDERS
from ui.styles import get_css, THEME
from ui.sidebar_dnd import build_dnd_html
from ui.kb_panel import render_kb_panel
from ui.vault_panel import render_vault_panel
from ui.components import (
    render_quiz_card, render_flashcard, render_podcast,
    render_quick_summary, render_learning_path, render_source_tags,
    render_stats_bar, render_welcome_screen, render_suggestion_chips,
)
from utils.helpers import safe_json_parse
import json as _json

t = THEME

# ════════════════════════════════════════════
# 对话持久化
# ════════════════════════════════════════════
CONV_FILE = os.path.join(os.path.dirname(__file__), "conversations.json")


# 旧格式：{{conv_id: {title, messages, ...}}}
# 新格式：{{"folders": {...}, "conversations": {...}}}


def _load_conversations() -> dict:
    if os.path.exists(CONV_FILE):
        with open(CONV_FILE, "r", encoding="utf-8") as f:
            data = _json.load(f)
    else:
        data = {}
    # 兼容旧格式：无 folders 键则升级
    if "folders" not in data:
        data = {"folders": {}, "conversations": data}
    return data


def _save_conversations(data: dict):
    with open(CONV_FILE, "w", encoding="utf-8") as f:
        _json.dump(data, f, ensure_ascii=False, indent=2)


def _convs() -> dict:
    """获取 conversations 子字典"""
    return st.session_state.conversations.setdefault("conversations", {})


def _folders() -> dict:
    """获取 folders 子字典"""
    return st.session_state.conversations.setdefault("folders", {})


def _conv_title(msgs: list) -> str:
    """取第一条用户消息作为对话标题"""
    for m in msgs:
        if m.get("role") == "user":
            t = m["content"].strip()[:30]
            return t if len(m["content"]) <= 30 else t + "..."
    return "新对话"


def _create_folder(name: str, parent_id: str = "") -> str:
    import uuid as _uuid
    fid = _uuid.uuid4().hex[:8]
    _folders()[fid] = {"name": name.strip()[:20], "parent_id": parent_id, "created_at": time.strftime("%Y-%m-%d %H:%M")}
    _save_conversations(st.session_state.conversations)
    return fid


def _rename_folder(fid: str, new_name: str):
    if fid in _folders():
        _folders()[fid]["name"] = new_name.strip()[:20]
        _save_conversations(st.session_state.conversations)


def _delete_folder(fid: str):
    # 删除子文件夹
    for sfid in list(_folders().keys()):
        if _folders()[sfid].get("parent_id") == fid:
            _folders().pop(sfid, None)
    _folders().pop(fid, None)
    # 将该文件夹下的对话移到未分类
    for cdata in _convs().values():
        if cdata.get("folder_id") == fid:
            cdata["folder_id"] = ""
    _save_conversations(st.session_state.conversations)


def _move_conversation(conv_id: str, folder_id: str):
    if conv_id in _convs():
        _convs()[conv_id]["folder_id"] = folder_id
        _save_conversations(st.session_state.conversations)


def _get_folder_tree() -> list:
    """返回缩进排序的文件夹列表 [(fid, name, depth, parent_id), ...]"""
    folders = _folders()
    result = []

    def _recurse(parent_id, depth):
        children = [(fid, fd) for fid, fd in folders.items() if fd.get("parent_id") == parent_id]
        children.sort(key=lambda x: x[1].get("name", ""))
        for fid, fd in children:
            result.append((fid, fd["name"], depth, parent_id))
            _recurse(fid, depth + 1)

    _recurse("", 0)
    return result


def _folder_options() -> list:
    """生成文件夹选项列表 [(fid, display_name), ...]"""
    opts = [("", "📂 未分类")]
    tree = _get_folder_tree()
    for fid, name, depth, _ in tree:
        prefix = "  " * depth + ("└ " if depth > 0 else "")
        opts.append((fid, f"{prefix}📁 {name}"))
    return opts

# ════════════════════════════════════════════
# 初始化（只执行一次）
# ════════════════════════════════════════════
@st.cache_resource
def init_core():
    """缓存不依赖 LLM 的基础资源（向量库、Embeddings、复习智库）"""
    kb_manager = KnowledgeBaseManager()
    rag_engine = RAGEngine(kb_manager)
    vault = ReviewVault()
    return kb_manager, rag_engine, vault


kb_manager, rag_engine, vault = init_core()

# ── 用户 API 设置 & 动态 ChatAgent ──
if "user_settings" not in st.session_state:
    st.session_state.user_settings = UserSettings()

user_settings: UserSettings = st.session_state.user_settings
current_llm_config = user_settings.get_llm_config()
current_config_hash = user_settings.config_hash()

# 检测配置变化 → 重建 ChatAgent
if ("chat_agent" not in st.session_state or
    st.session_state.get("llm_config_hash") != current_config_hash):
    st.session_state.chat_agent = ChatAgent(
        kb_manager, rag_engine, vault, current_llm_config)
    st.session_state.llm_config_hash = current_config_hash

chat_agent: ChatAgent = st.session_state.chat_agent

# Session 状态
if "conversations" not in st.session_state:
    st.session_state.conversations = _load_conversations()
if "active_conv_id" not in st.session_state:
    import uuid as _uuid
    st.session_state.active_conv_id = _uuid.uuid4().hex[:12]
    _convs()[st.session_state.active_conv_id] = {
        "title": "新对话", "messages": [], "folder_id": "",
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
    }
if "active_kb_ids" not in st.session_state:
    st.session_state.active_kb_ids = []
if "pending_quiz" not in st.session_state:
    st.session_state.pending_quiz = None
if "show_kb_dialog" not in st.session_state:
    st.session_state.show_kb_dialog = False
if "show_vault_dialog" not in st.session_state:
    st.session_state.show_vault_dialog = False
if "show_settings_dialog" not in st.session_state:
    st.session_state.show_settings_dialog = False


# ════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════
st.html(get_css())

# JS：侧边栏展开锁定逻辑（修复 checkbox 点击后收起问题）
st.html("""<script>
(function() {
    function getSidebar() {
        return document.querySelector('section[data-testid="stSidebar"]');
    }

    var collapseTimer = null;
    var keepOpenUntil = parseInt(sessionStorage.getItem('aero_sidebar_expire')||'0');

    function expand() {
        var sb = getSidebar();
        if (sb) { sb.classList.add('sb-expanded'); sessionStorage.setItem('aero_sidebar_expanded', '1'); }
    }
    function collapse() {
        var sb = getSidebar();
        if (sb) { sb.classList.remove('sb-expanded'); sessionStorage.removeItem('aero_sidebar_expanded'); }
    }

    // 恢复上次状态
    if (sessionStorage.getItem('aero_sidebar_expanded') === '1') expand();

    function scheduleCollapse(delay) {
        clearTimeout(collapseTimer);
        collapseTimer = setTimeout(function() {
            var sb = getSidebar();
            if (!sb) return;
            var popover = document.querySelector('div[data-baseweb="popover"]');
            var menu = document.querySelector('ul[data-baseweb="menu"]');
            var selectOpen = document.querySelector('div[data-baseweb="select"] [aria-expanded="true"]');
            if (Date.now() < keepOpenUntil || popover || menu || selectOpen || sb.matches(':hover')) {
                scheduleCollapse(300);
                return;
            }
            collapse();
        }, delay);
    }

    document.addEventListener('click', function(e) {
        var sb = getSidebar();
        if (sb && sb.contains(e.target)) {
            // 文本框/下拉框等输入元素 → 保持 30 秒
            var isInput = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.closest('[data-baseweb="select"]');
            keepOpenUntil = Date.now() + (isInput ? 30000 : 3000);
            sessionStorage.setItem('aero_sidebar_expire', keepOpenUntil);
            expand();
        }
    });

    var observer = new MutationObserver(function() {
        if (document.querySelector('div[data-baseweb="popover"]') ||
            document.querySelector('ul[data-baseweb="menu"]') ||
            document.querySelector('div[data-baseweb="select"] [aria-expanded="true"]')) {
            keepOpenUntil = Date.now() + 5000;
            sessionStorage.setItem('aero_sidebar_expire', keepOpenUntil);
            expand();
        }
    });
    observer.observe(document.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['aria-expanded']});
})();
</script>""")

# hidden action receiver — JS 拖拽后通过 postMessage 写入
if "dnd_action" not in st.session_state:
    st.session_state.dnd_action = ""
dnd_action = st.text_input("dnd_action", key="dnd_action_input", label_visibility="collapsed")

# postMessage 监听器：将拖拽事件写入 hidden input
st.html("""<script>
window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'aero_dnd') {
        var inp = document.querySelector('input[aria-label="dnd_action"]');
        if (inp) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(inp, JSON.stringify(e.data.action));
            inp.dispatchEvent(new Event('input', {bubbles: true}));
        }
    }
});
</script>""")



# ════════════════════════════════════════════
# 辅助函数
# ════════════════════════════════════════════
def _stream_markdown(text: str, delay: float = 0.018):
    """逐段渲染 markdown，模拟打字机效果"""
    placeholder = st.empty()
    paragraphs = text.split("\n\n")
    accumulated = ""
    for para in paragraphs:
        accumulated += para + "\n\n"
        placeholder.markdown(accumulated.strip() + '<span class="streaming-cursor"></span>',
                             unsafe_allow_html=True)
        time.sleep(delay)
    placeholder.markdown(accumulated.strip(), unsafe_allow_html=True)


def _active_messages() -> list:
    """获取当前活跃对话的消息列表"""
    conv = _convs().get(st.session_state.active_conv_id, {})
    return conv.get("messages", [])


def _save_current_conv():
    """保存当前对话到持久化存储"""
    msgs = _active_messages()
    c = _convs().get(st.session_state.active_conv_id, {})
    c["title"] = _conv_title(msgs) if msgs else c.get("title", "新对话")
    c["messages"] = msgs
    c.setdefault("created_at", time.strftime("%Y-%m-%d %H:%M"))
    _convs()[st.session_state.active_conv_id] = c
    _save_conversations(st.session_state.conversations)


def _switch_conversation(conv_id: str, folder_id: str = ""):
    """切换到指定对话"""
    st.session_state.active_conv_id = conv_id
    if conv_id not in _convs():
        import uuid as _uuid
        _convs()[conv_id] = {
            "title": "新对话", "messages": [], "folder_id": folder_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
        }
    st.session_state.pending_quiz = None
    chat_agent._chat_history = []


# 从活跃对话同步 messages
st.session_state.messages = _active_messages()

# 处理拖拽动作
if dnd_action:
    try:
        action = _json.loads(dnd_action)
        atype = action.get("type", "")
        if atype == "move_conv":
            _move_conversation(action["conv_id"], action.get("folder_id", ""))
        elif atype == "switch_conv":
            _switch_conversation(action["conv_id"])
        elif atype == "new_folder":
            _create_folder(action["name"], action.get("parent", ""))
        elif atype == "new_subfolder":
            _create_folder("新文件夹", action.get("parent", ""))
        elif atype == "delete_folder":
            _delete_folder(action.get("folder_id", ""))
    except Exception:
        pass
    st.session_state.dnd_action_input = ""
    st.rerun()

# ════════════════════════════════════════════
# 侧边栏
# ════════════════════════════════════════════
with st.sidebar:
    # ── Logo ──
    st.markdown(f"""
    <div style="text-align:center;padding:0.8rem 0 0.6rem 0;">
        <div style="font-size:1.8rem;">🎓</div>
        <div style="font-weight:700;font-size:0.85rem;color:{t['text_primary']};margin-top:0.2rem;">AeroTutor</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 新建文件夹 ──
    with st.expander("📁 新建文件夹", expanded=False):
        new_fname = st.text_input("名称", key="new_folder_name", placeholder="文件夹名", label_visibility="collapsed")
        parent_opts = [("", "根目录")] + [(fid, fd["name"]) for fid, fd in sorted(_folders().items(), key=lambda x: x[1].get("name", ""))]
        parent_sel = st.selectbox("父文件夹", parent_opts, format_func=lambda x: x[1], key="new_folder_parent", label_visibility="collapsed")
        create_clicked = st.button("➕ 创建文件夹", use_container_width=True, key="create_folder_btn")
        if create_clicked:
            name = (new_fname or "").strip()
            pid = parent_sel[0] if parent_sel and parent_sel[0] else ""
            if name:
                # 防重复：检查是否刚刚创建过同名同父文件夹
                last_key = f"_last_create_{name}_{pid}"
                now_ts = time.time()
                last_ts = st.session_state.get(last_key, 0)
                if now_ts - last_ts > 2.0:  # 2 秒内不重复创建
                    _create_folder(name, pid)
                    st.session_state[last_key] = now_ts
                    # 清空输入防止 rerun 时再次触发
                    if "new_folder_name" in st.session_state:
                        st.session_state.new_folder_name = ""
                    st.rerun()
            else:
                st.warning("请输入文件夹名称")

    # ── 新建对话 ──
    new_conv_folder = st.selectbox(
        "存入", _folder_options(), format_func=lambda x: x[1],
        key="new_conv_folder", label_visibility="collapsed")

    if st.button("✨ 新对话", use_container_width=True, key="new_chat_btn"):
        import uuid as _uuid
        new_id = _uuid.uuid4().hex[:12]
        _switch_conversation(new_id, new_conv_folder[0] if new_conv_folder[0] else "")
        st.rerun()

    st.divider()

    # ── 拖拽文件夹树 ──
    st.html(build_dnd_html(_convs(), _folders(), st.session_state.active_conv_id, t))

    st.divider()

    # ── 知识空间 ──
    all_kbs = kb_manager.list_kbs()
    new_active = []
    if all_kbs:
        st.caption("📚 知识库")
        for kb in all_kbs:
            checked = st.checkbox(
                f"{kb['name']}",
                value=kb["id"] in st.session_state.active_kb_ids,
                key=f"sidebar_kb_{kb['id']}",
            )
            if checked:
                new_active.append(kb["id"])
    else:
        st.caption("📚 暂无知识空间")

    st.session_state.active_kb_ids = new_active
    if new_active:
        chat_agent.set_active_kbs(new_active)

    st.divider()


    # ── 底部：管理入口 + 设置 ──
    ckb, cvb, csb = st.columns(3)
    with ckb:
        if st.button("📁 知识空间", use_container_width=True, key="sidebar_kb_btn",
                     help="管理知识空间和文件"):
            st.session_state.show_kb_dialog = True
    with cvb:
        if st.button("🧠 复习智库", use_container_width=True, key="sidebar_vault_btn",
                     help="查看错题本、闪卡、诊断报告"):
            st.session_state.show_vault_dialog = True
    with csb:
        if st.button("⚙️ 设置", use_container_width=True, key="sidebar_settings_btn",
                     help="配置 API 供应商和密钥"):
            st.session_state.show_settings_dialog = True

    # 学习统计
    st.divider()
    stats = vault.get_stats()
    st.markdown(f"""
    <div style="font-size:0.75rem;color:{t['text_secondary']};line-height:1.8;">
        🔥 连续 {stats['streak_days']} 天 · 📝 {stats['total_quizzes']} 次测验<br>
        🃏 {stats['flashcard_count']} 张闪卡 · ❌ {stats['wrong_count']} 道错题
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════
# 弹窗：知识空间管理
# ════════════════════════════════════════════
@st.dialog("📁 知识空间管理", width="large")
def show_kb_dialog():
    kb_tab1, kb_tab2 = st.tabs(["📋 知识空间列表", "➕ 创建新空间"])
    with kb_tab1:
        all_kbs = kb_manager.list_kbs()
        if not all_kbs:
            st.info("暂无知识空间，请先创建。")
        for kb in all_kbs:
            with st.expander(f"📚 {kb['name']} · {kb['doc_count']} 文档 · {kb.get('category', '')}"):
                # 文件上传
                uploaded = st.file_uploader(
                    "上传 PDF / PPTX / TXT / MD",
                    type=["pdf", "pptx", "ppt", "txt", "md"],
                    key=f"dialog_fu_{kb['id']}",
                    label_visibility="visible",
                )
                if uploaded:
                    with st.spinner(f"解析「{uploaded.name}」..."):
                        from ui.kb_panel import _parse_uploaded_file
                        try:
                            text = _parse_uploaded_file(uploaded)
                            if text.strip():
                                count = kb_manager.add_file(kb["id"], uploaded.name, text.strip())
                                st.success(f"✅ 已入库 → {count} 块")
                                st.rerun()
                            else:
                                st.warning("未提取到有效文字")
                        except Exception as e:
                            st.error(f"解析失败：{str(e)[:200]}")

                # 文件列表
                files = kb_manager.list_files(kb["id"])
                if files:
                    for f in files:
                        fc1, fc2 = st.columns([0.85, 0.15])
                        with fc1:
                            st.caption(f"📄 {f['file_name']} · {f['chunk_count']} 块")
                        with fc2:
                            if st.button("🗑️", key=f"dialog_del_{kb['id']}_{f['file_name']}"):
                                kb_manager.delete_file(kb["id"], f["file_name"])
                                st.rerun()
                else:
                    st.caption("暂无文件")

                # 删除空间
                if st.button(f"🗑️ 删除「{kb['name']}」", key=f"dialog_delkb_{kb['id']}"):
                    kb_manager.delete_kb(kb["id"])
                    if kb["id"] in st.session_state.active_kb_ids:
                        st.session_state.active_kb_ids.remove(kb["id"])
                    st.rerun()

    with kb_tab2:
        from config import KB_CATEGORIES, KB_CATEGORY_LABELS
        name = st.text_input("空间名称", placeholder="如：空气动力学", key="dialog_kb_name")
        desc = st.text_area("描述（可选）", key="dialog_kb_desc")
        cat = st.radio(
            "分类", KB_CATEGORIES,
            format_func=lambda x: KB_CATEGORY_LABELS.get(x, x),
            key="dialog_kb_cat",
            horizontal=True,
            label_visibility="collapsed",
        )
        if st.button("✅ 创建", use_container_width=True):
            if name.strip():
                kb_manager.create_kb(name.strip(), desc.strip(), cat)
                st.success(f"「{name}」创建成功！")
                st.rerun()
            else:
                st.warning("请输入名称")


# ════════════════════════════════════════════
# 弹窗：复习智库
# ════════════════════════════════════════════
@st.dialog("🧠 复习智库", width="large")
def show_vault_dialog():
    render_vault_panel(vault)


# ── 弹窗：API 设置 ──
@st.dialog("⚙️ API 设置", width="large")
def show_settings_dialog():
    st.caption("选择 AI 模型供应商，填入你的 API Key 即可切换")

    # 当前供应商
    current_provider = user_settings.provider

    # ── 供应商选择 ──
    provider_names = [(k, v["name"]) for k, v in PROVIDERS.items()]
    current_idx = max(0, [i for i, (k, _) in enumerate(provider_names) if k == current_provider][0]
                      if current_provider in PROVIDERS else 0)

    selected_provider_key = st.radio(
        "🤖 供应商",
        options=list(PROVIDERS.keys()),
        format_func=lambda k: f"{PROVIDERS[k]['name']}  {'（OpenAI 兼容）' if k == 'custom' else ''}",
        index=current_idx,
        horizontal=True,
        key="settings_provider",
    )

    preset = PROVIDERS.get(selected_provider_key, PROVIDERS["deepseek"])

    st.divider()

    # ── API Key ──
    col_key, col_model = st.columns([1, 1])
    with col_key:
        current_key = user_settings.api_key if current_provider == selected_provider_key else ""
        api_key = st.text_input(
            "🔑 API Key",
            type="password",
            value=current_key,
            placeholder=f"输入你的 {preset['name']} API Key...",
            key="settings_api_key",
        )
    with col_model:
        if selected_provider_key == "custom":
            model = st.text_input(
                "🧩 模型名称",
                value=user_settings.model if current_provider == selected_provider_key else "",
                placeholder="如：gpt-4o-mini、qwen-turbo...",
                key="settings_model",
            )
        else:
            current_model = user_settings.model if current_provider == selected_provider_key else preset["default_model"]
            model_idx = 0
            if current_model in preset["models"]:
                model_idx = preset["models"].index(current_model)
            model = st.selectbox(
                "🧩 模型",
                options=preset["models"],
                index=model_idx,
                key="settings_model",
            )

    # ── 自定义 Base URL ──
    if selected_provider_key == "custom":
        current_base = user_settings._data.get("base_url", "")
        base_url = st.text_input(
            "🌐 Base URL",
            value=current_base if current_provider == "custom" else "",
            placeholder="https://your-api-endpoint/v1",
            key="settings_base_url",
        )
    else:
        base_url = preset["base_url"]

    # ── 高级参数 ──
    with st.expander("⚡ 高级参数", expanded=False):
        ct1, ct2 = st.columns(2)
        with ct1:
            temperature = st.slider(
                "Temperature", 0.0, 1.0,
                value=user_settings.temperature,
                step=0.05,
                help="越高越有创意，越低越保守",
                key="settings_temperature",
            )
        with ct2:
            max_tokens = st.number_input(
                "Max Tokens", 256, 8192,
                value=user_settings.max_tokens,
                step=256,
                help="单次回复最大 token 数",
                key="settings_max_tokens",
            )

    st.divider()

    # ── 按钮行 ──
    col_test, col_save, col_reset = st.columns([1, 1, 1])
    with col_test:
        test_clicked = st.button("🔍 测试连接", use_container_width=True, key="settings_test_btn")
    with col_save:
        save_clicked = st.button("💾 保存设置", use_container_width=True, type="primary", key="settings_save_btn")
    with col_reset:
        if st.button("🔄 恢复默认", use_container_width=True, key="settings_reset_btn"):
            if os.path.exists(user_settings.SETTINGS_FILE):
                os.remove(user_settings.SETTINGS_FILE)
            st.session_state.user_settings = UserSettings()
            st.session_state.llm_config_hash = ""
            st.rerun()

    # ── 测试连接 ──
    if test_clicked:
        if not api_key.strip():
            st.error("请先输入 API Key")
        else:
            with st.spinner("正在测试连接..."):
                ok, msg = user_settings.test_connection(
                    selected_provider_key, api_key, model, base_url)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # ── 保存设置 ──
    if save_clicked:
        if not api_key.strip():
            st.error("请先输入 API Key")
        else:
            user_settings.update(
                provider=selected_provider_key,
                api_key=api_key,
                model=model,
                base_url=base_url,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # 立即重建 ChatAgent
            new_config = user_settings.get_llm_config()
            st.session_state.llm_config_hash = user_settings.config_hash()
            if hasattr(st.session_state.chat_agent, 'reconfigure'):
                st.session_state.chat_agent.reconfigure(new_config)
            else:
                st.session_state.chat_agent = ChatAgent(
                    kb_manager, rag_engine, vault, new_config)
            st.success(f"✅ 已切换到 {preset['name']} · `{model}`")
            time.sleep(0.8)
            st.rerun()

# 触发弹窗
if st.session_state.show_kb_dialog:
    show_kb_dialog()
    st.session_state.show_kb_dialog = False
if st.session_state.show_vault_dialog:
    show_vault_dialog()
    st.session_state.show_vault_dialog = False
if st.session_state.show_settings_dialog:
    show_settings_dialog()
    st.session_state.show_settings_dialog = False


# ════════════════════════════════════════════
# 主区域
# ════════════════════════════════════════════

# ── 情况 A：欢迎页（无消息）──
if not st.session_state.messages:
    st.markdown('<div style="margin-top:8vh;"></div>', unsafe_allow_html=True)
    render_welcome_screen()

    # 建议问题
    suggestions = [
        ("📝 出几道测验题", "帮我从知识库出3道测验题"),
        ("🔍 诊断薄弱点", "分析我的学习薄弱点"),
        ("⚡ 速查摘要", "帮我总结知识库的核心重点"),
        ("🃏 制作闪卡", "基于知识库生成5张学习闪卡"),
    ]
    clicked = render_suggestion_chips(suggestions)

    if clicked:
        st.session_state.messages.append({"role": "user", "content": clicked, "id": 0})
        _save_current_conv()
        st.rerun()

# ── 情况 B：对话历史 ──
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                render_source_tags(msg["sources"])
            if msg.get("quiz"):
                with st.expander("📝 查看测验题", expanded=True):
                    render_quiz_card(msg["quiz"], f"msg_{msg.get('id', '')}", vault, current_llm_config)
            if msg.get("podcast"):
                render_podcast(msg["podcast"])
            if msg.get("summary"):
                render_quick_summary(msg["summary"])
            if msg.get("learning_path"):
                render_learning_path(msg["learning_path"])

# ── 待处理测验 ──
if st.session_state.pending_quiz:
    with st.expander("📝 快捷测验", expanded=True):
        render_quiz_card(st.session_state.pending_quiz, "pending", vault, current_llm_config)


# ════════════════════════════════════════════
# 底部输入区
# ════════════════════════════════════════════
# 快捷操作按钮行（Gemini Chip 风格）
if st.session_state.active_kb_ids:
    qc1, qc2, qc3, qc4, qc5 = st.columns([1, 1, 1, 1, 2])
    quick_action = None
    with qc1:
        if st.button("📝 生成测验", use_container_width=True, key="quick_quiz"):
            quick_action = "quiz"
    with qc2:
        if st.button("🃏 制作闪卡", use_container_width=True, key="quick_cards"):
            quick_action = "flashcards"
    with qc3:
        if st.button("🔍 诊断薄弱点", use_container_width=True, key="quick_diag"):
            quick_action = "diagnosis"
    with qc4:
        if st.button("⚡ 速查摘要", use_container_width=True, key="quick_summary"):
            quick_action = "summary"

    if quick_action:
        action_map = {
            "quiz": "帮我从知识库出3道测验题",
            "flashcards": "基于知识库生成5张学习闪卡",
            "diagnosis": "分析我的学习薄弱点",
            "summary": "帮我总结知识库的核心重点",
        }
        prompt_text = action_map[quick_action]
        st.session_state.messages.append({"role": "user", "content": prompt_text, "id": len(st.session_state.messages)})
        chat_agent.set_active_kbs(st.session_state.active_kb_ids)
        result = chat_agent.invoke(prompt_text)
        response = result.get("response", "")
        msg_id = len(st.session_state.messages)
        msg_data = {"role": "assistant", "content": response, "id": msg_id}
        if result.get("quiz"):
            msg_data["quiz"] = result["quiz"]
        if result.get("podcast"):
            msg_data["podcast"] = result["podcast"]
        if result.get("summary"):
            msg_data["summary"] = result["summary"]
        if result.get("learning_path"):
            msg_data["learning_path"] = result["learning_path"]
        st.session_state.messages.append(msg_data)
        _save_current_conv()
        st.rerun()

# 聊天输入
if prompt := st.chat_input("输入你的问题，或试试「帮我出几道题」「分析我的薄弱点」..."):
    # 用户消息
    st.session_state.messages.append({"role": "user", "content": prompt, "id": len(st.session_state.messages)})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 回复
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.markdown(f'<span style="color:{t["text_secondary"]};">✨ 思考中...</span>', unsafe_allow_html=True)
        chat_agent.set_active_kbs(st.session_state.active_kb_ids)
        result = chat_agent.invoke(prompt)
        response = result.get("response", "抱歉，处理请求时遇到了问题。")
        status_placeholder.empty()
        _stream_markdown(response)

        # 渲染附属卡片
        quiz_data = result.get("quiz")
        if quiz_data and quiz_data.get("questions"):
            with st.expander("📝 查看测验题", expanded=True):
                render_quiz_card(quiz_data, f"quiz_{len(st.session_state.messages)}", vault, current_llm_config)

        podcast = result.get("podcast")
        if podcast:
            render_podcast(podcast)

        summary = result.get("summary")
        if summary:
            with st.expander("⚡ 查看速查摘要", expanded=True):
                render_quick_summary(summary)

        diagnosis = result.get("diagnosis")
        if diagnosis:
            with st.expander("📊 认知诊断详情", expanded=False):
                st.markdown(f"**整体评估**：{diagnosis.get('overall_assessment', '')}")
                for wp in diagnosis.get("weak_points", []):
                    st.markdown(f"🟡 {wp['topic']} — {wp.get('evidence', '')}")
                for sp in diagnosis.get("strong_points", []):
                    st.markdown(f"🟢 {sp['topic']}")
                for gp in diagnosis.get("gaps", []):
                    st.markdown(f"🔴 {gp['topic']} — {gp.get('suggestion', '')}")

        path = result.get("learning_path")
        if path:
            render_learning_path(path)

        flashcards = result.get("flashcards")
        if flashcards:
            st.success(f"🃏 {len(flashcards)} 张闪卡已存入复习智库")

        # 保存消息
        msg_id = len(st.session_state.messages)
        msg_data = {"role": "assistant", "content": response, "id": msg_id}
        if quiz_data:
            msg_data["quiz"] = quiz_data
        if podcast:
            msg_data["podcast"] = podcast
        if summary:
            msg_data["summary"] = summary
        if path:
            msg_data["learning_path"] = path
        st.session_state.messages.append(msg_data)
        _save_current_conv()


# ════════════════════════════════════════════
# 页脚
# ════════════════════════════════════════════
st.markdown(f"""
<div style="text-align:center;color:{t['text_tertiary']};font-size:0.7rem;padding:1.5rem 0 0.5rem 0;letter-spacing:0.5px;">
    🎓 {AGENT_NAME} · {SCHOOL_NAME} · 第一届「筑梦空天」AI 智能体创新应用大赛
</div>
""", unsafe_allow_html=True)
