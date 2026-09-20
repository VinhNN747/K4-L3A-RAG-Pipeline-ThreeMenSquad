"""Run the required RAGAS evaluation with a real configured LLM API."""

import json
import os
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from .task4_chunking_indexing import EMBEDDING_MODEL, embed_texts
from .task5_semantic_search import semantic_search
from .task9_retrieval_pipeline import retrieve
from .task10_generation import SYSTEM_PROMPT, call_llm, format_context, reorder_for_llm


load_dotenv()

ROOT = Path(__file__).parent.parent
DATASET_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
RESULTS_PATH = ROOT / "group_project" / "evaluation" / "evaluation_results.json"
REPORT_PATH = ROOT / "group_project" / "evaluation" / "RESULT.md"
TOP_K = int(os.getenv("EVAL_TOP_K", "5"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD") or "0.3")
REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."


class _RagasEmbeddingAdapter:
    """Compatibility adapter for RAGAS 0.4 metrics using LangChain names.

    RAGAS 0.4 providers expose ``embed_text``/``embed_texts``, while the
    legacy metrics still call ``embed_query``/``embed_documents``.  The
    pipeline already has a single configured embedding function, so wrapping
    it here keeps evaluation on the same local BGE-M3 model without making a
    second remote embedding request.
    """

    def embed_query(self, text: str) -> list[float]:
        return embed_texts([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_texts(texts)


def _real_evaluator():
    """Build RAGAS LLM and embedding clients from environment variables."""
    provider = os.getenv("EVAL_PROVIDER", os.getenv("LLM_PROVIDER", "openai")).lower()
    model = os.getenv("EVAL_MODEL", os.getenv("LLM_MODEL", ""))
    if not model:
        model = "gpt-4o-mini" if provider == "openai" else "claude-3-5-haiku-latest"

    from ragas.llms import llm_factory

    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for a real RAGAS evaluation")
        client = OpenAI(api_key=api_key)
        llm = llm_factory(model, provider="openai", client=client)
        return provider, model, llm, _RagasEmbeddingAdapter()

    if provider == "anthropic":
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for a real RAGAS evaluation")
        client = Anthropic(api_key=api_key)
        llm = llm_factory(model, provider="anthropic", client=client)
        return provider, model, llm, _RagasEmbeddingAdapter()

    raise RuntimeError(
        "EVAL_PROVIDER must be openai or anthropic. Configure a real API key in .env."
    )


def _answer_from_results(question: str, results: list[dict]) -> str:
    if not results:
        return REFUSAL
    context = format_context(reorder_for_llm(results))
    prompt = (
        "Use only the supplied context. Answer in Vietnamese when appropriate. "
        "Cite every factual statement using [Document N]. If the context is not "
        f"enough, reply exactly with a safe refusal.\n\nContext:\n{context}\n\nQuestion: {question}"
    )
    answer = call_llm(SYSTEM_PROMPT, prompt)
    if not answer.strip():
        raise RuntimeError("generator API returned an empty answer")
    return answer.strip()


def _build_samples(dataset: list[dict], configuration: str) -> list[dict]:
    samples = []
    for case in dataset:
        if configuration == "dense-only":
            results = semantic_search(case["question"], top_k=TOP_K)
        else:
            results = retrieve(
                case["question"],
                top_k=TOP_K,
                score_threshold=SCORE_THRESHOLD,
                use_reranking=True,
            )
        samples.append(
            {
                "user_input": case["question"],
                "response": _answer_from_results(case["question"], results),
                "retrieved_contexts": [item["content"] for item in results],
                "reference": case["expected_answer"],
                "source_ids": [item["id"] for item in results],
            }
        )
    return samples


def _run_ragas(samples: list[dict], llm, embeddings) -> list[dict]:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    dataset = Dataset.from_list(
        [
            {
                key: value
                for key, value in sample.items()
                if key in {"user_input", "response", "retrieved_contexts", "reference"}
            }
            for sample in samples
        ]
    )
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=True,
        show_progress=True,
    )
    rows = []
    for sample, score in zip(samples, result.scores):
        row = dict(sample)
        for key in ("faithfulness", "answer_relevancy", "context_recall", "context_precision"):
            value = score.get(key)
            row[key] = None if value is None else float(value)
        rows.append(row)
    return rows


def _average(rows: list[dict], key: str) -> float:
    values = [row[key] for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else 0.0


def _report(payload: dict) -> str:
    fields = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
    labels = {
        "faithfulness": "Faithfulness",
        "answer_relevancy": "Answer relevance",
        "context_recall": "Context recall",
        "context_precision": "Context precision",
    }
    configurations = payload["configurations"]
    dense = configurations["dense-only"]
    hybrid = configurations["hybrid + RRF"]
    dense_avg = {field: _average(dense["rows"], field) for field in fields}
    hybrid_avg = {field: _average(hybrid["rows"], field) for field in fields}
    dense_mean = sum(dense_avg.values()) / len(fields)
    hybrid_mean = sum(hybrid_avg.values()) / len(fields)
    worst = sorted(
        hybrid["rows"],
        key=lambda row: sum(row.get(field) or 0.0 for field in fields),
    )[:3]
    lines = [
        "# RAG evaluation results", "", "## Run information", "",
        "| Field | Value |", "| --- | --- |",
        f"| Evaluation date | {payload['evaluation_date']} |",
        "| Framework and version | RAGAS 0.4.3 |",
        f"| Evaluator model | {payload['evaluator_model']} ({payload['evaluator_provider']}) |",
        f"| Generator model | {payload['generator_model']} ({payload['generator_provider']}) |",
        f"| Embedding model | {payload['embedding_model']} |",
        "| Corpus version/commit | local filesystem snapshot |",
        f"| Golden dataset size | {payload['dataset_size']} |",
        f"| `top_k` | {TOP_K} |",
        f"| Fallback threshold and calibration | {SCORE_THRESHOLD}; configured baseline |",
        "", "## Configurations", "",
        "- **Config A — dense-only:** shared embedding + Chroma cosine search.",
        "- **Config B — hybrid + RRF:** dense + BM25 + one RRF fusion + threshold fallback.",
        "", "## Overall scores", "",
        "| Metric | Config A | Config B | Delta B−A |",
        "| --- | ---: | ---: | ---: |",
    ]
    for field in fields:
        lines.append(f"| {labels[field]} | {dense_avg[field]:.4f} | {hybrid_avg[field]:.4f} | {hybrid_avg[field] - dense_avg[field]:+.4f} |")
    lines += [
        f"| **Average** | **{dense_mean:.4f}** | **{hybrid_mean:.4f}** | **{hybrid_mean - dense_mean:+.4f}** |",
        "", "## A/B comparison", "",
        f"- Cấu hình tốt hơn: {'hybrid + RRF' if hybrid_mean >= dense_mean else 'dense-only'}.",
        f"- Evidence: RAGAS average {dense_mean:.4f} → {hybrid_mean:.4f}.",
        f"- Trade-off latency: dense {dense['latency_ms']:.2f} ms/query; hybrid {hybrid['latency_ms']:.2f} ms/query, đã bao gồm generation và RAGAS API evaluation.",
        "", "## Worst performers", "",
        "| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for index, row in enumerate(worst, 1):
        lines.append(
            f"| {index} | {row['user_input']} | hybrid + RRF | {row['faithfulness']:.4f} | {row['answer_relevancy']:.4f} | {row['context_recall']:.4f} | {row['context_precision']:.4f} | retrieval/generation | inspect retrieved IDs: {', '.join(row['source_ids'][:2])} |"
        )
    lines += [
        "", "## Recommendations", "",
        "| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |",
        "| ---: | --- | --- | --- | --- |",
        "| 1 | Tune chunk size and overlap | Low context recall cases | Higher grounded recall | Re-run RAGAS |",
        "| 2 | Calibrate score threshold | Weak dense matches trigger fallback | Safer retrieval | Evaluate threshold grid |",
        "| 3 | Improve Vietnamese lexical normalization | Low context precision/relevance cases | Better BM25 contribution | Add query variants |",
        "", "## Bonus experiments", "",
        "| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |",
        "| --- | --- | ---: | ---: | --- |",
        "| None | hybrid + RRF | 0.0000 | 0 | Not run; required A/B scope completed |",
        "", "> Scores above are real RAGAS LLM-evaluator scores from the configured API; no deterministic fallback was substituted.",
    ]
    return "\n".join(lines) + "\n"


def run() -> dict:
    evaluator_provider, evaluator_model, evaluator_llm, evaluator_embeddings = _real_evaluator()
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    generator_provider = os.getenv("LLM_PROVIDER", evaluator_provider)
    generator_model = os.getenv("LLM_MODEL", evaluator_model)
    payload = {
        "evaluation_date": date.today().isoformat(),
        "evaluator_provider": evaluator_provider,
        "evaluator_model": evaluator_model,
        "generator_provider": generator_provider,
        "generator_model": generator_model,
        "embedding_model": EMBEDDING_MODEL,
        "dataset_size": len(dataset),
        "configurations": {},
    }
    for configuration in ("dense-only", "hybrid + RRF"):
        started = time.perf_counter()
        samples = _build_samples(dataset, configuration)
        rows = _run_ragas(samples, evaluator_llm, evaluator_embeddings)
        payload["configurations"][configuration] = {
            "rows": rows,
            "latency_ms": (time.perf_counter() - started) * 1000 / max(1, len(dataset)),
        }
    RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(_report(payload), encoding="utf-8")
    print(json.dumps(payload["configurations"], ensure_ascii=False, indent=2))
    print(f"Wrote {REPORT_PATH}")
    return payload


if __name__ == "__main__":
    run()
