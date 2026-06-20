"""通用工具函数"""
import json
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AeroTutor")

def log(level: str, msg: str):
    getattr(logger, level, logger.info)(f"[{datetime.now():%H:%M:%S}] {msg}")

def safe_json_parse(text: str):
    """
    从 LLM 返回的文本中安全提取 JSON（对象或数组）。

    处理策略：
    1. 去除 markdown 代码围栏（```json … ``` 或 ``` … ```）
    2. 尝试直接解析
    3. 失败则用正则提取 top-level JSON 结构
    4. 对象和数组都能正确处理
    """
    text = text.strip()

    # ── 去除 markdown 代码围栏 ──
    fence_pattern = re.compile(r"^```(?:json|JSON)?\s*\n(.*?)\n```\s*$", re.DOTALL)
    m = fence_pattern.match(text)
    if m:
        text = m.group(1).strip()
    elif text.startswith("```"):
        # 不规范的围栏（没有闭合或没有语言标注）
        lines = text.split("\n")
        if len(lines) > 1 and lines[0].startswith("```"):
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    def _try_parse(s: str):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    # ── 直接解析 ──
    result = _try_parse(text)
    if result is not None:
        return result

    # ── 尝试提取最外层的 JSON 结构 ──
    # 先尝试对象
    for pattern in [r"\{.*\}", r"\[.*\]"]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            result = _try_parse(match.group())
            if result is not None:
                return result

    # ── 最后兜底：找到第一个 { 或 [，尝试匹配到对应的闭合位置 ──
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        in_string = False
        escape = False
        for i, ch in enumerate(text[start:], start=start):
            if escape:
                escape = False
                continue
            if ch == '"' and not escape:
                in_string = not in_string
            elif ch == '\\' and in_string:
                escape = True
            elif not in_string:
                if ch == start_char:
                    depth += 1
                elif ch == end_char:
                    depth -= 1
                    if depth == 0:
                        result = _try_parse(text[start:i + 1])
                        if result is not None:
                            return result
                        break

    # 彻底失败：返回空容器（调用方根据上下文判断类型）
    log("warning", f"safe_json_parse: 无法从文本中提取 JSON，原文前 200 字符: {text[:200]}")
    return {}
