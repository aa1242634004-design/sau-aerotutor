"""
模块 A：动态知识空间管理 (NotebookLM 风格)
- 创建/删除独立 ChromaDB collection
- 文件上传解析 (PDF/docx/txt)
- 精准 CRUD（通过 collection metadata filter）
"""
import os
import hashlib
import json
import time
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

from config import CHROMA_CONFIG, EMBEDDING_CONFIG
from utils.helpers import log

COLLECTION_PREFIX = "kb_"
META_FILE = os.path.join(CHROMA_CONFIG["persist_directory"], "kb_meta.json")


class KnowledgeBaseManager:
    """多知识空间管理器"""

    def __init__(self):
        os.makedirs(CHROMA_CONFIG["persist_directory"], exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=CHROMA_CONFIG["persist_directory"],
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._embeddings = None

    def _get_embeddings(self):
        if self._embeddings:
            return self._embeddings
        if EMBEDDING_CONFIG["provider"] == "openai":
            self._embeddings = OpenAIEmbeddings(
                model=EMBEDDING_CONFIG["model"],
                api_key=EMBEDDING_CONFIG["api_key"],
                base_url=EMBEDDING_CONFIG["base_url"],
            )
        else:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=f"sentence-transformers/{EMBEDDING_CONFIG['model']}",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embeddings

    def _col_name(self, kb_id: str) -> str:
        return f"{COLLECTION_PREFIX}{kb_id}"

    # ---- 元数据持久化 ----
    def _load_meta(self) -> dict:
        if os.path.exists(META_FILE):
            with open(META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_meta(self, meta: dict):
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    # ---- 知识空间 CRUD ----
    def list_kbs(self) -> list[dict]:
        """列出所有知识空间"""
        meta = self._load_meta()
        kbs = []
        for kb_id, info in meta.items():
            col = self._client.get_collection(self._col_name(kb_id))
            kbs.append({
                "id": kb_id,
                "name": info.get("name", kb_id),
                "description": info.get("description", ""),
                "category": info.get("category", "other"),
                "doc_count": col.count(),
                "created_at": info.get("created_at", ""),
            })
        return sorted(kbs, key=lambda k: k["created_at"], reverse=True)

    def create_kb(self, name: str, description: str = "", category: str = "other") -> str:
        """创建新知识空间"""
        kb_id = hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:12]
        self._client.create_collection(
            name=self._col_name(kb_id),
            metadata={"hnsw:space": "cosine", "kb_name": name, "kb_category": category},
        )
        meta = self._load_meta()
        meta[kb_id] = {
            "name": name,
            "description": description,
            "category": category,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
        }
        self._save_meta(meta)
        log("info", f"创建知识空间: {name} ({kb_id})")
        return kb_id

    def delete_kb(self, kb_id: str):
        """删除知识空间"""
        try:
            self._client.delete_collection(self._col_name(kb_id))
        except Exception:
            pass
        meta = self._load_meta()
        meta.pop(kb_id, None)
        self._save_meta(meta)
        log("info", f"删除知识空间: {kb_id}")

    def get_kb_info(self, kb_id: str) -> Optional[dict]:
        """获取单个知识空间信息"""
        meta = self._load_meta()
        if kb_id not in meta:
            return None
        info = meta[kb_id]
        col = self._client.get_collection(self._col_name(kb_id))
        info["doc_count"] = col.count()
        info["id"] = kb_id
        return info

    # ---- 文件操作 ----
    def list_files(self, kb_id: str) -> list[dict]:
        """列出知识空间中的所有文件"""
        try:
            col = self._client.get_collection(self._col_name(kb_id))
            if col.count() == 0:
                return []
            data = col.get(include=["metadatas"])
            file_set = {}
            for meta in data.get("metadatas", []):
                if meta is None:
                    continue
                fname = meta.get("file_name", "unknown")
                if fname not in file_set:
                    file_set[fname] = {
                        "file_name": fname,
                        "chunk_count": 0,
                        "uploaded_at": meta.get("uploaded_at", ""),
                    }
                file_set[fname]["chunk_count"] += 1
            return sorted(file_set.values(), key=lambda f: f["uploaded_at"], reverse=True)
        except Exception:
            return []

    def add_file(self, kb_id: str, file_name: str, text: str) -> int:
        """添加文件内容到知识空间"""
        col = self._client.get_collection(self._col_name(kb_id))
        emb = self._get_embeddings()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        )
        chunks = splitter.split_text(text)
        if not chunks:
            return 0

        uploaded_at = time.strftime("%Y-%m-%d %H:%M")
        ids, embeddings, metadatas, documents = [], [], [], []

        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{kb_id}_{file_name}_{i}_{chunk[:30]}".encode()).hexdigest()
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "file_name": file_name,
                "chunk_index": i,
                "uploaded_at": uploaded_at,
                "kb_id": kb_id,
            })

        # 批量向量化
        batch_size = 50
        for start in range(0, len(chunks), batch_size):
            end = min(start + batch_size, len(chunks))
            batch_vectors = emb.embed_documents(documents[start:end])
            col.upsert(
                ids=ids[start:end],
                embeddings=batch_vectors,
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

        log("info", f"添加文件: {file_name} → {len(chunks)} chunks (kb={kb_id})")
        return len(chunks)

    def delete_file(self, kb_id: str, file_name: str):
        """从知识空间中删除指定文件的所有向量"""
        col = self._client.get_collection(self._col_name(kb_id))
        if col.count() == 0:
            return
        data = col.get(include=["metadatas"])
        delete_ids = []
        for doc_id, meta in zip(data["ids"], data.get("metadatas", [])):
            if meta and meta.get("file_name") == file_name:
                delete_ids.append(doc_id)
        if delete_ids:
            col.delete(ids=delete_ids)
            log("info", f"删除文件: {file_name} ({len(delete_ids)} chunks)")

    def get_collection(self, kb_id: str):
        """获取 ChromaDB collection 对象（供 RAG 引擎使用）"""
        return self._client.get_collection(self._col_name(kb_id))

    def get_embedding_function(self):
        """获取 embedding 函数"""
        return self._get_embeddings()
