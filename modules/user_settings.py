"""
用户自定义 API 设置 — 供应商切换 & 配置持久化
支持：DeepSeek / 智谱 GLM / 自定义 OpenAI 兼容接口
"""
import os
import json
import hashlib
import time

from config import LLM_CONFIG as _ENV_LLM_CONFIG

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_settings.json")

PROVIDERS = {
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


class UserSettings:
    """用户 API 设置管理器"""

    SETTINGS_FILE = SETTINGS_FILE  # 从模块常量继承

    def __init__(self):
        self._data = self._load()

    # ── 持久化 ──

    def _load(self) -> dict:
        """加载用户设置，首次启动从 .env 继承"""
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 兼容旧格式：确保所有 key 存在
            for key in ("provider", "api_key", "model", "base_url",
                        "temperature", "max_tokens"):
                data.setdefault(key, self._defaults().get(key, ""))
            return data
        return self._defaults()

    def _defaults(self) -> dict:
        """从 .env 读取默认值"""
        provider = "deepseek"
        # 尝试从 base_url 自动检测供应商
        env_url = _ENV_LLM_CONFIG.get("base_url", "")
        if "bigmodel" in env_url:
            provider = "glm"

        preset = PROVIDERS.get(provider, PROVIDERS["deepseek"])
        return {
            "provider": provider,
            "api_key": _ENV_LLM_CONFIG.get("api_key", ""),
            "model": _ENV_LLM_CONFIG.get("model", preset["default_model"]),
            "base_url": _ENV_LLM_CONFIG.get("base_url", preset["base_url"]),
            "temperature": _ENV_LLM_CONFIG.get("temperature", 0.4),
            "max_tokens": _ENV_LLM_CONFIG.get("max_tokens", 2048),
        }

    def save(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # ── 配置获取 ──

    def get_llm_config(self) -> dict:
        """返回当前 LLM 配置（用于 ChatOpenAI）"""
        provider = self._data.get("provider", "deepseek")
        preset = PROVIDERS.get(provider, PROVIDERS["deepseek"])

        # base_url: 用户自定义 > 预设 > .env
        base_url = self._data.get("base_url") or preset["base_url"]
        # api_key: 用户设置 > .env fallback
        api_key = self._data.get("api_key") or _ENV_LLM_CONFIG.get("api_key", "")

        return {
            "base_url": base_url,
            "api_key": api_key,
            "model": self._data.get("model") or preset["default_model"],
            "temperature": self._data.get("temperature", 0.4),
            "max_tokens": self._data.get("max_tokens", 2048),
        }

    def config_hash(self) -> str:
        """配置指纹，用于检测变化"""
        raw = json.dumps(self.get_llm_config(), sort_keys=True, ensure_ascii=False)
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    # ── 更新 ──

    def update(self, provider: str, api_key: str, model: str,
               base_url: str = "", temperature: float = 0.4,
               max_tokens: int = 2048):
        """更新并持久化设置"""
        self._data["provider"] = provider
        self._data["api_key"] = api_key.strip()
        self._data["model"] = model.strip()
        self._data["base_url"] = base_url.strip()
        self._data["temperature"] = float(temperature)
        self._data["max_tokens"] = int(max_tokens)
        self.save()

    # ── 连接测试 ──

    def test_connection(self, provider: str, api_key: str,
                        model: str, base_url: str = "") -> tuple:
        """测试 API 连通性，返回 (ok: bool, message: str)"""
        from langchain_openai import ChatOpenAI

        preset = PROVIDERS.get(provider, PROVIDERS["custom"])
        test_url = base_url.strip() or preset["base_url"]
        test_model = model.strip() or preset["default_model"]
        test_key = api_key.strip() or _ENV_LLM_CONFIG.get("api_key", "")

        if not test_key:
            return False, "请先输入 API Key"
        if not test_url:
            return False, "请先配置 Base URL"
        if not test_model:
            return False, "请先输入模型名称"

        try:
            llm = ChatOpenAI(
                base_url=test_url,
                api_key=test_key,
                model=test_model,
                temperature=0.0,
                max_tokens=16,
                timeout=15,
            )
            t0 = time.time()
            result = llm.invoke("回复 OK")
            elapsed = time.time() - t0
            return True, f"连接成功 ✅ · 响应耗时 {elapsed:.1f}s · 模型 `{test_model}`"
        except Exception as e:
            msg = str(e)[:300]
            if "401" in msg or "Unauthorized" in msg:
                return False, "❌ API Key 无效（401 Unauthorized）"
            if "403" in msg or "Forbidden" in msg:
                return False, "❌ 访问被拒（403 Forbidden），请检查 API Key 权限"
            if "404" in msg:
                return False, f"❌ 接口不存在（404），请检查 Base URL 和模型名"
            if "timeout" in msg.lower() or "timed out" in msg.lower():
                return False, "❌ 连接超时，请检查网络或 Base URL"
            return False, f"❌ 连接失败：{msg}"

    # ── 便捷属性 ──

    @property
    def provider(self) -> str:
        return self._data.get("provider", "deepseek")

    @property
    def api_key(self) -> str:
        return self._data.get("api_key", "")

    @property
    def model(self) -> str:
        return self._data.get("model", "")

    @property
    def temperature(self) -> float:
        return self._data.get("temperature", 0.4)

    @property
    def max_tokens(self) -> int:
        return self._data.get("max_tokens", 2048)
