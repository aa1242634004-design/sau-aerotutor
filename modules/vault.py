"""
模块 E：复习智库 (Review Vault)
- 错题本 + 闪卡集 + 诊断报告 + 学习航线
- 优化⑤：复习统计（连续天数、完成次数等）
"""
import json
import os
import time

VAULT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vault_data.json")


class ReviewVault:
    """复习智库"""

    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(VAULT_FILE):
            with open(VAULT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "wrong_answers": [],     # 错题本
            "flashcards": [],        # 闪卡集
            "diagnoses": [],         # 诊断报告历史
            "learning_paths": [],    # 学习航线历史
            "quick_summaries": [],   # 速查摘要历史
            "stats": {               # 学习统计
                "review_days": {},
                "total_quizzes": 0,
                "total_cards_reviewed": 0,
            },
        }

    def _save(self):
        with open(VAULT_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # ---- 错题本 ----
    def add_wrong_answer(self, question: str, student_answer: str,
                         correct_answer: str, topic: str, explanation: str):
        self._data["wrong_answers"].append({
            "id": len(self._data["wrong_answers"]) + 1,
            "question": question,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "topic": topic,
            "explanation": explanation,
            "review_count": 0,
            "added_at": time.strftime("%Y-%m-%d %H:%M"),
            "last_reviewed": "",
        })
        self._save()

    def get_wrong_answers(self) -> list[dict]:
        return sorted(self._data["wrong_answers"], key=lambda w: w["added_at"], reverse=True)

    def mark_reviewed(self, answer_id: int):
        for a in self._data["wrong_answers"]:
            if a["id"] == answer_id:
                a["review_count"] += 1
                a["last_reviewed"] = time.strftime("%Y-%m-%d %H:%M")
                break
        self._record_review_day()
        self._save()

    # ---- 闪卡 ----
    def add_flashcards(self, cards: list[dict], kb_name: str = ""):
        for card in cards:
            self._data["flashcards"].append({
                "front": card.get("front", ""),
                "back": card.get("back", ""),
                "topic": card.get("topic", ""),
                "source_kb": kb_name,
                "review_count": 0,
                "added_at": time.strftime("%Y-%m-%d %H:%M"),
            })
        self._save()

    def get_flashcards(self) -> list[dict]:
        return self._data["flashcards"][-50:]  # 最近 50 张

    def mark_card_reviewed(self, idx: int):
        cards = self._data["flashcards"]
        if 0 <= idx < len(cards):
            cards[idx]["review_count"] = cards[idx].get("review_count", 0) + 1
            self._data["total_cards_reviewed"] = self._data["stats"].get("total_cards_reviewed", 0) + 1
        self._record_review_day()
        self._save()

    # ---- 诊断报告 ----
    def add_diagnosis(self, diagnosis: dict):
        self._data["diagnoses"].append({
            "data": diagnosis,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
        })
        # 只保留最近 10 次
        self._data["diagnoses"] = self._data["diagnoses"][-10:]
        self._save()

    def get_latest_diagnosis(self) -> dict:
        if self._data["diagnoses"]:
            return self._data["diagnoses"][-1]
        return {}

    # ---- 学习航线 ----
    def add_learning_path(self, path_text: str):
        self._data["learning_paths"].append({
            "content": path_text,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
        })
        self._data["learning_paths"] = self._data["learning_paths"][-5:]
        self._save()

    def get_latest_path(self) -> dict:
        if self._data["learning_paths"]:
            return self._data["learning_paths"][-1]
        return {}

    # ---- 速查摘要 ----
    def add_quick_summary(self, summary: dict, kb_name: str):
        self._data["quick_summaries"].append({
            "data": summary,
            "kb_name": kb_name,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
        })
        self._data["quick_summaries"] = self._data["quick_summaries"][-10:]
        self._save()

    # ---- 统计 ----
    def increment_quiz_count(self):
        self._data["stats"]["total_quizzes"] = \
            self._data["stats"].get("total_quizzes", 0) + 1
        self._save()

    def _record_review_day(self):
        today = time.strftime("%Y-%m-%d")
        self._data["stats"]["review_days"][today] = True
        self._save()

    def get_stats(self) -> dict:
        stats = self._data["stats"]
        review_days = sorted(stats.get("review_days", {}).keys())
        streak = 0
        today = time.strftime("%Y-%m-%d")

        if review_days:
            from datetime import datetime, timedelta
            # 从今天开始往回数连续天数
            check_date = datetime.strptime(today, "%Y-%m-%d")
            # 如果今天还没复习，从昨天开始算（允许今天稍后复习）
            if today not in stats.get("review_days", {}):
                check_date = check_date - timedelta(days=1)

            review_set = set(review_days)
            while True:
                day_str = check_date.strftime("%Y-%m-%d")
                if day_str in review_set:
                    streak += 1
                    check_date = check_date - timedelta(days=1)
                else:
                    break

        return {
            "streak_days": streak,
            "total_quizzes": stats.get("total_quizzes", 0),
            "total_cards_reviewed": stats.get("total_cards_reviewed", 0),
            "wrong_count": len(self._data["wrong_answers"]),
            "flashcard_count": len(self._data["flashcards"]),
            "diagnosis_count": len(self._data["diagnoses"]),
        }
