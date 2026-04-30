from typing import Dict, List


EXPLANATION_HINTS_EN = {
    "hemoglobin": "May indicate anemia or dehydration depending on low/high direction.",
    "wbc": "Can shift in infection, inflammation, or immune stress.",
    "rbc": "Can relate to anemia, blood loss, or chronic oxygen changes.",
    "platelets": "May affect clotting risk when significantly low or high.",
    "glucose_fasting": "Important for diabetes and metabolic risk screening.",
    "hba1c": "Shows average blood sugar over roughly 3 months.",
    "creatinine": "Common marker related to kidney filtration.",
    "urea": "Can rise with kidney stress, dehydration, or protein metabolism changes.",
    "alt": "Liver enzyme; high values can indicate liver inflammation/injury.",
    "ast": "Liver/muscle-associated enzyme; interpret with ALT and clinical context.",
    "bilirubin_total": "Can rise with liver/bile flow issues or blood breakdown changes.",
    "cholesterol_total": "Lipid risk marker for long-term cardiovascular health.",
    "sodium": "Reflects body fluid/electrolyte balance and hydration status.",
    "potassium": "Important for heart rhythm and muscle/nerve function.",
    "chloride": "Helps assess hydration and acid-base balance.",
    "carbon_dioxide": "Related to bicarbonate/acid-base status in blood chemistry.",
    "blood_urea_nitrogen": "Kidney-related marker affected by hydration and protein metabolism.",
    "glucose": "Screens blood sugar level for metabolic risk.",
}


URDU_NAME_MAP = {
    "hemoglobin": "ہیموگلوبن",
    "wbc": "وائٹ بلڈ سیلز",
    "rbc": "ریڈ بلڈ سیلز",
    "platelets": "پلیٹ لیٹس",
    "glucose_fasting": "فاسٹنگ شوگر",
    "hba1c": "ایچ بی اے ون سی",
    "creatinine": "کریاٹینین",
    "urea": "یوریا",
    "alt": "اے ایل ٹی",
    "ast": "اے ایس ٹی",
    "bilirubin_total": "بلیروبن",
    "cholesterol_total": "کولیسٹرول",
    "sodium": "سوڈیم",
    "potassium": "پوٹاشیم",
    "chloride": "کلورائیڈ",
    "carbon_dioxide": "کاربن ڈائی آکسائیڈ",
    "blood_urea_nitrogen": "بلڈ یوریا نائٹروجن",
    "glucose": "گلوکوز",
}


def build_english_report(abnormalities: List[Dict], sex: str, age: int) -> str:
    header = f"**Profile:** {sex.title()}, {age} years\n\n"
    if not abnormalities:
        return header + "- No major abnormality detected in recognized tests.\n- Continue routine check-ups and healthy lifestyle."

    lines = [header, "**Flagged findings:**"]
    for item in abnormalities:
        hint = EXPLANATION_HINTS_EN.get(
            item["test"], "Needs clinical interpretation with full history."
        )
        lines.append(
            f"- **{item['original_test']}** is **{item['status'].upper()}** "
            f"({item['value']} {item['unit']}; expected {item['expected_range']}). {hint}"
        )

    lines.extend(
        [
            "",
            "**Next steps:**",
            "- Repeat test if result quality is doubtful (fasting/sample handling can affect values).",
            "- Discuss abnormal markers with a licensed physician for diagnosis.",
            "- Do not self-medicate based on this summary.",
        ]
    )
    return "\n".join(lines)


def build_urdu_report(abnormalities: List[Dict], sex: str, age: int) -> str:
    urdu_sex = "مرد" if str(sex).lower() == "male" else "خاتون"
    header = f"**پروفائل:** {urdu_sex}، عمر {age} سال\n\n"
    if not abnormalities:
        return (
            header
            + "- پہچانے گئے ٹیسٹ میں کوئی بڑی غیر معمولی خرابی نظر نہیں آئی۔\n"
            + "- باقاعدہ چیک اپ اور صحت مند طرزِ زندگی جاری رکھیں۔"
        )

    lines = [header, "**اہم نتائج:**"]
    for item in abnormalities:
        urdu_name = URDU_NAME_MAP.get(item["test"], item["original_test"])
        status = "کم" if item["status"] == "low" else "زیادہ"
        lines.append(
            f"- **{urdu_name}** کی قدر **{status}** ہے "
            f"({item['value']} {item['unit']})۔ متوقع حد: {item['expected_range']}۔"
        )

    lines.extend(
        [
            "",
            "**اگلا قدم:**",
            "- اپنی رپورٹ ڈاکٹر کو دکھائیں تاکہ مکمل طبی تاریخ کے ساتھ درست تشخیص ہو۔",
            "- اگر رپورٹ/نمونہ کے معیار میں شک ہو تو ٹیسٹ دوبارہ کروائیں۔",
            "- اس خلاصے کی بنیاد پر خود سے دوا شروع نہ کریں۔",
        ]
    )
    return "\n".join(lines)
