import json
import time
from statistics import mean

import pandas as pd
import streamlit as st

from src.benchmarking import aggregate_scores, score_case
from src.parser import extract_lab_values
from src.quality import normalize_and_validate_results

st.set_page_config(page_title="Benchmark Dashboard", layout="wide")
st.title("SehatNama AI - Accuracy & Latency Benchmark")
st.caption(
    "Run dataset-driven evaluation with precision/recall/F1 and per-case latency."
)

st.markdown(
    """
### Dataset JSON format
```json
[
  {
    "id": "case_001",
    "ocr_text": "Sodium (Na) 140 mEq/L 135 - 145 mEq/L\\nCreatinine 1.0 mg/dL 0.6 - 1.2 mg/dL",
    "expected": [
      {"test": "sodium", "value": 140.0},
      {"test": "creatinine", "value": 1.0}
    ]
  }
]
```
"""
)

uploaded = st.file_uploader("Upload benchmark JSON", type=["json"])
rel_tol = st.slider("Relative value tolerance", 0.0, 0.2, 0.05, 0.01)
abs_tol = st.slider("Absolute value tolerance", 0.0, 1.0, 0.2, 0.05)

if not uploaded:
    st.info("Upload dataset JSON to run benchmark.")
    st.stop()

try:
    cases = json.loads(uploaded.read().decode("utf-8"))
except Exception as exc:
    st.error(f"Invalid JSON file: {exc}")
    st.stop()

if not isinstance(cases, list) or not cases:
    st.error("Dataset must be a non-empty JSON array.")
    st.stop()

case_rows = []
case_scores = []
latencies_ms = []
all_misses = []

for case in cases:
    case_id = case.get("id", f"case_{len(case_rows)+1:03d}")
    ocr_text = case.get("ocr_text", "")
    expected = case.get("expected", [])

    start = time.perf_counter()
    parsed = extract_lab_values(ocr_text)
    parsed, warnings = normalize_and_validate_results(parsed)
    latency_ms = (time.perf_counter() - start) * 1000
    latencies_ms.append(latency_ms)

    score = score_case(parsed, expected, rel_tol=rel_tol, abs_tol=abs_tol)
    case_scores.append(score)

    case_rows.append(
        {
            "case_id": case_id,
            "rows_expected": len(expected),
            "rows_detected": len(parsed),
            "precision": score["precision"],
            "recall": score["recall"],
            "f1": score["f1"],
            "latency_ms": round(latency_ms, 2),
            "quality_warnings": len(warnings),
        }
    )
    for miss in score["misses"]:
        all_misses.append({"case_id": case_id, **miss})

summary = aggregate_scores(case_scores)
summary["latency_avg_ms"] = round(mean(latencies_ms), 2) if latencies_ms else 0.0
summary["latency_p95_ms"] = (
    round(sorted(latencies_ms)[int(0.95 * (len(latencies_ms) - 1))], 2)
    if latencies_ms
    else 0.0
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Precision", summary["precision"])
c2.metric("Recall", summary["recall"])
c3.metric("F1", summary["f1"])
c4.metric("Avg Latency (ms)", summary["latency_avg_ms"])

st.subheader("Per-case results")
st.dataframe(pd.DataFrame(case_rows), use_container_width=True)

if all_misses:
    st.subheader("Error Analysis")
    st.dataframe(pd.DataFrame(all_misses), use_container_width=True)
else:
    st.success("No false positives/negatives found in this dataset.")

st.download_button(
    "Download Benchmark Summary JSON",
    data=json.dumps({"summary": summary, "cases": case_rows, "errors": all_misses}, indent=2).encode(
        "utf-8"
    ),
    file_name="benchmark_summary.json",
    mime="application/json",
)
