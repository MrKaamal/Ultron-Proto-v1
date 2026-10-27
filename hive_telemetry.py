# src/memory/engram_store.py
import hashlib
import json
import math
import sqlite3
import time
from typing import Dict, List


class EngramStore:
    def __init__(self, db_path: str = "ultron_engrams.db", dim: int = 128):
        self.db_path = db_path
        self.dim = dim
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS engrams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    category TEXT,
                    content TEXT,
                    embedding TEXT
                )
            """)
            conn.commit()

    def _embed_text(self, text: str) -> List[float]:
        """Deterministic lightweight local vector embedding using character & word n-gram hashing."""
        vec = [0.0] * self.dim
        tokens = text.lower().split()
        for token in tokens:
            for n in (2, 3, len(token)):
                for i in range(max(1, len(token) - n + 1)):
                    sub = token[i : i + n]
                    h = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16)
                    idx = h % self.dim
                    sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
                    vec[idx] += sign

        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 5) for x in vec]

    @staticmethod
    def _cosine_sim(v1: List[float], v2: List[float]) -> float:
        return sum(a * b for a, b in zip(v1, v2))

    def store_engram(self, category: str, content: str) -> int:
        vec = self._embed_text(f"{category} {content}")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO engrams (timestamp, category, content, embedding) VALUES (?, ?, ?, ?)",
                (time.time(), category, content, json.dumps(vec)),
            )
            conn.commit()
            return cur.lastrowid

    def recall(self, query: str, top_k: int = 3) -> List[Dict]:
        q_vec = self._embed_text(query)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, timestamp, category, content, embedding FROM engrams"
            ).fetchall()

        scored = []
        for r_id, ts, cat, content, emb_json in rows:
            emb = json.loads(emb_json)
            score = self._cosine_sim(q_vec, emb)
            scored.append({
                "id": r_id,
                "category": cat,
                "content": content,
                "similarity": round(score, 4),
                "timestamp": ts,
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]
