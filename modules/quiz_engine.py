"""
模块 D：测验生成 + 闪卡生成 (Generative UI)
- 基于知识库内容自动出题
- 生成知识闪卡（正面概念 / 反面解释）
- 优化④：速查闪卡 — 知识空间摘要
"""
import json
from utils.helpers import safe_json_parse


class QuizEngine:
    """测验 & 闪卡生成引擎"""

    def __init__(self, llm):
        self.llm = llm

    def generate_quiz(self, context: str, num_questions: int = 3) -> dict:
        """基于上下文生成测验题"""
        prompt = f"""基于以下知识内容，生成 {num_questions} 道测验题。

## 要求
- 题型：1 道选择题（4 个选项），{num_questions - 1} 道简答题
- 每道题标注知识点 (topic) 和难度 (difficulty: easy/medium/hard)
- 每道题附参考答案 (answer) 和解析 (explanation)

## 知识内容
{context[:3000]}

## 输出：仅输出 JSON
```json
{{
  "title": "测验标题",
  "questions": [
    {{
      "type": "choice",
      "topic": "知识点",
      "difficulty": "medium",
      "question": "题目内容",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "B",
      "explanation": "解析"
    }},
    {{
      "type": "short_answer",
      "topic": "知识点",
      "difficulty": "easy",
      "question": "题目内容",
      "answer": "参考答案要点",
      "explanation": "解析"
    }}
  ]
}}
```"""

        result = self.llm.invoke(prompt)
        quiz_data = safe_json_parse(result.content)
        return quiz_data

    def generate_flashcards(self, context: str, num_cards: int = 5) -> list[dict]:
        """基于上下文生成知识闪卡"""
        prompt = f"""基于以下知识内容，生成 {num_cards} 张知识闪卡。

## 闪卡格式
每张闪卡包含：
- front（正面）：核心概念/关键词/公式名称
- back（反面）：详细解释/公式内容/关键理解
- topic（所属知识点）

## 知识内容
{context[:3000]}

## 输出：仅输出 JSON 数组
```json
[
  {{"front": "伯努利原理", "back": "流体在流动过程中，流速增大的地方压强减小，流速减小的地方压强增大。该原理解释了机翼产生升力的根本原因。", "topic": "空气动力学基础"}},
  ...
]
```"""

        result = self.llm.invoke(prompt)
        cards = safe_json_parse(result.content)
        if isinstance(cards, dict):
            cards = cards.get("cards", [])
        return cards if isinstance(cards, list) else []

    def generate_quick_summary(self, context: str, kb_name: str) -> dict:
        """
        优化④：速查闪卡 — 一键生成知识空间摘要
        """
        prompt = f"""你是沈航资深课程助教。请为知识空间「{kb_name}」生成一份速查摘要。

## 知识内容
{context[:4000]}

## 输出格式（仅 JSON）
```json
{{
  "core_concepts": ["概念1 - 一句话解释", "概念2 - 一句话解释", "概念3 - 一句话解释"],
  "key_formulas": ["公式1名称: 公式内容", "公式2名称: 公式内容"],
  "common_mistakes": ["误区1", "误区2"],
  "suggested_review": "一段 50 字内的复习建议"
}}
```"""

        result = self.llm.invoke(prompt)
        summary = safe_json_parse(result.content)
        return summary

    def generate_podcast_script(self, context: str, kb_name: str) -> str:
        """
        优化②：知识播客 — 生成双人对话式知识脚本
        """
        prompt = f"""你是沈航的资深教授。请为知识空间「{kb_name}」生成一段"师生对话"式知识播客脚本。

## 知识内容
{context[:3000]}

## 要求
- 老师角色：王教授，讲课风趣幽默，善于用比喻
- 学生角色：小明，航空航天专业大二学生，好奇心强
- 对话自然流畅，像真实课堂互动
- 覆盖知识内容中的核心知识点
- 长度：10-15 个对话回合

## 输出格式
```
👨‍🏫 王教授：（对话内容）
🧑‍🎓 小明：（对话内容）
👨‍🏫 王教授：（对话内容）
...
```"""

        result = self.llm.invoke(prompt)
        return result.content

    def grade_answer(self, question: str, reference_answer: str, student_answer: str) -> dict:
        """评估学生答案（按要点打分）"""
        prompt = f"""你是沈航课程助教，正在批改一道作业题。

## 题目
{question}

## 参考答案（评分要点）
{reference_answer}

## 学生答案
{student_answer}

## 评分要求
- 按参考答案的要点逐一比对
- 满分 20 分，每个要点分配合理分值
- 指出哪些要点答对了，哪些遗漏或错误
- 给出总分和改进建议

## 输出（仅 JSON）
```json
{{
  "total_score": 15,
  "max_score": 20,
  "points": [
    {{"content": "要点1描述", "score": 5, "max": 5, "comment": "完全正确"}},
    {{"content": "要点2描述", "score": 3, "max": 5, "comment": "部分正确，缺少..."}}
  ],
  "feedback": "总体评价和建议"
}}
```"""

        result = self.llm.invoke(prompt)
        grade = safe_json_parse(result.content)
        return grade
