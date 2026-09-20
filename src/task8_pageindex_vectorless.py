"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
LANDING_LEGAL_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
PAGEINDEX_CACHE = Path(__file__).parent.parent / "pageindex_ids.json"
PAGEINDEX_TIMEOUT = float(os.getenv("PAGEINDEX_TIMEOUT", "30"))


def _read_cache() -> dict[str, str]:
    if not PAGEINDEX_CACHE.exists():
        return {}
    try:
        value = json.loads(PAGEINDEX_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_cache(cache: dict[str, str]) -> None:
    PAGEINDEX_CACHE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        return
    from pageindex import PageIndexClient

    cache = _read_cache()
    client = PageIndexClient(PAGEINDEX_API_KEY)
    for path in sorted(LANDING_LEGAL_DIR.glob("*.pdf")):
        if path.name in cache:
            continue
        response = client.submit_document(str(path))
        doc_id = response.get("doc_id") if isinstance(response, dict) else None
        if not doc_id:
            raise RuntimeError(f"PageIndex response has no doc_id for {path.name}")
        cache[path.name] = str(doc_id)
        _write_cache(cache)


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not PAGEINDEX_API_KEY or not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []
    from pageindex import PageIndexClient

    try:
        upload_documents()
        cache = _read_cache()
        client = PageIndexClient(PAGEINDEX_API_KEY)
        results = []
        for source, doc_id in cache.items():
            submitted = client.submit_query(doc_id, query)
            retrieval_id = submitted.get("retrieval_id") if isinstance(submitted, dict) else None
            if not retrieval_id:
                continue
            deadline = time.monotonic() + PAGEINDEX_TIMEOUT
            retrieval = {}
            while time.monotonic() < deadline:
                retrieval = client.get_retrieval(str(retrieval_id))
                if retrieval.get("status") in {"completed", "success", "failed"}:
                    break
                if any(key in retrieval for key in ("nodes", "results", "answer", "data")):
                    break
                time.sleep(1)
            for item in _extract_items(retrieval):
                content = item.get("content") or item.get("text") or item.get("markdown")
                if not isinstance(content, str) or not content.strip():
                    continue
                score = item.get("score")
                if not isinstance(score, (int, float)):
                    score = 1.0 / (len(results) + 1)
                results.append({
                    "id": f"pageindex:{doc_id}:{len(results)}",
                    "content": content.strip(),
                    "score": float(score),
                    "metadata": {
                        "source": source,
                        "title": Path(source).stem,
                        "doc_type": "legal",
                        "url": None,
                        "chunk_index": len(results),
                    },
                    "retrieval_method": "pageindex",
                })
        return sorted(results, key=lambda item: (-item["score"], item["id"]))[:top_k]
    except Exception:
        return []


def _extract_items(value: object) -> list[dict]:
    """Find result-like dictionaries across PageIndex response variants."""
    found: list[dict] = []
    if isinstance(value, dict):
        if any(key in value for key in ("content", "text", "markdown")):
            found.append(value)
        for child in value.values():
            found.extend(_extract_items(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_extract_items(child))
    return found


if __name__ == "__main__":
    upload_documents()
