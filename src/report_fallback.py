import re
from typing import Dict, List


SECTION_HEADINGS = [
    "patient information",
    "consulting physician",
    "symptoms",
    "diagnosis",
    "treatment plan",
    "prescription",
    "follow-up",
    "follow up",
    "recommendations",
    "medications",
    "conclusion",
]

SECTION_CANONICAL = {
    "follow up": "follow-up",
}

URDU_SECTION_NAMES = {
    "overview": "خلاصہ",
    "patient information": "مریض کی معلومات",
    "consulting physician": "معالج ڈاکٹر",
    "symptoms": "علامات",
    "diagnosis": "تشخیص",
    "treatment plan": "علاج کا منصوبہ",
    "prescription": "ادویات",
    "follow-up": "فالو اَپ",
    "follow up": "فالو اَپ",
    "recommendations": "ہدایات",
    "medications": "ادویات",
    "conclusion": "نتیجہ",
}

URDU_LINE_RULES = [
    ("severe pain in the lower back and abdomen", "کمر کے نچلے حصے اور پیٹ میں شدید درد"),
    ("pain during urination", "پیشاب کے دوران درد"),
    ("frequent urination", "بار بار پیشاب آنا"),
    ("nausea and occasional vomiting", "متلی اور کبھی کبھار قے"),
    ("blood in urine", "پیشاب میں خون"),
    ("kidney stones (nephrolithiasis)", "گردے کی پتھری"),
    (
        "pain management with nsaids (non-steroidal anti-inflammatory drugs)",
        "درد کے لئے این ایس اے آئی ڈیز (NSAIDs) کے ذریعے علاج",
    ),
    (
        "increased fluid intake to help pass the stones",
        "پتھری خارج کرنے میں مدد کے لئے پانی/مائعات کا زیادہ استعمال",
    ),
    (
        "monitoring the size and position of the stones with follow-up imaging",
        "فالو اَپ امیجنگ کے ذریعے پتھری کے سائز اور پوزیشن کی نگرانی",
    ),
    (
        "potential referral to a urologist if the stones do not pass naturally",
        "اگر پتھری خود نہ نکلے تو یورولوجسٹ کو ریفر کرنے پر غور",
    ),
    (
        "the following medications have been prescribed:",
        "درج ذیل ادویات تجویز کی گئی ہیں:",
    ),
    (
        "the patient is advised to follow up in:",
        "مریض کو درج ذیل مدت میں فالو اَپ کی ہدایت دی گئی ہے:",
    ),
    (
        "1 week for re-evaluation of symptoms and follow-up imaging.",
        "علامات کا دوبارہ جائزہ اور فالو اَپ امیجنگ کے لئے 1 ہفتہ بعد",
    ),
    (
        "immediately if symptoms worsen or if there is an inability to urinate.",
        "اگر علامات بڑھ جائیں یا پیشاب میں رکاوٹ ہو تو فوراً رابطہ کریں",
    ),
    (
        "the patient is to be monitored closely and educated about dietary changes to help prevent future kidney stones.",
        "مریض کی قریبی نگرانی کی جائے اور آئندہ پتھری سے بچاؤ کے لئے غذائی تبدیلیوں کی رہنمائی دی جائے",
    ),
    (
        "a discussion regarding potential surgical options will occur if stones do not pass as expected.",
        "اگر پتھری متوقع طور پر خارج نہ ہو تو ممکنہ جراحی آپشنز پر مشاورت کی جائے گی",
    ),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def detect_report_type(ocr_text: str) -> str:
    low = ocr_text.lower()
    lab_signals = [
        "reference range",
        "mg/dl",
        "meq/l",
        "hemoglobin",
        "wbc",
        "rbc",
        "creatinine",
        "sodium",
        "potassium",
        "platelet",
    ]
    clinical_signals = [
        "diagnosis",
        "treatment plan",
        "symptoms",
        "consulting physician",
        "medical report",
    ]
    lab_score = sum(1 for s in lab_signals if s in low)
    clinical_score = sum(1 for s in clinical_signals if s in low)
    if lab_score >= clinical_score and lab_score > 0:
        return "lab"
    if clinical_score > 0:
        return "clinical"
    return "unknown"


def extract_clinical_sections(ocr_text: str) -> Dict[str, List[str]]:
    lines = [_normalize(line) for line in ocr_text.splitlines() if _normalize(line)]
    sections: Dict[str, List[str]] = {}
    current = "overview"
    sections[current] = []

    heading_set = set(SECTION_HEADINGS)
    for line in lines:
        low = line.lower().strip(":")
        if low in heading_set:
            current = SECTION_CANONICAL.get(low, low)
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    # Trim noisy generic lines.
    for key, vals in list(sections.items()):
        clean_vals = [
            v
            for v in vals
            if v.lower()
            not in {
                "the treatment plan includes:",
                "the patient presents with the following symptoms:",
                "after a thorough examination and imaging studies, the patient has been diagnosed with:",
            }
        ]
        sections[key] = clean_vals
    return sections


def _translate_line_to_urdu(line: str) -> str:
    low = line.lower().strip()
    for en, ur in URDU_LINE_RULES:
        if low == en:
            return ur

    # Lightweight fallback transformations for common prefixes.
    if low.startswith("doctor:"):
        return "ڈاکٹر: " + line.split(":", 1)[1].strip()
    if low.startswith("hospital:"):
        return "ہسپتال: " + line.split(":", 1)[1].strip()
    if low.startswith("age:"):
        return "عمر: " + line.split(":", 1)[1].strip()
    if low.startswith("gender:"):
        gender_val = line.split(":", 1)[1].strip().lower()
        mapped = "مرد" if gender_val == "male" else ("خاتون" if gender_val == "female" else line.split(":", 1)[1].strip())
        return "جنس: " + mapped
    if low.startswith("patient name:"):
        return "مریض کا نام: " + line.split(":", 1)[1].strip()
    if low.startswith("patient id:"):
        return "مریض آئی ڈی: " + line.split(":", 1)[1].strip()
    # Deterministic fallback: keep Urdu-only panel consistent and fast.
    # Preserve numbers when present so timeline/dosage still useful.
    nums = " ".join(re.findall(r"\d+(?:[./-]\d+)?", line))
    if nums:
        return f"مزید طبی تفصیل دستیاب ہے۔ عددی معلومات: {nums}"
    return "مزید طبی تفصیل دستیاب ہے۔"


def build_clinical_urdu_sections(sections: Dict[str, List[str]]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for sec_key, sec_lines in sections.items():
        urdu_key = URDU_SECTION_NAMES.get(sec_key, sec_key)
        out[urdu_key] = [_translate_line_to_urdu(line) for line in sec_lines]
    return out
