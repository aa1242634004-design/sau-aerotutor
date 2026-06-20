"""
模块 B：RAG 检索引擎 (FAISS 版)
- 根据 active_kb_ids 多索引联合查询
- 返回结果带来源标注（优化①：答案溯源）
"""
from modules.kb_manager import KnowledgeBaseManager


class RAGEngine:
    """多知识空间联合检索引擎"""

    def __init__(self, kb_manager: KnowledgeBaseManager):
        self.kb = kb_manager

    def query(
        self,
        query_text: str,
        active_kb_ids: list[str],
        top_k_per_kb: int = 5,
    ) -> tuple[list[dict], list[dict]]:
        """
        多知识空间联合检索
        返回：(检索结果列表, 来源信息列表)
        """
        emb = self.kb.get_embedding_function()
        query_vector = emb.embed_query(query_text)

        all_docs = []
        sources = []

        for kb_id in active_kb_ids:
            try:
                index = self.kb.get_collection(kb_id)
                # FAISS similarity_search_with_score_by_vector
                results = index.similarity_search_with_score_by_vector(
                    query_vector, k=min(top_k_per_kb, 20)
                )

                kb_info = self.kb.get_kb_info(kb_id)
                kb_name = kb_info["name"] if kb_info else kb_id

                for doc, score in results:
                    if doc.page_content == "__init__":
                        continue  # 跳过分隔占位文档
                    meta = doc.metadata
                    file_name = meta.get("file_name", "未知")
                    # FAISS 返回的是 L2 距离，越小越相似；转为 0-1 分数
                    normalized_score = round(1.0 / (1.0 + score), 3)

                    all_docs.append({
                        "content": doc.page_content,
                        "kb_name": kb_name,
                        "kb_id": kb_id,
                        "file_name": file_name,
                        "score": normalized_score,
                    })

                    # 收集来源
                    if file_name not in [s["file_name"] for s in sources]:
                        sources.append({
                            "kb_name": kb_name,
                            "file_name": file_name,
                            "kb_id": kb_id,
                        })
            except Exception as e:
                continue

        # 按得分降序排列
        all_docs.sort(key=lambda d: d["score"], reverse=True)
        return all_docs[:12], sources[:8]

    def format_context(self, docs: list[dict]) -> str:
        """格式化检索结果为 LLM 上下文 + 来源标注"""
        if not docs:
            return "未在已选知识库中找到相关信息。"

        parts = []
        for i, doc in enumerate(docs):
            parts.append(
                f"[来源{i+1}] 知识库「{doc['kb_name']}」· {doc['file_name']}\n"
                f"{doc['content']}"
            )
        return "\n\n".join(parts)

    def format_sources(self, sources: list[dict]) -> str:
        """格式化来源列表"""
        if not sources:
            return ""
        lines = ["\n\n📎 **答案溯源**"]
        for s in sources:
            lines.append(f"• 「{s['kb_name']}」— {s['file_name']}")
        return "\n".join(lines)
