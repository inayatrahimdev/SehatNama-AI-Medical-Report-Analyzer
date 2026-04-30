from typing import Dict, List, Optional, Tuple


# Approximate adult reference ranges common in local labs (educational use).
RANGE_TABLE = {
    "hemoglobin": {"male": (13.5, 17.5), "female": (12.0, 15.5), "unit": "g/dL"},
    "wbc": {"default": (4.0, 11.0), "unit": "x10^3/uL"},
    "rbc": {"male": (4.5, 5.9), "female": (4.1, 5.1), "unit": "x10^6/uL"},
    "platelets": {"default": (150, 450), "unit": "x10^3/uL"},
    "glucose_fasting": {"default": (70, 99), "unit": "mg/dL"},
    "hba1c": {"default": (4.0, 5.6), "unit": "%"},
    "creatinine": {"male": (0.74, 1.35), "female": (0.59, 1.04), "unit": "mg/dL"},
    "urea": {"default": (15, 40), "unit": "mg/dL"},
    "alt": {"default": (7, 56), "unit": "U/L"},
    "ast": {"default": (10, 40), "unit": "U/L"},
    "bilirubin_total": {"default": (0.2, 1.2), "unit": "mg/dL"},
    "cholesterol_total": {"default": (0, 199), "unit": "mg/dL"},
    "sodium": {"default": (135, 145), "unit": "mEq/L"},
    "potassium": {"default": (3.5, 5.0), "unit": "mEq/L"},
    "chloride": {"default": (98, 107), "unit": "mEq/L"},
    "carbon_dioxide": {"default": (22, 32), "unit": "mEq/L"},
    "blood_urea_nitrogen": {"default": (7, 20), "unit": "mg/dL"},
    "glucose": {"default": (70, 100), "unit": "mg/dL"},
}


def _pick_range(test: str, sex: str) -> Optional[Tuple[float, float, str]]:
    item = RANGE_TABLE.get(test)
    if not item:
        return None
    if sex in item:
        low, high = item[sex]
    elif "default" in item:
        low, high = item["default"]
    else:
        return None
    return low, high, item["unit"]


def _status(value: float, low: float, high: float) -> str:
    if value < low:
        return "low"
    if value > high:
        return "high"
    return "normal"


def check_abnormalities(
    parsed_rows: List[Dict], sex: str = "male", age: int = 24
) -> List[Dict]:
    _ = age  # Reserved for future age-specific ranges.
    out: List[Dict] = []
    for row in parsed_rows:
        # Prefer report-provided reference ranges when OCR captured them.
        if row.get("ref_low") is not None and row.get("ref_high") is not None:
            low = float(row["ref_low"])
            high = float(row["ref_high"])
            ref_unit = row.get("ref_unit") or row.get("unit") or "-"
        else:
            picked = _pick_range(row["test"], sex=sex)
            if not picked:
                continue
            low, high, ref_unit = picked

        current_status = _status(row["value"], low, high)
        if current_status == "normal":
            continue
        out.append(
            {
                "test": row["test"],
                "original_test": row.get("original_test", row["test"]),
                "value": row["value"],
                "unit": row["unit"] or ref_unit,
                "status": current_status,
                "expected_range": f"{low} - {high} {ref_unit}",
            }
        )
    return out
