import time
import hashlib
import json
import os
from typing import Optional, Any, Dict

class SearchCache:
    _memory_cache: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def _make_key(query: str, language: str = "auto", mode: str = "normal") -> str:
        raw = f"{query.strip().lower()}_{language}_{mode}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    @classmethod
    def get(cls, query: str, language: str = "auto", mode: str = "normal") -> Optional[Dict[str, Any]]:
        key = cls._make_key(query, language, mode)
        if key in cls._memory_cache:
            entry = cls._memory_cache[key]
            if time.time() < entry["expire_at"]:
                return entry["data"]
            else:
                del cls._memory_cache[key]
        return None

    @classmethod
    def set(cls, query: str, data: Dict[str, Any], language: str = "auto", mode: str = "normal", ttl_seconds: int = 3600):
        key = cls._make_key(query, language, mode)
        cls._memory_cache[key] = {
            "data": data,
            "expire_at": time.time() + ttl_seconds
        }

    @classmethod
    def clear(cls):
        cls._memory_cache.clear()
