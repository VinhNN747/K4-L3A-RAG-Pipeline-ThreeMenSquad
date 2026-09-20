"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import json
import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from .contracts import validate_document


load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"


@lru_cache(maxsize=1)
def _local_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts with one configured provider and a stable output shape."""
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("all texts must be non-empty strings")

    provider = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").lower()
    if provider in {"sentence_transformers", "sentence-transformers", "local"}:
        vectors = _local_embedding_model().encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        response = OpenAI(api_key=api_key).embeddings.create(
            model=model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    if provider == "gemini":
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required for Gemini embeddings")
        model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        response = genai.Client(api_key=api_key).models.embed_content(
            model=model,
            contents=texts,
        )
        return [embedding.values for embedding in response.embeddings]

    raise ValueError(
        "Unsupported EMBEDDING_PROVIDER. Use sentence_transformers, openai or gemini."
    )


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _first_heading(content: str, fallback: str) -> str:
    for line in content.splitlines():
        match = re.match(r"^#+\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return fallback


def _metadata_from_markdown(path: Path, content: str) -> dict:
    source_match = re.search(r"^\*\*Source:\s*(.+?)\*\*\s*$", content, re.MULTILINE)
    url = source_match.group(1).strip() if source_match else None
    doc_type = "legal" if path.parent.name == "legal" else "news"
    return {
        "source": path.name,
        "title": _first_heading(content, path.stem),
        "doc_type": doc_type,
        "url": url,
    }


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        document = {
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": _metadata_from_markdown(path, content),
        }
        validate_document(document)
        documents.append(document)
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        validate_document(document)
        pieces = splitter.split_text(document["content"])
        for index, text in enumerate(pieces):
            text = text.strip()
            if not text:
                continue
            chunk = {
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {**document["metadata"], "chunk_index": index},
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    if len(vectors) != len(chunks):
        raise RuntimeError("embedding provider returned an unexpected number of vectors")
    return [{**chunk, "embedding": vector} for chunk, vector in zip(chunks, vectors)]


def _chroma_metadata(metadata: dict) -> dict:
    return {
        key: ("" if value is None else value)
        for key, value in metadata.items()
    }


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return
    ids = [chunk["id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("chunk IDs must be unique before indexing")
    for chunk in chunks:
        validate_document(chunk, require_chunk=True)
        if not isinstance(chunk.get("embedding"), list) or not chunk["embedding"]:
            raise ValueError("each chunk must contain a non-empty embedding")

    collection = get_collection()
    collection.upsert(
        ids=ids,
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[_chroma_metadata(chunk["metadata"]) for chunk in chunks],
    )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
