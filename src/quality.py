from typing import Dict, List, Tuple


UNIT_NORMALIZATION = {
    "mg/dl": "mg/dL",
    "g/dl": "g/dL",
    "meq/l": "mEq/L",
    "u/l": "U/L",
    "iu/l": "IU/L",
    "mmol/l": "mmol/L",
    "x10^3/ul": "x10^3/uL",
    "x10^6/ul": "x10^6/uL",
}

# Broad physiological sanity bounds for OCR-error detection only.
SANITY_LIMITS = {
    "hemoglobin": (2.0, 25.0),
    "wbc": (0.1, 200.0),
    "rbc": (0.5, 10.0),
    "platelets": (1.0, 2000.0),
    "glucose_fasting": (20.0, 700.0),
    "glucose": (20.0, 700.0),
    "hba1c": (2.0, 20.0),
    "creatinine": (0.1, 20.0),
    "urea": (1.0, 400.0),
    "blood_urea_nitrogen": (1.0, 300.0),
    "sodium": (90.0, 220.0),
    "potassium": (1.0, 12.0),
    "chloride": (60.0, 180.0),
    "carbon_dioxide": (5.0, 60.0),
    "alt": (1.0, 5000.0),
    "ast": (1.0, 5000.0),
    "bilirubin_total": (0.0, 60.0),
    "cholesterol_total": (50.0, 1200.0),
}


def _normalize_unit(unit: str) -> str:
    if not unit:
        return "-"
    low = unit.strip().lower()
    return UNIT_NORMALIZATION.get(low, unit.strip())


def normalize_and_validate_results(parsed_rows: List[Dict]) -> Tuple[List[Dict], List[str]]:
    normalized: List[Dict] = []
    warnings: List[str] = []

    for row in parsed_rows:
        row_copy = dict(row)
        row_copy["unit"] = _normalize_unit(str(row_copy.get("unit", "-")))
        if row_copy.get("ref_unit"):
            row_copy["ref_unit"] = _normalize_unit(str(row_copy.get("ref_unit", "-")))

        test_name = row_copy.get("test")
        value = row_copy.get("value")
        if test_name in SANITY_LIMITS and isinstance(value, (int, float)):
            low, high = SANITY_LIMITS[test_name]
            if value < low or value > high:
                warnings.append(
                    f"Possible OCR/value issue: {row_copy.get('original_test', test_name)}={value} "
                    f"{row_copy.get('unit', '')} is outside sanity bounds ({low}-{high})."
                )
                row_copy["confidence"] = min(int(row_copy.get("confidence", 60)), 45)
                row_copy["confidence_warning"] = "sanity_check_failed"

        if row_copy.get("confidence_warning"):
            warnings.append(
                f"Low confidence row: {row_copy.get('original_test', test_name)} "
                f"(confidence={row_copy.get('confidence', 0)})."
            )

        normalized.append(row_copy)

    return normalized, warnings
