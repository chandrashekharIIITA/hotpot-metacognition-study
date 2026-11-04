"""
evaluator.py
Utilities for HotpotQA answer evaluation and paired baseline/experimental analysis.

Example:
    from evaluator import load_hotpot, evaluate_pair, save_results
"""

import json
import re
import string
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


def load_hotpot(path: str, limit: Optional[int] = None) -> List[dict]:
    """Load HotpotQA JSON and optionally restrict the number of rows."""
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data[:limit] if limit is not None else data


def get_sample_id(row: dict, index: int) -> str:
    """Return a stable ID, falling back to the dataset index."""
    value = row.get("_id", row.get("id", index))
    return str(value)


def format_context(row: dict) -> str:
    """Format HotpotQA context (title and sentences are separate arrays)."""
    context = row.get("context", {})
    titles = context.get("title", [])
    sentence_groups = context.get("sentences", [])

    blocks = []
    for title, sentences in zip(titles, sentence_groups):
        blocks.append(f"Title: {title}\nText: {' '.join(sentences)}")
    return "\n\n".join(blocks)


def normalize_answer(answer: Any) -> str:
    """HotpotQA-style normalization: lowercase, remove punctuation/articles."""
    text = str(answer).lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def exact_match(prediction: Any, gold: Any) -> int:
    return int(normalize_answer(prediction) == normalize_answer(gold))


def token_f1(prediction: Any, gold: Any) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(gold).split()

    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)

    common = Counter(pred_tokens) & Counter(gold_tokens)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0

    precision = overlap / len(pred_tokens)
    recall = overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def extract_answer(text: str) -> str:
    """
    Extract answer from common output formats:
      FINAL ANSWER: ...
      DRAFT ANSWER: ...
      Answer: ...
    Otherwise return the last non-empty line.
    """
    if not text:
        return ""

    patterns = [
        r"FINAL\s+ANSWER\s*:\s*(.+)",
        r"DRAFT\s+ANSWER\s*:\s*(.+)",
        r"ANSWER\s*:\s*(.+)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            return matches[-1].strip().strip('"').strip("'")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def evaluate_prediction(prediction: str, gold: str) -> dict:
    """Return normalized EM and token F1 for one prediction."""
    return {
        "exact_match": exact_match(prediction, gold),
        "f1": token_f1(prediction, gold),
    }


def save_results(
    rows: Iterable[dict],
    csv_path: str,
    json_path: Optional[str] = None,
) -> pd.DataFrame:
    """Save results to CSV and optionally JSON."""
    df = pd.DataFrame(list(rows))
    df.to_csv(csv_path, index=False)

    if json_path:
        df.to_json(json_path, orient="records", indent=2, force_ascii=False)

    return df


def _parse_bool(value):
    """Safely parse CSV booleans; strings like 'False' stay False."""
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False

    value = str(value).strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    return None


def evaluate_pair(
    baseline_csv: str = "baseline_results.csv",
    experimental_csv: str = "experimental_results.csv",
    output_csv: str = "paired_analysis_valid.csv",
    failed_csv: str = "paired_analysis_failed.csv",
) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Align baseline and experimental CSVs by ID, validate gold answers,
    calculate transitions, and save valid/failed paired rows.

    Expected correctness column: is_correct
    Expected gold column: ground_truth
    ID column may be id or _id.
    """
    base = pd.read_csv(baseline_csv)
    exp = pd.read_csv(experimental_csv)

    def standardize(df, label):
        df = df.copy()
        if "_id" not in df.columns:
            if "id" in df.columns:
                df["_id"] = df["id"]
            else:
                raise KeyError(f"{label}: missing id/_id column")

        if df["_id"].isna().any():
            raise ValueError(f"{label}: missing IDs")
        df["_id"] = df["_id"].astype(str).str.strip()
        if df["_id"].duplicated().any():
            raise ValueError(f"{label}: duplicate IDs")
        if "is_correct" not in df.columns:
            raise KeyError(f"{label}: missing is_correct column")
        if "ground_truth" not in df.columns:
            raise KeyError(f"{label}: missing ground_truth column")
        df["is_correct"] = df["is_correct"].apply(_parse_bool)
        return df

    base = standardize(base, "Baseline")
    exp = standardize(exp, "Experimental")

    merged = base.merge(
        exp, on="_id", how="outer", suffixes=("_base", "_exp"),
        indicator=True, validate="one_to_one"
    )

    unmatched = merged[merged["_merge"] != "both"]
    if not unmatched.empty:
        unmatched.to_csv("paired_analysis_unmatched.csv", index=False)
        raise ValueError(
            "Baseline and experimental IDs differ. "
            "Details saved to paired_analysis_unmatched.csv"
        )

    merged = merged.drop(columns="_merge")

    gold_base = merged["ground_truth_base"].astype(str).str.strip().str.lower()
    gold_exp = merged["ground_truth_exp"].astype(str).str.strip().str.lower()
    if not gold_base.equals(gold_exp):
        raise ValueError("Gold answers differ between conditions.")

    valid = merged[
        merged["is_correct_base"].notna()
        & merged["is_correct_exp"].notna()
    ].copy()

    failed = merged[
        merged["is_correct_base"].isna()
        | merged["is_correct_exp"].isna()
    ].copy()

    b = valid["is_correct_base"].astype(bool)
    e = valid["is_correct_exp"].astype(bool)

    transitions = {
        "Wrong -> Correct": int((~b & e).sum()),
        "Correct -> Wrong": int((b & ~e).sum()),
        "Correct -> Correct": int((b & e).sum()),
        "Wrong -> Wrong": int((~b & ~e).sum()),
    }

    n = len(valid)
    baseline_accuracy = float(b.mean()) if n else None
    experimental_accuracy = float(e.mean()) if n else None
    recoveries = transitions["Wrong -> Correct"]
    overcorrections = transitions["Correct -> Wrong"]

    summary = {
        "paired_total": len(merged),
        "valid_pairs": n,
        "incomplete_pairs": len(failed),
        "baseline_accuracy": baseline_accuracy,
        "experimental_accuracy": experimental_accuracy,
        "absolute_improvement": (
            experimental_accuracy - baseline_accuracy if n else None
        ),
        "recoveries": recoveries,
        "overcorrections": overcorrections,
        "recovery_rate": (
            recoveries / int((~b).sum()) if int((~b).sum()) else None
        ),
        "overcorrection_rate": (
            overcorrections / int(b.sum()) if int(b.sum()) else None
        ),
        "transitions": transitions,
    }

    valid.to_csv(output_csv, index=False)
    failed.to_csv(failed_csv, index=False)

    print("\n=== PAIRED EVALUATION ===")
    print(f"Total paired: {summary['paired_total']}")
    print(f"Valid pairs: {n}")
    print(f"Incomplete pairs: {len(failed)}")
    print(f"Baseline accuracy: {baseline_accuracy}")
    print(f"Experimental accuracy: {experimental_accuracy}")
    print(f"Absolute improvement: {summary['absolute_improvement']}")
    for label, count in transitions.items():
        print(f"{label}: {count}")
    print(f"Recovery rate: {summary['recovery_rate']}")
    print(f"Over-correction rate: {summary['overcorrection_rate']}")
    print(f"Saved: {output_csv}, {failed_csv}")

    return valid, failed, summary


if __name__ == "__main__":
    evaluate_pair()
