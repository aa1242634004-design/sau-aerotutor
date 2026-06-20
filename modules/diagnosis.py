"""
模块 C：动态认知诊断 (Weakness Detection)
- 分析对话历史 + 测验结果，识别薄弱知识点
- 优化③：生成学习航线图
"""
import json
from utils.helpers import safe_json_parse


class DiagnosisEngine:
    """认知诊断引擎"""

    def __init__(self, llm):
        self.llm = llm

    def analyze_weakness(self, chat_history: list, quiz_results: list = None) -> dict:
        """
        分析学生的薄弱知识点
        chat_history: 最近的对话记录
        quiz_results: 测验结果列表 [{"topic": "...", "score": 5, "max": 10}, ...]
        """
        history_text = ""
        for msg in chat_history[-20:]:  # 最近 20 条
            role = msg.get("role", "user")
            content = msg.get("content", "")[:300]
            history_text += f"[{role}] {content}\n"

        quiz_text = ""
        if quiz_results:
            quiz_text = json.dumps(quiz_results, ensure_ascii=False)

        prompt = f"""你是沈航学习分析专家。请分析以下学生的学习活动，诊断其薄弱知识点。

## 对话历史
{history_text or "无对话记录"}

## 测验结果
{quiz_text or "无测验记录"}

## 输出（仅 JSON）
```json
{{
  "overall_assessment": "整体学习评估（50 字内）",
  "weak_points": [
    {{"topic": "薄弱知识点名称", "level": "weak", "evidence": "判断依据", "importance": "high"}}
  ],
  "strong_points": [
    {{"topic": "已掌握知识点", "level": "mastered"}}
  ],
  "gaps": [
    {{"topic": "可能遗漏的知识点", "level": "unknown", "suggestion": "建议补充学习的内容"}}
  ]
}}
```

## 等级说明
- mastered: 对话/测验中表现出正确理解
- weak: 有明显的理解错误或知识漏洞
- unknown: 该知识领域尚未涉及
"""

        result = self.llm.invoke(prompt)
        diagnosis = safe_json_parse(result.content)
        return diagnosis

    def generate_learning_path(self, diagnosis: dict) -> str:
        """
        优化③：基于诊断结果生成学习航线
        """
        weak_points = diagnosis.get("weak_points", [])
        gaps = diagnosis.get("gaps", [])
        strong_points = diagnosis.get("strong_points", [])

        all_to_learn = weak_points + gaps
        if not all_to_learn:
            return "🎉 当前学习状态良好，未发现明显薄弱点！继续保持。"

        prompt = f"""你是沈航学习规划师。请为以下学生生成一条「学习航线」。

## 已有基础
{json.dumps([s["topic"] for s in strong_points], ensure_ascii=False)}

## 需要加强的知识点（按优先级）
{json.dumps([{"topic": p["topic"], "importance": p.get("importance", "medium")} for p in all_to_learn], ensure_ascii=False)}

## 要求
- 设计 3-5 步学习路径，从基础到进阶
- 每步包含：知识点名称、建议学习时长（分钟）、推荐资源类型（PPT/教材/视频/习题）
- 考虑知识点之间的前置依赖关系
- 使用鼓励性语言

## 输出格式（Markdown）
```
🧭 **你的学习航线**

**Step 1: [知识点名]** ⏱️ XX 分钟
→ 学习建议：...

**Step 2: [知识点名]** ⏱️ XX 分钟
→ 学习建议：...

...
```"""

        result = self.llm.invoke(prompt)
        return result.content
