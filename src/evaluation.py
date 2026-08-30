"""RAGAS + retrieval-ablation harness for the Riffle pipeline.

Two Q&A sets share the GreenLeaf sample PDFs:

- ``data/eval/qa_dataset.json`` — extractive smoke quiz (easy, keyword-overlap).
- ``data/eval/qa_heldout.json`` — paraphrase, SKU distractors, multi-hop, and
  unanswerable questions. This is the headline eval.

Ablation measures source hit rate across BM25 / dense / hybrid / rerank
without calling the judge LLM.

Usage:
    python -m src.evaluation              # held-out RAGAS + retrieval ablation
    python -m src.evaluation --smoke      # easy quiz only
    python -m src.evaluation --all        # both Q&A sets + ablation
    python scripts/run_eval.py
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from langchain_openai import ChatOpenAI

from src import _ragas_compat
from src.config import (
    EVAL_DIR,
    EVAL_LLM_MODEL,
    LLAMA_API_KEY,
    LLAMA_BASE_URL,
    RETRIEVER_K,
)
from src.embeddings import get_embeddings
from src.ingest import load_and_split_pdf

logger = logging.getLogger(__name__)

DOCS_DIR = EVAL_DIR / "docs"
QA_PATH = EVAL_DIR / "qa_dataset.json"
HELDOUT_PATH = EVAL_DIR / "qa_heldout.json"
RESULTS_MD = Path(__file__).resolve().parent.parent / "docs" / "eval_results.md"

ABLATION_CONFIGS: list[tuple[str, dict]] = [
    ("BM25 only", {"bm25_weight": 1.0, "dense_weight": 0.0, "rerank_enabled": False}),
    ("Dense only", {"bm25_weight": 0.0, "dense_weight": 1.0, "rerank_enabled": False}),
    (
        "Hybrid (no rerank)",
        {"bm25_weight": 0.5, "dense_weight": 0.5, "rerank_enabled": False},
    ),
    (
        "Hybrid + rerank",
        {"bm25_weight": 0.5, "dense_weight": 0.5, "rerank_enabled": True},
    ),
]


def _load_qa(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Q&A dataset not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _build_eval_index() -> int:
    """Index every sample PDF together so questions can span documents."""
    from src import retrieval

    pdfs = sorted(DOCS_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(
            f"No sample PDFs in {DOCS_DIR}. Run: python scripts/make_sample_docs.py"
        )
    all_chunks: list = []
    for pdf in pdfs:
        all_chunks.extend(load_and_split_pdf(pdf))
    retrieval.build_index(all_chunks)
    logger.info("Indexed %d chunks from %d sample PDFs.", len(all_chunks), len(pdfs))
    return len(pdfs)


def _eval_llm() -> ChatOpenAI:
    """LLM used as the RAGAS judge (configurable, defaults to the chat model)."""
    return ChatOpenAI(
        base_url=LLAMA_BASE_URL,
        api_key=LLAMA_API_KEY,
        model=EVAL_LLM_MODEL,
        temperature=0.0,
    )


def _filename_of(doc) -> str:
    return Path(str(doc.metadata.get("source", ""))).name


def _answerable(qa: list[dict]) -> list[dict]:
    return [item for item in qa if item.get("kind") != "unanswerable" and item.get("sources")]


def run_ablation(qa: list[dict], top_k: int | None = None) -> list[dict]:
    """Source hit rates for each retrieval setup (no LLM judge)."""
    from src import retrieval

    k = top_k or RETRIEVER_K
    items = _answerable(qa)
    if not items:
        raise ValueError("Held-out set has no answerable items with `sources`.")

    rows = []
    for name, kwargs in ABLATION_CONFIGS:
        top1 = 0
        topk = 0
        for item in items:
            gold = set(item["sources"])
            ranked = retrieval.retrieve_with_scores(item["question"], top_k=k, **kwargs)
            names = [_filename_of(doc) for doc, _ in ranked]
            if names and names[0] in gold:
                top1 += 1
            if gold <= set(names):
                topk += 1
        n = len(items)
        row = {
            "name": name,
            "n": n,
            "top1": top1 / n,
            "topk": topk / n,
            "k": k,
        }
        rows.append(row)
        logger.info(
            "Ablation %-20s  top-1=%.3f  top-%d recall=%.3f  (n=%d)",
            name,
            row["top1"],
            k,
            row["topk"],
            n,
        )
    return rows


def run_ragas(qa: list[dict], limit: int | None = None) -> tuple[dict, int]:
    """Score a Q&A list with RAGAS using the live RAG chain."""
    _ragas_compat.install()

    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )
    from ragas.run_config import RunConfig

    from src.rag import answer_with_sources

    if limit:
        qa = qa[:limit]

    samples = []
    for item in qa:
        question = item["question"]
        answer, docs = answer_with_sources(question)
        samples.append(
            {
                "user_input": question,
                "retrieved_contexts": [d.page_content for d in docs],
                "response": answer,
                "reference": item["ground_truth"],
            }
        )

    dataset = EvaluationDataset.from_list(samples)
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=LangchainLLMWrapper(_eval_llm()),
        embeddings=LangchainEmbeddingsWrapper(get_embeddings()),
        raise_exceptions=False,
        show_progress=True,
        # A single local Ollama instance cannot absorb RAGAS's default 16
        # concurrent judge calls; extra workers just time out.
        run_config=RunConfig(max_workers=2, timeout=300),
    )
    return _aggregate(result), len(samples)


def run(limit: int | None = None) -> dict:
    """Smoke-set RAGAS (kept for ``--smoke`` / older scripts)."""
    from src.llm import init_llm

    init_llm()
    _build_eval_index()
    scores, n = run_ragas(_load_qa(QA_PATH), limit=limit)
    _write_report(smoke_scores=scores, smoke_n=n)
    return scores


def _aggregate(result) -> dict:
    """Reduce RAGAS per-sample scores to mean values per metric."""
    df = result.to_pandas()
    metric_cols = [
        c
        for c in df.columns
        if c not in ("user_input", "retrieved_contexts", "response", "reference")
    ]
    scores = {}
    for col in metric_cols:
        series = df[col].dropna()
        if len(series):
            scores[col] = float(series.mean())
    return scores


_METRIC_BLURBS = {
    "faithfulness": "Answer claims grounded in retrieved context (higher = less hallucination)",
    "answer_relevancy": "How directly the answer addresses the question",
    "answer_relevance": "How directly the answer addresses the question",
    "nv_accuracy": "Whether the answer is factually consistent with the reference",
    "context_precision": "Whether relevant chunks are ranked highly",
    "context_recall": "Whether all needed info was retrieved",
}


def _score_of(scores: dict, *names: str) -> str:
    """Format a metric score, matching RAGAS column-name variants."""
    lower = {k.lower(): v for k, v in scores.items()}
    for name in names:
        if name.lower() in lower:
            return f"{lower[name.lower()]:.3f}"
    return "_run to fill_"


def _ragas_table(scores: dict) -> list[str]:
    rows = [
        ("faithfulness", _score_of(scores, "faithfulness"), _METRIC_BLURBS["faithfulness"]),
        (
            "answer_relevancy",
            _score_of(scores, "answer_relevancy", "answer_relevance"),
            _METRIC_BLURBS["answer_relevancy"],
        ),
        (
            "context_precision",
            _score_of(scores, "context_precision"),
            _METRIC_BLURBS["context_precision"],
        ),
        (
            "context_recall",
            _score_of(scores, "context_recall"),
            _METRIC_BLURBS["context_recall"],
        ),
    ]
    extra = [
        (k, v)
        for k, v in scores.items()
        if k.lower()
        not in {
            "faithfulness",
            "answer_relevancy",
            "answer_relevance",
            "context_precision",
            "context_recall",
        }
    ]
    lines = [
        "| Metric | Score (0-1) | What it measures |",
        "|--------|-------------|------------------|",
    ]
    for metric, value, blurb in rows:
        lines.append(f"| {metric} | {value} | {blurb} |")
    for metric, value in extra:
        blurb = _METRIC_BLURBS.get(metric.lower(), "See RAGAS metric docs")
        lines.append(f"| {metric} | {value:.3f} | {blurb} |")
    return lines


def _parse_existing_ablation() -> list[dict] | None:
    """Keep the last ablation table when this run only scores RAGAS."""
    if not RESULTS_MD.is_file():
        return None
    text = RESULTS_MD.read_text(encoding="utf-8")
    rows: list[dict] = []
    k = RETRIEVER_K
    n = 0
    in_section = False
    for line in text.splitlines():
        if line.startswith("## Retrieval ablation"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        if line.startswith("Same **"):
            try:
                n = int(line.split("**")[1])
            except (IndexError, ValueError):
                pass
        if line.startswith("| Setup |"):
            for part in line.split("|"):
                part = part.strip()
                if part.startswith("Top-") and "recall" in part.lower():
                    digits = "".join(ch for ch in part if ch.isdigit())
                    if digits:
                        k = int(digits)
            continue
        if not line.startswith("| ") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 3:
            continue
        name, top1, topk = cells
        try:
            rows.append(
                {
                    "name": name,
                    "n": n or 16,
                    "top1": float(top1),
                    "topk": float(topk),
                    "k": k,
                }
            )
        except ValueError:
            continue
    return rows or None


def _write_report(
    *,
    smoke_scores: dict | None = None,
    smoke_n: int | None = None,
    heldout_scores: dict | None = None,
    heldout_n: int | None = None,
    ablation: list[dict] | None = None,
) -> None:
    RESULTS_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Evaluation Results",
        "",
        f"**Run:** {date.today().isoformat()} · generator/judge `{EVAL_LLM_MODEL}` · "
        "embeddings `bge-small-en-v1.5`.",
        "",
        "Two Q&A sets share the GreenLeaf sample corpus (5 PDFs, including SunMax 370 "
        "and PowerCell 15 distractor SKUs). No data leaves the machine.",
        "",
    ]

    if heldout_scores is not None:
        lines.extend(
            [
                "## Held-out set (headline)",
                "",
                f"Evaluated **{heldout_n}** items from `data/eval/qa_heldout.json`: "
                "paraphrase, near-duplicate SKU distractors, multi-hop, and "
                "unanswerable questions. This set is designed so a keyword-only "
                "retriever can fail.",
                "",
            ]
        )
        lines.extend(_ragas_table(heldout_scores))
        lines.append("")

    if ablation:
        k = ablation[0]["k"]
        n = ablation[0]["n"]
        lines.extend(
            [
                "## Retrieval ablation (held-out, answerable questions)",
                "",
                f"Same **{n}** answerable held-out questions (unanswerable items "
                f"excluded). Top-1 = gold source file is rank 1. Top-{k} source "
                "recall = every gold source file appears in the top "
                f"{k} hits. No LLM judge — isolates retrieval.",
                "",
                f"| Setup | Top-1 hit | Top-{k} source recall |",
                "|--------|----------:|---------------------:|",
            ]
        )
        for row in ablation:
            lines.append(
                f"| {row['name']} | {row['top1']:.3f} | {row['topk']:.3f} |"
            )
        lines.extend(
            [
                "",
                "Hybrid + rerank lifts top-1 vs BM25. Dense-only is often close; "
                "adding BM25 *without* a reranker can hurt precision because "
                "keyword overlap pulls in distractor SKUs. The cross-encoder "
                "recovers ranking.",
                "",
            ]
        )

    if smoke_scores is not None:
        lines.extend(
            [
                "## Smoke set (extractive quiz)",
                "",
                f"Evaluated **{smoke_n}** keyword-overlap pairs from "
                "`data/eval/qa_dataset.json`. Easy on purpose — a sanity check, "
                "not a claim of production quality.",
                "",
            ]
        )
        lines.extend(_ragas_table(smoke_scores))
        lines.append("")

    lines.extend(
        [
            "> Scores from a small local judge (e.g. `qwen2.5:3b`) are directional. "
            "Set `EVAL_LLM_MODEL` to a larger local model for more reliable judging. "
            "Re-run: `python scripts/make_sample_docs.py` then `python -m src.evaluation`.",
            "",
        ]
    )
    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote %s", RESULTS_MD)


def _print_scores(title: str, scores: dict) -> None:
    print(f"\n=== {title} ===")
    for metric, value in scores.items():
        print(f"{metric:24s} {value:.3f}")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Riffle evaluation harness")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run RAGAS on the easy extractive quiz only",
    )
    parser.add_argument(
        "--heldout",
        action="store_true",
        help="Run RAGAS on the harder held-out set",
    )
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="Run retrieval source-hit ablation (no judge LLM)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Smoke RAGAS + held-out RAGAS + retrieval ablation",
    )
    parser.add_argument("--limit", type=int, default=None, help="Cap RAGAS items")
    args = parser.parse_args(argv)

    do_smoke = args.smoke or args.all
    do_heldout = args.heldout or args.all or not (args.smoke or args.heldout or args.ablation)
    do_ablation = args.ablation or args.all or not (args.smoke or args.heldout or args.ablation)
    # Default (no flags): held-out RAGAS + ablation. --smoke alone skips those.

    from src.llm import init_llm

    init_llm()
    _build_eval_index()

    smoke_scores = smoke_n = heldout_scores = heldout_n = None
    ablation = None

    if do_ablation:
        ablation = run_ablation(_load_qa(HELDOUT_PATH))
    else:
        ablation = _parse_existing_ablation()

    if do_heldout:
        heldout_scores, heldout_n = run_ragas(_load_qa(HELDOUT_PATH), limit=args.limit)
        _print_scores("Held-out RAGAS", heldout_scores)

    if do_smoke:
        smoke_scores, smoke_n = run_ragas(_load_qa(QA_PATH), limit=args.limit)
        _print_scores("Smoke RAGAS", smoke_scores)

    if ablation:
        print("\n=== Retrieval ablation ===")
        k = ablation[0]["k"]
        for row in ablation:
            print(
                f"{row['name']:22s}  top-1 {row['top1']:.3f}  "
                f"top-{k} recall {row['topk']:.3f}"
            )

    _write_report(
        smoke_scores=smoke_scores,
        smoke_n=smoke_n,
        heldout_scores=heldout_scores,
        heldout_n=heldout_n,
        ablation=ablation,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
