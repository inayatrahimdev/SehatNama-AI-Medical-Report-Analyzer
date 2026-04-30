import unittest

from src.parser import detect_template_profile, extract_lab_values
from src.quality import normalize_and_validate_results
from src.range_checker import check_abnormalities
from src.report_fallback import extract_clinical_sections


SYNTHETIC_CASES = [
    ("Hemoglobin 11.2 g/dL 12.0 - 15.5 g/dL", "hemoglobin"),
    ("WBC 12.5 x10^3/uL 4.0 - 11.0 x10^3/uL", "wbc"),
    ("RBC 4.7 x10^6/uL 4.1 - 5.1 x10^6/uL", "rbc"),
    ("Platelets 220 x10^3/uL 150 - 450 x10^3/uL", "platelets"),
    ("Sodium (Na) 140 mEq/L 135 - 145 mEq/L", "sodium"),
    ("Potassium (K) 4.0 mEq/L 3.5 - 5.0 mEq/L", "potassium"),
    ("Chloride (Cl) 102 mEq/L 98 - 107 mEq/L", "chloride"),
    ("Carbon Dioxide 25 mEq/L 22 - 32 mEq/L", "carbon_dioxide"),
    ("Glucose 90 mg/dL 70 - 100 mg/dL", "glucose"),
    ("Fasting Glucose 108 mg/dL 70 - 99 mg/dL", "glucose_fasting"),
    ("HbA1c 6.3 % 4.0 - 5.6 %", "hba1c"),
    ("Blood Urea Nitrogen 15 mg/dL 7 - 20 mg/dL", "blood_urea_nitrogen"),
    ("Urea 32 mg/dL 15 - 40 mg/dL", "urea"),
    ("Creatinine 1.0 mg/dL 0.6 - 1.2 mg/dL", "creatinine"),
    ("ALT 62 U/L 7 - 56 U/L", "alt"),
    ("AST 45 U/L 10 - 40 U/L", "ast"),
    ("Total Bilirubin 1.4 mg/dL 0.2 - 1.2 mg/dL", "bilirubin_total"),
    ("Total Cholesterol 210 mg/dL 0 - 199 mg/dL", "cholesterol_total"),
    ("SGPT 40 U/L 7 - 56 U/L", "alt"),
    ("SGOT 38 U/L 10 - 40 U/L", "ast"),
    ("BUN 18 mg/dL 7 - 20 mg/dL", "blood_urea_nitrogen"),
    ("C02 24 mEq/L 22 - 32 mEq/L", "carbon_dioxide"),
]


class TestSehatNamaPipeline(unittest.TestCase):
    def test_20_plus_synthetic_cases_parse(self):
        self.assertGreaterEqual(len(SYNTHETIC_CASES), 20)
        for line, expected_test in SYNTHETIC_CASES:
            rows = extract_lab_values(line)
            self.assertTrue(rows, msg=f"No rows parsed for: {line}")
            self.assertEqual(rows[0]["test"], expected_test)

    def test_split_line_parsing(self):
        text = "Carbon Dioxide\n25 mEq/L 22 - 32 mEq/L\nCreatinine 1.0 mg/dL 0.6 - 1.2 mg/dL"
        rows = extract_lab_values(text)
        tests = [r["test"] for r in rows]
        self.assertIn("carbon_dioxide", tests)
        self.assertIn("creatinine", tests)

    def test_non_result_lines_filtered(self):
        text = "Patient Name Ahmad\nDate of birth 01-01-1990\nMedical record number 1111"
        rows = extract_lab_values(text)
        self.assertEqual(rows, [])

    def test_confidence_presence(self):
        rows = extract_lab_values("Sodium (Na) 140 mEq/L 135 - 145 mEq/L")
        self.assertIn("confidence", rows[0])
        self.assertGreaterEqual(rows[0]["confidence"], 60)

    def test_quality_normalization(self):
        rows = extract_lab_values("Sodium (Na) 140 meq/l 135 - 145 meq/l")
        normalized, warnings = normalize_and_validate_results(rows)
        self.assertEqual(normalized[0]["unit"], "mEq/L")
        self.assertEqual(normalized[0]["ref_unit"], "mEq/L")
        self.assertIsInstance(warnings, list)

    def test_sanity_warning_on_impossible_value(self):
        rows = extract_lab_values("Sodium (Na) 1000 mEq/L 135 - 145 mEq/L")
        normalized, warnings = normalize_and_validate_results(rows)
        self.assertTrue(any("sanity" in w.lower() for w in warnings))
        self.assertLess(normalized[0]["confidence"], 60)

    def test_profile_detection_bmp(self):
        text = "Sodium Potassium Chloride CO2 BUN Creatinine Glucose"
        self.assertEqual(detect_template_profile(text), "bmp")

    def test_profile_detection_cbc(self):
        text = "Hemoglobin WBC RBC Platelet Differential count"
        self.assertEqual(detect_template_profile(text), "cbc")

    def test_abnormality_detection(self):
        rows = extract_lab_values("ALT 88 U/L 7 - 56 U/L\nCreatinine 1.0 mg/dL 0.6 - 1.2 mg/dL")
        rows, _ = normalize_and_validate_results(rows)
        abnormal = check_abnormalities(rows, sex="male", age=35)
        self.assertEqual(len(abnormal), 1)
        self.assertEqual(abnormal[0]["test"], "alt")

    def test_follow_up_heading_canonicalization(self):
        text = (
            "Follow-Up\n"
            "The patient is advised to follow up in:\n"
            "1 week for review\n"
            "Follow up\n"
            "Immediately if severe pain"
        )
        sections = extract_clinical_sections(text)
        self.assertIn("follow-up", sections)
        self.assertNotIn("follow up", sections)


if __name__ == "__main__":
    unittest.main()
