import os
import requests
from typing import Dict, Any, List, Optional

class BackendApiClient:
    """
    Centralized Backend API Client for Desktop PC Application (Phase 7).
    Communicates with FastAPI backend at /api/v1.
    """
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DouyinSmartSearchPC/2.0"})

    def set_base_url(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    # 1. Smart Search (Vietnamese / Chinese / English)
    def smart_search(
        self,
        query: str,
        language: str = "auto",
        mode: str = "normal",
        custom_queries: Optional[List[str]] = None,
        min_score: float = 60.0,
        min_likes: int = 0,
        sort_by: str = "similarity"
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/search"
        payload = {
            "query": query,
            "language": language,
            "mode": mode,
            "custom_queries": custom_queries,
            "min_score": min_score,
            "min_likes": min_likes,
            "sort_by": sort_by
        }
        r = self.session.post(url, json=payload, timeout=45)
        r.raise_for_status()
        return r.json()

    # 2. Query Translate & Keywords Preview
    def translate_query(self, query: str, language: str = "auto", mode: str = "normal") -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/query/translate"
        payload = {"query": query, "language": language, "mode": mode}
        r = self.session.post(url, json=payload, timeout=20)
        r.raise_for_status()
        return r.json()

    # 3. Analyze Video File
    def analyze_video_file(self, file_path: str, user_hint: str = "", deep_search: bool = False) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/analyze/video"
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "video/mp4")}
            data = {"user_hint": user_hint, "deep_search": str(deep_search).lower()}
            r = self.session.post(url, files=files, data=data, timeout=60)
        r.raise_for_status()
        return r.json()

    # 4. Analyze Douyin / TikTok URL
    def analyze_url(self, douyin_url: str, user_hint: str = "", deep_search: bool = False) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/analyze/url"
        payload = {"url": douyin_url, "user_hint": user_hint, "deep_search": deep_search}
        r = self.session.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    # 5. Get Job Progress
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/jobs/{job_id}"
        r = self.session.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    # 6. Get Ranked Results
    def get_job_results(
        self,
        job_id: str,
        page: int = 1,
        page_size: int = 50,
        min_score: float = 60.0,
        sort_by: str = "similarity"
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/search/{job_id}/results"
        params = {
            "page": page,
            "page_size": page_size,
            "min_score": min_score,
            "sort_by": sort_by
        }
        r = self.session.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    # 7. Search History
    def get_history(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/history"
        r = self.session.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("history", [])

    # 8. Settings
    def get_settings(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/settings"
        r = self.session.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    def update_settings(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/settings"
        r = self.session.put(url, json=settings_dict, timeout=10)
        r.raise_for_status()
        return r.json()
