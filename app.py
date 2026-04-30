import io
import json
import time
from typing import Dict, List

import streamlit as st

from src.explainer import build_english_report, build_urdu_report
from src.ocr_engine import extract_text_from_file
from src.parser import detect_template_profile, extract_lab_values
from src.quality import normalize_and_validate_results
from src.range_checker import check_abnormalities
from src.report_fallback import (
    build_clinical_urdu_sections,
    detect_report_type,
    extract_clinical_sections,
)


st.set_page_config(
    page_title="SehatNama AI - Lab Report Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("SehatNama AI - Pakistani Lab Report Analyzer")
st.caption(
    "Upload a lab report image/PDF. The app extracts values, flags abnormal tests, and explains findings in English + Urdu."
)
st.warning(
    "Clinical safety note: This tool is for educational support only, not a medical diagnosis. Always confirm with a doctor."
)

with st.sidebar:
    st.header("Settings")
    sex = st.selectbox("Patient sex (for ranges)", ["male", "female"])
    age = st.number_input("Age", min_value=1, max_value=120, value=24)
    ocr_profile = st.selectbox(
        "OCR mode",
        ["fast", "balanced", "max_accuracy"],
        index=2,
        help="fast = lower latency, max_accuracy = heavier OCR passes.",
    )
    confidence_threshold = st.slider("Low-confidence warning threshold", 40, 95, 60, 5)
    show_raw_text = st.checkbox("Show OCR text", value=False)
    show_parsed_rows = st.checkbox("Show parsed rows", value=False)

uploaded_file = st.file_uploader(
    "Upload report (PDF/JPG/PNG/JPEG)", type=["pdf", "jpg", "jpeg", "png"]
)

if not uploaded_file:
    st.info("Upload one report file to start analysis.")
    st.stop()

file_bytes = uploaded_file.read()
if not file_bytes:
    st.error("Uploaded file is empty.")
    st.stop()


@st.cache_data(show_spinner=False)
def cached_ocr(file_name: str, file_bytes: bytes, profile: str) -> str:
    return extract_text_from_file(file_name, file_bytes, profile=profile)


with st.spinner("Running OCR and parsing report..."):
    t0 = time.perf_counter()
    try:
        ocr_text = cached_ocr(uploaded_file.name, file_bytes, ocr_profile)
    except Exception as exc:
        st.error(f"OCR setup error: {exc}")
        st.info(
            "Install Tesseract OCR and restart the app.\n\n"
            "Windows command:\n"
            "`winget install UB-Mannheim.TesseractOCR`\n\n"
            "If already installed, close Streamlit and run again so PATH updates are picked up."
        )
        st.stop()
    t1 = time.perf_counter()

    template_profile = detect_template_profile(ocr_text)
    parsed_rows = extract_lab_values(ocr_text)
    parsed_rows, quality_warnings = normalize_and_validate_results(parsed_rows)
    t2 = time.perf_counter()
    abnormalities = check_abnormalities(parsed_rows, sex=sex, age=int(age))
    t3 = time.perf_counter()

if show_raw_text:
    st.subheader("OCR Output")
    st.code(ocr_text if ocr_text else "[No text extracted]")

if show_parsed_rows:
    st.subheader("Parsed Lab Rows")
    if parsed_rows:
        st.dataframe(parsed_rows, use_container_width=True)
    else:
        st.info("No structured test rows parsed.")

if not parsed_rows:
    report_type = detect_report_type(ocr_text)
    st.subheader("OCR Preview (first lines)")
    preview = "\n".join((ocr_text or "").splitlines()[:25]).strip()
    st.code(preview if preview else "[No OCR text extracted]")

    if report_type == "clinical":
        st.info(
            "Detected a clinical narrative report (not a numeric lab table). "
            "Showing structured clinical summary below."
        )
        sections = extract_clinical_sections(ocr_text)
        urdu_sections = build_clinical_urdu_sections(sections)

        left_en, right_ur = st.columns(2)
        ordered_sections = [
            "patient information",
            "consulting physician",
            "symptoms",
            "diagnosis",
            "treatment plan",
            "prescription",
            "follow-up",
            "follow up",
            "conclusion",
            "recommendations",
        ]
        with left_en:
            st.subheader("Clinical Summary (English)")
            for sec in ordered_sections:
                if sections.get(sec):
                    st.markdown(f"**{sec.title()}**")
                    for item in sections[sec]:
                        st.write(f"- {item}")
        with right_ur:
            st.subheader("طبی خلاصہ (Urdu)")
            rendered_ur_sections = set()
            for sec in ordered_sections:
                ur_sec_name = {
                    "patient information": "مریض کی معلومات",
                    "consulting physician": "معالج ڈاکٹر",
                    "symptoms": "علامات",
                    "diagnosis": "تشخیص",
                    "treatment plan": "علاج کا منصوبہ",
                    "prescription": "ادویات",
                    "follow-up": "فالو اَپ",
                    "follow up": "فالو اَپ",
                    "conclusion": "نتیجہ",
                    "recommendations": "ہدایات",
                }.get(sec)
                if (
                    ur_sec_name
                    and urdu_sections.get(ur_sec_name)
                    and ur_sec_name not in rendered_ur_sections
                ):
                    rendered_ur_sections.add(ur_sec_name)
                    st.markdown(f"**{ur_sec_name}**")
                    for item in urdu_sections[ur_sec_name]:
                        st.write(f"- {item}")

        clinical_payload = {
            "report_type": "clinical",
            "sections_english": sections,
            "sections_urdu": urdu_sections,
        }
        st.download_button(
            "Download Clinical Summary JSON",
            data=json.dumps(clinical_payload, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="sehatnama_clinical_summary.json",
            mime="application/json",
        )
        st.stop()

    st.error(
        "Could not parse structured lab values from this file yet. "
        "Try uploading a clearer lab report export/scan or share this OCR preview for parser tuning."
    )
    st.stop()

st.caption(
    f"OCR + parser extracted **{len(parsed_rows)}** test rows; "
    f"flagged **{len(abnormalities)}** abnormal findings."
)
st.caption(f"Detected report profile: **{template_profile.upper()}**")
lat_ocr_ms = round((t1 - t0) * 1000, 2)
lat_parse_ms = round((t2 - t1) * 1000, 2)
lat_check_ms = round((t3 - t2) * 1000, 2)
lat_total_ms = round((t3 - t0) * 1000, 2)
lat_cols = st.columns(4)
lat_cols[0].metric("OCR ms", lat_ocr_ms)
lat_cols[1].metric("Parse+Normalize ms", lat_parse_ms)
lat_cols[2].metric("Flagging ms", lat_check_ms)
lat_cols[3].metric("Total ms", lat_total_ms)

low_conf_rows = [r for r in parsed_rows if int(r.get("confidence", 0)) < confidence_threshold]
if low_conf_rows:
    st.warning(
        f"{len(low_conf_rows)} rows are below confidence threshold ({confidence_threshold}). "
        "Please manually verify these entries."
    )
if quality_warnings:
    with st.expander("Quality warnings"):
        for w in quality_warnings:
            st.write(f"- {w}")

left, right = st.columns([1.25, 1.0])

with left:
    st.subheader("Detected Results")
    st.dataframe(parsed_rows, use_container_width=True)

with right:
    st.subheader("Abnormal Flags")
    if not abnormalities:
        st.success("All recognized values appear within configured ranges.")
    else:
        flagged = [
            {
                "test": item["test"],
                "value": item["value"],
                "unit": item["unit"],
                "status": item["status"],
                "expected_range": item["expected_range"],
            }
            for item in abnormalities
        ]
        st.dataframe(flagged, use_container_width=True)

st.markdown("---")

english_report = build_english_report(abnormalities, sex=sex, age=int(age))
urdu_report = build_urdu_report(abnormalities, sex=sex, age=int(age))

col1, col2 = st.columns(2)
with col1:
    st.subheader("Patient Explanation (English)")
    st.markdown(english_report)

with col2:
    st.subheader("مریض کے لئے وضاحت (Urdu)")
    st.markdown(urdu_report)

report_buffer = io.StringIO()
report_buffer.write("SEHATNAMA AI - LAB REPORT SUMMARY\n")
report_buffer.write(f"Patient sex: {sex}\nAge: {int(age)}\n\n")
report_buffer.write("ENGLISH SUMMARY\n")
report_buffer.write(english_report + "\n\n")
report_buffer.write("URDU SUMMARY\n")
report_buffer.write(urdu_report + "\n")

st.download_button(
    "Download Summary (.txt)",
    data=report_buffer.getvalue().encode("utf-8"),
    file_name="sehatnama_summary.txt",
    mime="text/plain",
)

json_payload = {
    "profile": {"sex": sex, "age": int(age), "template_profile": template_profile},
    "quality": {
        "rows_extracted": len(parsed_rows),
        "abnormal_count": len(abnormalities),
        "low_confidence_count": len(low_conf_rows),
        "warnings": quality_warnings,
    },
    "detected_results": parsed_rows,
    "abnormal_flags": abnormalities,
    "english_report": english_report,
    "urdu_report": urdu_report,
}
st.download_button(
    "Download Structured JSON",
    data=json.dumps(json_payload, ensure_ascii=False, indent=2).encode("utf-8"),
    file_name="sehatnama_result.json",
    mime="application/json",
)
