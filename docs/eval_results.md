# Evaluation Results

**Run:** 2026-08-28 · generator/judge `qwen2.5:3b` · embeddings `bge-small-en-v1.5`.

Two Q&A sets share the GreenLeaf sample corpus (5 PDFs, including SunMax 370 and PowerCell 15 distractor SKUs). No data leaves the machine.

## Held-out set (headline)

Evaluated **20** items from `data/eval/qa_heldout.json`: paraphrase, near-duplicate SKU distractors, multi-hop, and unanswerable questions. This set is designed so a keyword-only retriever can fail.

| Metric | Score (0-1) | What it measures |
|--------|-------------|------------------|
| faithfulness | 0.688 | Answer claims grounded in retrieved context (higher = less hallucination) |
| answer_relevancy | 0.675 | How directly the answer addresses the question |
| context_precision | 0.729 | Whether relevant chunks are ranked highly |
| context_recall | 0.750 | Whether all needed info was retrieved |

## Retrieval ablation (held-out, answerable questions)

Same **16** answerable held-out questions (unanswerable items excluded). Top-1 = gold source file is rank 1. Top-4 source recall = every gold source file appears in the top 4 hits. No LLM judge — isolates retrieval.

| Setup | Top-1 hit | Top-4 source recall |
|--------|----------:|---------------------:|
| BM25 only | 0.562 | 0.938 |
| Dense only | 0.875 | 1.000 |
| Hybrid (no rerank) | 0.688 | 1.000 |
| Hybrid + rerank | 0.875 | 1.000 |

Hybrid + rerank lifts top-1 vs BM25. Dense-only is often close; adding BM25 *without* a reranker can hurt precision because keyword overlap pulls in distractor SKUs. The cross-encoder recovers ranking.

> Scores from a small local judge (e.g. `qwen2.5:3b`) are directional. Set `EVAL_LLM_MODEL` to a larger local model for more reliable judging. Re-run: `python scripts/make_sample_docs.py` then `python -m src.evaluation`.
