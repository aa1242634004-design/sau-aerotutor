"""
模块 B+C+D：对话 Agent — RAG + Function Calling
- 集成知识库检索、测验生成、闪卡生成、弱点诊断
- 使用 langchain.agents.create_agent
"""
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

import re

from config import LLM_CONFIG
from modules.rag_engine import RAGEngine
from modules.quiz_engine import QuizEngine
from modules.diagnosis import DiagnosisEngine
from utils.helpers import log


def _extract_number(text: str, default: int = 3) -> int:
    """从用户输入中提取数字，如'出5道题'→5，'做3道'→3"""
    # 匹配中文数字词
    cn_num_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    for cn, val in cn_num_map.items():
        if cn in text:
            return val
    # 匹配阿拉伯数字
    m = re.search(r"(\d+)\s*[道题个张]", text)
    if m:
        n = int(m.group(1))
        return max(1, min(n, 10))  # 限制 1-10
    m = re.search(r"(\d+)", text)
    if m:
        n = int(m.group(1))
        return max(1, min(n, 10))
    return default


class ChatAgent:
    """沈航智学对话 Agent"""

    def __init__(self, kb_manager, rag_engine: RAGEngine, vault,
                 llm_config: dict = None):
        self.kb = kb_manager
        self.rag = rag_engine
        self.vault = vault

        cfg = llm_config or LLM_CONFIG
        self._llm_config = cfg
        self.llm = ChatOpenAI(
            base_url=cfg["base_url"],
            api_key=cfg["api_key"],
            model=cfg["model"],
            temperature=cfg.get("temperature", 0.4),
            max_tokens=cfg.get("max_tokens", 2048),
        )

        self.quiz_engine = QuizEngine(self.llm)
        self.diagnosis_engine = DiagnosisEngine(self.llm)

        self._active_kb_ids = []
        self._last_quiz = None
        self._last_context = ""
        self._chat_history: list[dict] = []  # 多轮对话记忆
        self._cached_agent = None
        self._cached_tools_kb_ids = None  # 用于判断 agent 是否需要重建

    def reconfigure(self, llm_config: dict):
        """运行时切换 LLM 供应商/模型，无需重启应用"""
        self._llm_config = dict(llm_config)
        self.llm = ChatOpenAI(
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            model=llm_config["model"],
            temperature=llm_config.get("temperature", 0.4),
            max_tokens=llm_config.get("max_tokens", 2048),
        )
        self.quiz_engine = QuizEngine(self.llm)
        self.diagnosis_engine = DiagnosisEngine(self.llm)
        self._cached_agent = None  # LangChain agent 缓存失效

    def set_active_kbs(self, kb_ids: list[str]):
        self._active_kb_ids = kb_ids

    # ---- 工具定义 ----
    def _make_tools(self):
        agent_self = self

        @tool
        def search_knowledge_base(query: str) -> str:
            """
            在用户已选中的知识库中搜索相关知识点。当你需要查阅用户上传的课件、教材、笔记来回答问题时，调用此工具。
            参数 query: 中文搜索查询，用关键词描述你要查的内容。
            """
            if not agent_self._active_kb_ids:
                return "⚠️ 当前未选择任何知识库。请在左侧知识空间面板中勾选要使用的知识库。"
            docs, sources = agent_self.rag.query(query, agent_self._active_kb_ids)
            agent_self._last_context = "\n\n".join([d["content"] for d in docs])
            context = agent_self.rag.format_context(docs)
            source_text = agent_self.rag.format_sources(sources)
            return context + source_text

        @tool
        def generate_quiz(num_questions: int = 3) -> str:
            """
            基于当前对话上下文和知识库内容，生成测验题。题型包含选择题和简答题。
            参数 num_questions: 题目数量，默认 3 道。
            """
            context = agent_self._last_context
            if not context and agent_self._active_kb_ids:
                # 自动从知识库检索上下文
                docs, _ = agent_self.rag.query("", agent_self._active_kb_ids, top_k_per_kb=4)
                context = "\n\n".join([d["content"] for d in docs])
            if not context:
                return "⚠️ 请先选择知识库，或通过 search_knowledge_base 检索相关知识点。"
            quiz = agent_self.quiz_engine.generate_quiz(context, num_questions)
            agent_self._last_quiz = quiz
            agent_self.vault.increment_quiz_count()
            return f"📝 **测验已生成**\n\n```json\n{str(quiz)[:3000]}\n```\n\n请在前端测验卡片中作答。每道题作答后会自动批改。"

        @tool
        def generate_flashcards(num_cards: int = 5) -> str:
            """
            基于当前知识库内容生成知识闪卡。每张闪卡包含正面（核心概念）和反面（详细解释）。
            参数 num_cards: 闪卡数量，默认 5 张。
            """
            context = agent_self._last_context
            if not context and agent_self._active_kb_ids:
                docs, _ = agent_self.rag.query("", agent_self._active_kb_ids, top_k_per_kb=4)
                context = "\n\n".join([d["content"] for d in docs])
            if not context:
                return "⚠️ 请先选择知识库，或通过 search_knowledge_base 检索相关知识点。"
            cards = agent_self.quiz_engine.generate_flashcards(context, num_cards)
            agent_self.vault.add_flashcards(cards)
            return f"✅ 已生成 {len(cards)} 张知识闪卡，已存入复习智库。\n\n```json\n{str(cards)[:2000]}\n```"

        @tool
        def analyze_weakness() -> str:
            """
            分析学生当前的薄弱知识点。基于对话历史和测验结果进行认知诊断。
            """
            diagnosis = agent_self.diagnosis_engine.analyze_weakness(agent_self._chat_history)
            agent_self.vault.add_diagnosis(diagnosis)
            # 生成学习航线
            path = agent_self.diagnosis_engine.generate_learning_path(diagnosis)
            agent_self.vault.add_learning_path(path)
            return f"📊 **认知诊断报告**\n\n```json\n{str(diagnosis)[:2000]}\n```\n\n{path}"

        @tool
        def generate_quick_summary(kb_name: str = "") -> str:
            """
            为一键生成当前知识库的速查摘要（核心概念 + 必会公式 + 常见误区）。
            参数 kb_name: 知识空间名称（可选，不填则使用当前检索上下文）
            """
            context = agent_self._last_context
            if not context and agent_self._active_kb_ids:
                docs, _ = agent_self.rag.query("", agent_self._active_kb_ids, top_k_per_kb=4)
                context = "\n\n".join([d["content"] for d in docs])
            name = kb_name or "当前知识库"
            if not context:
                return "⚠️ 请先选择知识库，或通过 search_knowledge_base 检索相关知识点。"
            summary = agent_self.quiz_engine.generate_quick_summary(context, name)
            agent_self.vault.add_quick_summary(summary, name)
            return f"⚡ **「{name}」速查摘要**\n\n```json\n{str(summary)[:2000]}\n```"

        @tool
        def generate_podcast() -> str:
            """
            生成一段师生对话式知识播客脚本，覆盖当前知识库的核心内容。
            """
            context = agent_self._last_context
            if not context and agent_self._active_kb_ids:
                docs, _ = agent_self.rag.query("", agent_self._active_kb_ids, top_k_per_kb=4)
                context = "\n\n".join([d["content"] for d in docs])
            if not context:
                return "⚠️ 请先选择知识库，或通过 search_knowledge_base 检索相关知识点。"
            script = agent_self.quiz_engine.generate_podcast_script(context, "当前知识库")
            return script

        return [
            search_knowledge_base,
            generate_quiz,
            generate_flashcards,
            analyze_weakness,
            generate_quick_summary,
            generate_podcast,
        ]

    # ---- 对话接口 ----
    def invoke(self, query: str, chat_history: list = None) -> dict:
        """
        执行对话（支持多轮记忆 + 工具意图直通）

        返回：{"response": str, "sources": list, "quiz": dict, "flashcards": list, ...}
        """
        # ── 意图预检测：工具类请求直接执行，不走 Agent ──
        force_tool = self._detect_intent(query)
        if force_tool:
            return self._invoke_tool_direct(force_tool, query)

        # ── 通用对话：走 Agent（含 search_knowledge_base）──
        return self._invoke_agent(query)

    def _detect_intent(self, query: str) -> str | None:
        """检测用户意图，返回工具名或 None（支持中英文关键词）"""
        ql = query.lower()
        intent_map = [
            (["出题", "测验", "考考", "测试", "出几道", "考题", "做题", "来几道", "做几道",
              "quiz", "test me", "give me question", "exam"], "generate_quiz"),
            (["闪卡", "卡片", "制作卡", "知识卡",
              "flashcard", "card"], "generate_flashcards"),
            (["薄弱", "诊断", "分析我的", "哪里没学好", "学习分析", "我的问题在哪",
              "weakness", "diagnos", "analyze my", "where am i weak"], "analyze_weakness"),
            (["速查", "总结重点", "核心概念", "摘要", "知识库总结", "帮我总结", "总结一下",
              "summary", "summarize", "key concept", "cheat sheet", "recap"], "generate_quick_summary"),
            (["播客", "对话讲解", "对话形式", "师生对话",
              "podcast", "dialogue", "conversation style"], "generate_podcast"),
        ]
        for keywords, tool_name in intent_map:
            if any(kw in ql for kw in keywords):
                return tool_name
        return None

    def _invoke_tool_direct(self, tool_name: str, user_query: str) -> dict:
        """
        直接执行工具意图 — 更可靠、更快，不依赖 LLM 的工具调用判断
        """
        # 先检索上下文
        context = self._last_context
        if not context and self._active_kb_ids:
            docs, _ = self.rag.query("", self._active_kb_ids, top_k_per_kb=4)
            context = "\n\n".join([d["content"] for d in docs])
            self._last_context = context

        # 提取参数（如出题数量）
        num = _extract_number(user_query, default=3)

        if tool_name == "generate_quiz":
            if not context:
                return {"response": "⚠️ 请先在「知识空间」中勾选要使用的知识库，然后重试。", "quiz": None}
            quiz = self.quiz_engine.generate_quiz(context, num)
            self._last_quiz = quiz
            self.vault.increment_quiz_count()
            n = len(quiz.get("questions", []))
            response = f"📝 已为你从知识库中生成 **{n}** 道测验题，请在下方答题卡中作答。每题作答后可查看参考答案。"
            self._save_history(user_query, response)
            return {"response": response, "quiz": quiz}

        elif tool_name == "generate_flashcards":
            if not context:
                return {"response": "⚠️ 请先在「知识空间」中勾选要使用的知识库，然后重试。", "flashcards": []}
            cards = self.quiz_engine.generate_flashcards(context, num)
            kb_names = [self.kb.get_kb_info(kid)["name"] for kid in self._active_kb_ids if self.kb.get_kb_info(kid)]
            self.vault.add_flashcards(cards, " · ".join(kb_names))
            response = f"🃏 已生成 **{len(cards)}** 张知识闪卡，已存入「复习智库 → 闪卡集」。\n\n前往复习智库翻阅闪卡，点击卡片即可翻转查看答案。"
            self._save_history(user_query, response)
            return {"response": response, "flashcards": cards}

        elif tool_name == "analyze_weakness":
            diagnosis = self.diagnosis_engine.analyze_weakness(self._chat_history)
            self.vault.add_diagnosis(diagnosis)
            path = self.diagnosis_engine.generate_learning_path(diagnosis)
            self.vault.add_learning_path(path)
            weak_count = len(diagnosis.get("weak_points", []))
            strong_count = len(diagnosis.get("strong_points", []))
            gap_count = len(diagnosis.get("gaps", []))
            response = f"📊 **认知诊断报告**\n\n{diagnosis.get('overall_assessment', '')}\n\n"
            response += f"🟢 已掌握 **{strong_count}** 项 | 🟡 薄弱 **{weak_count}** 项 | 🔴 未覆盖 **{gap_count}** 项\n\n"
            response += f"🧭 学习航线已同步生成，前往「复习智库 → 学习航线」查看。"
            self._save_history(user_query, response)
            return {"response": response, "diagnosis": diagnosis, "learning_path": path}

        elif tool_name == "generate_quick_summary":
            if not context:
                return {"response": "⚠️ 请先在「知识空间」中勾选要使用的知识库，然后重试。", "summary": None}
            kb_names = [self.kb.get_kb_info(kid)["name"] for kid in self._active_kb_ids if self.kb.get_kb_info(kid)]
            kb_name_str = " · ".join(kb_names) if kb_names else "当前知识库"
            summary = self.quiz_engine.generate_quick_summary(context, kb_name_str)
            self.vault.add_quick_summary(summary, kb_name_str)
            concepts = summary.get("core_concepts", [])
            formulas = summary.get("key_formulas", [])
            mistakes = summary.get("common_mistakes", [])
            response = f"⚡ **「{kb_name_str}」速查摘要**\n\n"
            response += f"🔑 核心概念 × {len(concepts)} | 📐 公式 × {len(formulas)} | ⚠️ 误区 × {len(mistakes)}\n\n"
            if summary.get("suggested_review"):
                response += f"💡 {summary['suggested_review']}"
            self._save_history(user_query, response)
            return {"response": response, "summary": summary}

        elif tool_name == "generate_podcast":
            if not context:
                return {"response": "⚠️ 请先在「知识空间」中勾选要使用的知识库，然后重试。", "podcast": None}
            kb_names = [self.kb.get_kb_info(kid)["name"] for kid in self._active_kb_ids if self.kb.get_kb_info(kid)]
            kb_name_str = " · ".join(kb_names) if kb_names else "当前知识库"
            script = self.quiz_engine.generate_podcast_script(context, kb_name_str)
            response = f"🎙️ 已生成「{kb_name_str}」的知识播客脚本：\n\n{script}"
            self._save_history(user_query, response)
            return {"response": response, "podcast": script}

        return {"response": "抱歉，处理请求时遇到了问题。"}

    def _invoke_agent(self, query: str) -> dict:
        """通用对话 — 走 LangChain Agent（主要用于 search_knowledge_base）"""
        # 仅在 KB 选择变化时重建 agent
        kb_sig = tuple(sorted(self._active_kb_ids))
        if self._cached_agent is None or self._cached_tools_kb_ids != kb_sig:
            tools = self._make_tools()
            system_prompt = self._build_system_prompt()
            self._cached_agent = create_agent(
                model=self.llm,
                tools=tools,
                system_prompt=system_prompt,
            )
            self._cached_tools_kb_ids = kb_sig
        agent = self._cached_agent

        input_messages = []
        for hist_msg in self._chat_history[-20:]:
            role = hist_msg.get("role", "user")
            content = hist_msg.get("content", "")
            if role == "user":
                input_messages.append(HumanMessage(content=content))
            else:
                from langchain_core.messages import AIMessage
                input_messages.append(AIMessage(content=content))
        input_messages.append(HumanMessage(content=query))

        try:
            result = agent.invoke({"messages": input_messages})
            messages = result.get("messages", [])
            response_text = ""
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.__class__.__name__ == "AIMessage":
                    response_text = msg.content
                    break
            if not response_text and messages:
                response_text = str(messages[-1].content)
        except Exception as e:
            response_text = f"❌ 处理时遇到问题：{str(e)[:300]}"

        self._save_history(query, response_text)
        return {
            "response": response_text,
            "quiz": self._last_quiz,
        }

    def _build_system_prompt(self) -> str:
        return f"""你是「沈航智学 AeroTutor」——一个专为沈阳航空航天大学学生打造的 AI 自适应学习助教。

## 你的定位
- 你不仅回答问题，更能管理多个知识空间、生成测验、制作闪卡、诊断学习薄弱点
- 你具有 NotebookLM 风格的多知识库隔离能力
- 你的回答风格专业但不失亲和，像一位热心的学长/学姐

## 你可以使用的工具
1. **search_knowledge_base**: 当用户的问题需要从课件/教材/笔记中查找时使用
2. **generate_quiz**: 当用户要求"出题"、"测验"、"考考我"时使用
3. **generate_flashcards**: 当用户要求"做闪卡"、"制作卡片"时使用
4. **analyze_weakness**: 当用户要求"分析薄弱点"、"看看哪里没学好"时使用
5. **generate_quick_summary**: 当用户要求"速查"、"总结重点"、"核心概念"时使用
6. **generate_podcast**: 当用户要求"播客"、"对话讲解"时使用

## 航空航天特色
- 你可以用航空航天比喻来解释概念（如"学习就像飞行前的 check list"）
- 对沈航的课程特点有一定了解（飞行原理、空气动力学、航空发动机等）

## 输出规范
- 使用 Markdown 格式，增强可读性
- 引用知识库内容时，提及来源文件名
- 回答末尾可以根据情况推荐下一步操作（做测验 / 生成闪卡 / 查看速查摘要）
- 注意：用户要求出题、做闪卡等操作时，直接调用对应的工具"""

    def _save_history(self, user_msg: str, assistant_msg: str):
        self._chat_history.append({"role": "user", "content": user_msg})
        self._chat_history.append({"role": "assistant", "content": assistant_msg})
        if len(self._chat_history) > 60:
            self._chat_history = self._chat_history[-60:]
