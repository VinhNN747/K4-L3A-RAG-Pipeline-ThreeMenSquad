"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

import json
import os
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    setup_directory()
    raw_sources = os.getenv("LEGAL_SOURCES_JSON", "")
    if not raw_sources.strip():
        print("No LEGAL_SOURCES_JSON configured; keeping existing legal corpus.")
        return
    try:
        sources = json.loads(raw_sources)
    except json.JSONDecodeError as error:
        raise ValueError("LEGAL_SOURCES_JSON must be a JSON object") from error
    if not isinstance(sources, dict):
        raise ValueError("LEGAL_SOURCES_JSON must map filenames to URLs")

    import requests

    for filename, url in sources.items():
        if not isinstance(filename, str) or not isinstance(url, str) or not url.strip():
            raise ValueError("legal source entries require a filename and URL")
        destination = DATA_DIR / Path(filename).name
        if destination.exists() and destination.stat().st_size > 1024:
            print(f"Exists: {destination}")
            continue
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        if not response.content:
            raise RuntimeError(f"Empty response for {url}")
        destination.write_bytes(response.content)
        print(f"Downloaded: {destination}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
