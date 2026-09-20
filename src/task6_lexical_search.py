"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""


import re

from .task4_chunking_indexing import chunk_documents, load_documents


CORPUS: list[dict] = []


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ỹ]+", text.lower(), flags=re.UNICODE)


def _get_corpus() -> list[dict]:
    global CORPUS
    if not CORPUS:
        CORPUS = chunk_documents(load_documents())
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    if not corpus:
        return None
    return BM25Okapi([_tokens(item["content"]) for item in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []
    corpus = _get_corpus()
    bm25 = build_bm25_index(corpus)
    if bm25 is None:
        return []
    scores = bm25.get_scores(_tokens(query))
    ranked = sorted(
        enumerate(scores),
        key=lambda pair: (-float(pair[1]), corpus[pair[0]]["id"]),
    )
    positive_scores = [score for _, score in ranked if score > 0]
    results = []
    for index, score in ranked[:top_k]:
        if positive_scores and score <= 0:
            continue
        item = corpus[index]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(score),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
