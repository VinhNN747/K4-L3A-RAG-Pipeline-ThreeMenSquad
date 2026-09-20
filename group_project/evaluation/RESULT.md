# RAG evaluation results

## Run information

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-21 |
| Framework and version | RAGAS 0.4.3 |
| Evaluator model | gpt-3.5-turbo (openai) |
| Generator model | gpt-3.5-turbo (openai) |
| Embedding model | BAAI/bge-m3 |
| Corpus version/commit | local filesystem snapshot |
| Golden dataset size | 15 |
| `top_k` | 5 |
| Fallback threshold and calibration | 0.3; configured baseline |

## Configurations

- **Config A — dense-only:** shared embedding + Chroma cosine search.
- **Config B — hybrid + RRF:** dense + BM25 + one RRF fusion + threshold fallback.

## Overall scores

| Metric | Config A | Config B | Delta B−A |
| --- | ---: | ---: | ---: |
| Faithfulness | 0.8489 | 0.8905 | +0.0416 |
| Answer relevance | 0.7951 | 0.8043 | +0.0092 |
| Context recall | 1.0000 | 1.0000 | +0.0000 |
| Context precision | 0.9138 | 0.8741 | -0.0397 |
| **Average** | **0.8894** | **0.8922** | **+0.0028** |

## A/B comparison

- Cấu hình tốt hơn: hybrid + RRF.
- Evidence: RAGAS average 0.8894 → 0.8922.
- Trade-off latency: dense 28038.41 ms/query; hybrid 49129.35 ms/query, đã bao gồm generation và RAGAS API evaluation.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Nhà ở xã hội được định nghĩa như thế nào? | hybrid + RRF | 0.5000 | 0.7160 | 1.0000 | 0.8667 | retrieval/generation | inspect retrieved IDs: legal/policy-c.md::chunk-10, legal/policy-c.md::chunk-380 |
| 2 | Robot hình người G1 của Unitree Robotics có giá khởi điểm khoảng bao nhiêu? | hybrid + RRF | 0.5000 | 0.9235 | 1.0000 | 0.8333 | retrieval/generation | inspect retrieved IDs: news/article_02.md::chunk-18, news/article_02.md::chunk-16 |
| 3 | Luật Nhà ở số 27/2023/QH15 có hiệu lực từ thời điểm nào? | hybrid + RRF | 0.5000 | 0.9678 | 1.0000 | 0.8875 | retrieval/generation | inspect retrieved IDs: legal/policy-c.md::chunk-0, legal/policy-c.md::chunk-3 |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| ---: | --- | --- | --- | --- |
| 1 | Tinh chỉnh chunk size và overlap | Các trường hợp có context recall thấp | Cải thiện grounded recall | Chạy lại RAGAS |
| 2 | Hiệu chỉnh score threshold | Dense match yếu dẫn đến kích hoạt fallback | Retrieval an toàn và chính xác hơn | Đánh giá trên threshold grid |
| 3 | Cải thiện lexical normalization cho tiếng Việt | Các trường hợp context precision/relevance thấp | Tăng đóng góp của BM25 | Bổ sung các query variants |
## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | ---: | ---: | --- |
| Threshold calibration (`0.2–0.5`) | hybrid + RRF | +0.002 ~ +0.010 | ~0% | cải thiện precision/faithfulness khi giảm các fallback không cần thiết |
| Vietnamese lexical normalization | hybrid + RRF | +0.003 ~ +0.012 | +1 ~ +5% | BM25 có thể bắt tốt hơn các biến thể từ và cách viết tiếng Việt |
| RRF weight tuning (dense vs. BM25) | hybrid + RRF | +0.002 ~ +0.008 | ~0% | Cải thiện context precision trong khi vẫn giữ lợi ích của hybrid retrieval |

> Các điểm số nêu trên là điểm đánh giá LLM thực tế từ RAGAS (thông qua API đã được cấu hình); không có cơ chế dự phòng fall back nào được sử dụng thay thế.
