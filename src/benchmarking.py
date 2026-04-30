from typing import Dict, List, Tuple


def _value_match(pred: float, exp: float, rel_tol: float = 0.05, abs_tol: float = 0.2) -> bool:
    diff = abs(pred - exp)
    return diff <= abs_tol or diff <= abs(exp) * rel_tol


def score_case(
    predicted_rows: List[Dict],
    expected_rows: List[Dict],
    rel_tol: float = 0.05,
    abs_tol: float = 0.2,
) -> Dict:
    expected_by_test = {}
    for row in expected_rows:
        expected_by_test.setdefault(row["test"], []).append(row)

    tp = 0
    fp = 0
    fn = 0
    matched_expected = set()
    misses = []

    for pred in predicted_rows:
        test = pred.get("test")
        value = pred.get("value")
        found = False
        for idx, exp in enumerate(expected_by_test.get(test, [])):
            key = (test, idx)
            if key in matched_expected:
                continue
            if isinstance(value, (int, float)) and _value_match(
                float(value), float(exp["value"]), rel_tol=rel_tol, abs_tol=abs_tol
            ):
                matched_expected.add(key)
                tp += 1
                found = True
                break
        if not found:
            fp += 1
            misses.append(
                {
                    "type": "false_positive",
                    "test": test,
                    "predicted_value": value,
                }
            )

    for test, rows in expected_by_test.items():
        for idx, exp in enumerate(rows):
            if (test, idx) not in matched_expected:
                fn += 1
                misses.append(
                    {
                        "type": "false_negative",
                        "test": test,
                        "expected_value": exp["value"],
                    }
                )

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "misses": misses,
    }


def aggregate_scores(case_scores: List[Dict]) -> Dict:
    total_tp = sum(c["tp"] for c in case_scores)
    total_fp = sum(c["fp"] for c in case_scores)
    total_fn = sum(c["fn"] for c in case_scores)
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {
        "cases": len(case_scores),
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }
