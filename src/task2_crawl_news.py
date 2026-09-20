"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://vnexpress.net/mo-hinh-cua-openai-day-phien-ban-sau-noi-doi-5122375.html",
    "https://vnexpress.net/nhung-robot-hinh-nguoi-di-lam-cong-nhan-5120622.html",
    "https://vnexpress.net/gemini-tan-cong-mang-doan-mat-khau-nguoi-dung-5122237.html",
    "https://vnexpress.net/ai-claude-tham-gia-phat-trien-phien-ban-tiep-theo-cua-chinh-no-5121950.html",
    "https://vnexpress.net/gioi-cong-nghe-chia-phe-vi-ai-noi-loan-5121529.html",
]


async def crawl_article(url: str) -> dict:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
    markdown = getattr(result, "markdown", "") or ""
    if not markdown.strip():
        raise RuntimeError(f"Crawler returned empty markdown for {url}")
    metadata = getattr(result, "metadata", {}) or {}
    title = metadata.get("title", "Unknown") if isinstance(metadata, dict) else "Unknown"
    return {
        "url": url,
        "title": str(title).strip() or "Unknown",
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": markdown.strip(),
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
