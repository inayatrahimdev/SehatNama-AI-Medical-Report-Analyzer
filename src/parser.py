import re
from typing import Dict, List, Optional


TEST_ALIASES = {
    "hemoglobin": ["hemoglobin", "hb", "hgb"],
    "wbc": ["wbc", "white blood cell", "tlc", "total leukocyte count"],
    "rbc": ["rbc", "red blood cell"],
    "platelets": ["platelet", "plt", "platelets"],
    "glucose_fasting": ["fasting glucose", "fbs", "glucose fasting"],
    "hba1c": ["hba1c", "glycated hemoglobin"],
    "creatinine": ["creatinine", "serum creatinine"],
    "urea": ["urea", "blood urea"],
    "alt": ["alt", "sgpt"],
    "ast": ["ast", "sgot"],
    "bilirubin_total": ["total bilirubin", "bilirubin total"],
    "cholesterol_total": ["total cholesterol", "cholesterol"],
    "sodium": ["sodium", "na"],
    "potassium": ["potassium", "k"],
    "chloride": ["chloride", "cl", "c1"],
    "carbon_dioxide": ["carbon dioxide", "co2", "c02", "bicarbonate", "hco3"],
    "blood_urea_nitrogen": ["blood urea nitrogen", "bun"],
    "glucose": ["glucose", "fbs", "fasting glucose", "glucose fasting"],
}

KNOWN_UNITS = {
    "mg/dl",
    "g/dl",
    "meq/l",
    "u/l",
    "iu/l",
    "mmol/l",
    "%",
    "x10^3/ul",
    "x10^6/ul",
    "fl",
    "pg",
    "pg/ml",
    "ng/ml",
    "miu/ml",
    "iu/ml",
    "cells/ul",
    "/hpf",
    "/lpf",
    "sec",
    "seconds",
    "ratio",
    "g/l",
    "mm/hr",
    "k/ul",
    "m/ul",
    "10^3/ul",
    "10^6/ul",
}

NON_RESULT_LINE_HINTS = [
    "patient",
    "name",
    "gender",
    "date of birth",
    "medical record",
    "clinical history",
    "routine check",
    "test results",
    "reference range",
    "report",
]

PROFILE_KEYWORDS = {
    "cbc": ["hemoglobin", "wbc", "rbc", "platelet", "tlc", "neutrophil", "lymphocyte"],
    "bmp": ["sodium", "potassium", "chloride", "co2", "bicarbonate", "bun", "creatinine", "glucose"],
    "lft": ["bilirubin", "alt", "ast", "alkaline phosphatase", "albumin", "sgpt", "sgot"],
    "rft": ["urea", "creatinine", "egfr", "uric acid", "bun"],
}


def _normalize_name(raw: str) -> str:
    low = raw.strip().lower()
    low = low.replace("c1", "cl").replace("c02", "co2")
    # Match more specific aliases first (e.g. "blood urea nitrogen" before "urea").
    alias_pairs = []
    for canonical, aliases in TEST_ALIASES.items():
        for alias in aliases:
            alias_pairs.append((alias, canonical))
    alias_pairs.sort(key=lambda x: len(x[0]), reverse=True)

    for alias, canonical in alias_pairs:
        if alias in low:
            return canonical
    return low


def _normalize_spaces(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def _clean_unit(unit: str) -> str:
    if not unit:
        return "-"
    normalized = unit.strip().replace("mEql", "mEq/L").replace("mEqI", "mEq/L")
    normalized = normalized.replace("x103/uL", "x10^3/uL").replace("x106/uL", "x10^6/uL")
    return normalized


def _is_non_result_line(line: str) -> bool:
    low = line.lower()
    return any(hint in low for hint in NON_RESULT_LINE_HINTS)


def _has_known_alias(text: str) -> bool:
    low = text.lower()
    for aliases in TEST_ALIASES.values():
        for alias in aliases:
            if alias in low:
                return True
    return False


def detect_template_profile(ocr_text: str) -> str:
    low = ocr_text.lower()
    scores = {}
    for profile, keywords in PROFILE_KEYWORDS.items():
        scores[profile] = sum(1 for kw in keywords if kw in low)
    best = max(scores, key=scores.get) if scores else "generic"
    return best if scores.get(best, 0) > 0 else "generic"


def _merge_split_lines(lines: List[str]) -> List[str]:
    merged: List[str] = []
    i = 0
    while i < len(lines):
        cur = lines[i]
        if i + 1 < len(lines):
            nxt = lines[i + 1]
            # Common OCR split: "Carbon Dioxide" then "25 mEq/L 22 - 32 mEq/L"
            if re.match(r"^[0-9]+(?:\.[0-9]+)?\s*", nxt) and _has_known_alias(cur):
                merged.append(f"{cur} {nxt}")
                i += 2
                continue
        merged.append(cur)
        i += 1
    return merged


def _extract_tabular_line(line: str) -> Optional[Dict[str, str]]:
    # Handles common report rows such as:
    # "Sodium (Na) 140 mEq/L 135 - 145 mEq/L"
    pattern = (
        r"^([A-Za-z][A-Za-z0-9\s()/\-]+?)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s*([%A-Za-z0-9^/.\-]+)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)\s*([%A-Za-z0-9^/.\-]+)?$"
    )
    match = re.match(pattern, line)
    if not match:
        return None

    test_raw = match.group(1).strip()
    value = float(match.group(2).strip())
    unit_raw = _clean_unit((match.group(3) or "-").strip())
    ref_low = float(match.group(4).strip())
    ref_high = float(match.group(5).strip())
    ref_unit = _clean_unit((match.group(6) or unit_raw).strip())

    return {
        "test": _normalize_name(test_raw),
        "original_test": test_raw,
        "value": value,
        "unit": unit_raw,
        "ref_low": ref_low,
        "ref_high": ref_high,
        "ref_unit": ref_unit,
        "source_line": line,
    }


def _extract_tabular_without_unit(line: str) -> Optional[Dict[str, str]]:
    # Handles rows like:
    # "ESR 12 0 - 20"
    pattern = (
        r"^([A-Za-z][A-Za-z0-9\s()/\-]+?)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)$"
    )
    match = re.match(pattern, line)
    if not match:
        return None

    test_raw = match.group(1).strip()
    value = float(match.group(2).strip())
    ref_low = float(match.group(3).strip())
    ref_high = float(match.group(4).strip())

    if _is_non_result_line(test_raw):
        return None

    return {
        "test": _normalize_name(test_raw),
        "original_test": test_raw,
        "value": value,
        "unit": "-",
        "ref_low": ref_low,
        "ref_high": ref_high,
        "ref_unit": "-",
        "source_line": line,
    }


def _extract_value_unit(line: str) -> Optional[Dict[str, str]]:
    # Typical patterns: "Hemoglobin 11.2 g/dL", "WBC : 12.5 x10^3/uL"
    pattern = r"([A-Za-z][A-Za-z\s\-/()]+?)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*([%A-Za-z0-9^/.\-]*)"
    match = re.search(pattern, line)
    if not match:
        return None

    test_raw = match.group(1).strip()
    value_raw = match.group(2).strip()
    unit_raw = _clean_unit(match.group(3).strip() or "-")

    try:
        value = float(value_raw)
    except ValueError:
        return None

    if len(test_raw) < 2:
        return None
    if _is_non_result_line(test_raw):
        return None
    # For generic report compatibility:
    # - accept known tests regardless of unit
    # - accept unknown tests only when unit looks medically plausible
    if not _has_known_alias(test_raw):
        if unit_raw == "-" or unit_raw.lower() not in KNOWN_UNITS:
            return None

    return {
        "test": _normalize_name(test_raw),
        "original_test": test_raw,
        "value": value,
        "unit": unit_raw,
        "source_line": line,
    }


def _compute_row_confidence(row: Dict[str, str]) -> int:
    score = 35
    if row.get("test") and row.get("test") != row.get("original_test", "").lower():
        score += 20
    if isinstance(row.get("value"), (float, int)):
        score += 15
    unit = (row.get("unit") or "").lower()
    if unit in KNOWN_UNITS:
        score += 15
    if row.get("ref_low") is not None and row.get("ref_high") is not None:
        score += 15
    source = row.get("source_line", "")
    if len(source) > 8 and any(ch.isdigit() for ch in source):
        score += 10
    return max(0, min(100, score))


def extract_lab_values(ocr_text: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    seen = set()
    raw_lines = [_normalize_spaces(line) for line in ocr_text.splitlines()]
    candidate_lines = [line for line in raw_lines if line]
    candidate_lines = _merge_split_lines(candidate_lines)

    for line in candidate_lines:
        if not line:
            continue
        if _is_non_result_line(line):
            continue
        parsed = (
            _extract_tabular_line(line)
            or _extract_tabular_without_unit(line)
            or _extract_value_unit(line)
        )
        if not parsed:
            continue
        key = (parsed["test"], parsed["value"], parsed["unit"])
        if key in seen:
            continue
        parsed["confidence"] = _compute_row_confidence(parsed)
        parsed["confidence_warning"] = (
            "low_ocr_confidence" if parsed["confidence"] < 60 else ""
        )
        seen.add(key)
        rows.append(parsed)
    return rows
