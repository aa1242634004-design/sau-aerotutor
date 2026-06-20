"""
沈航智学 AeroTutor — 全局配置
"""
import os
from dotenv import load_dotenv

# 显式指定 .env 路径，避免 Streamlit 工作目录不一致
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_ENV_PATH)


def _get_secret(key: str, default: str = "") -> str:
    """
    优先从 Streamlit Secrets 读取，fallback 到环境变量。
    Streamlit Cloud 部署时在 TOML 中设置；本地通过 .env 设置。
    """
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key, default)

LLM_CONFIG = {
    "base_url": _get_secret("LLM_BASE_URL", "https://api.deepseek.com/v1"),
    "api_key": _get_secret("LLM_API_KEY", "sk-placeholder"),
    "model": _get_secret("LLM_MODEL", "deepseek-chat"),
    "temperature": 0.3,
    "max_tokens": 2048,
}

EMBEDDING_CONFIG = {
    "provider": _get_secret("EMBEDDING_PROVIDER", "local"),
    "model": _get_secret("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
    "api_key": _get_secret("EMBEDDING_API_KEY", ""),
    "base_url": _get_secret("EMBEDDING_BASE_URL", ""),
}

CHROMA_CONFIG = {
    "persist_directory": os.path.join(os.path.dirname(__file__), "chroma_db"),
}

AGENT_NAME = "沈航智学 AeroTutor"
AGENT_SLOGAN = "NotebookLM 风格 · 多知识库隔离 · 自适应学习"
SCHOOL_NAME = "沈阳航空航天大学"

KB_CATEGORIES = ["course", "note", "paper", "reference", "other"]
KB_CATEGORY_LABELS = {
    "course": "📚 课程课件",
    "note": "📝 学习笔记",
    "paper": "📄 论文文献",
    "reference": "📖 参考资料",
    "other": "📋 其他",
}

# ── API 供应商预设 ──
PROVIDER_PRESETS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
    },
    "glm": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-flash", "glm-4-plus", "glm-4"],
        "default_model": "glm-4-flash",
    },
    "custom": {
        "name": "自定义",
        "base_url": "",
        "models": [],
        "default_model": "",
    },
}


def get_effective_llm_config(user_settings_data: dict | None = None) -> dict:
    """合并用户设置与 .env 默认值，用户设置优先"""
    config = dict(LLM_CONFIG)  # 从 .env 复制默认值
    if user_settings_data:
        provider = user_settings_data.get("provider", "deepseek")
        preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["deepseek"])
        config["base_url"] = user_settings_data.get("base_url") or preset["base_url"] or config["base_url"]
        config["api_key"] = user_settings_data.get("api_key") or config["api_key"]
        config["model"] = user_settings_data.get("model") or preset["default_model"] or config["model"]
        config["temperature"] = user_settings_data.get("temperature", config["temperature"])
        config["max_tokens"] = user_settings_data.get("max_tokens", config["max_tokens"])
    return config

# 认知诊断-薄弱等级
WEAKNESS_LEVELS = {
    "mastered": {"label": "已掌握 🟢", "color": "#00e676"},
    "weak": {"label": "薄弱 🟡", "color": "#ffab00"},
    "unknown": {"label": "未覆盖 🔴", "color": "#ff5252"},
}
