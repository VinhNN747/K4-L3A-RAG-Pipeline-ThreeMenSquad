"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .contracts import validate_search_results
from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []
    query_vector = embed_texts([query])[0]
    collection = get_collection()
    if hasattr(collection, "count") and collection.count() == 0:
        return []
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    rows = zip(
        response.get("ids", [[]])[0],
        response.get("documents", [[]])[0],
        response.get("metadatas", [[]])[0],
        response.get("distances", [[]])[0],
    )
    results = []
    for item_id, content, metadata, distance in rows:
        metadata = dict(metadata or {})
        if metadata.get("url") == "":
            metadata["url"] = None
        results.append({
            "id": item_id,
            "content": content,
            "score": max(0.0, 1.0 - float(distance)),
            "metadata": metadata,
            "retrieval_method": "dense",
        })
    results = sorted(results, key=lambda item: (-item["score"], item["id"]))[:top_k]
    validate_search_results(results, top_k=top_k, expected_method="dense")
    return results


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)
