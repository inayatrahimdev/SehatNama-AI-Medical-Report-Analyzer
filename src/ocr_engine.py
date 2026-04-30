import os
import re
from typing import List

import cv2
import fitz
import numpy as np
import pytesseract
from pytesseract import TesseractNotFoundError


def _configure_tesseract_path() -> None:
    # Try common Windows install locations so users don't have to edit code.
    if os.name != "nt":
        return
    if pytesseract.pytesseract.tesseract_cmd != "tesseract":
        return

    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for exe_path in candidates:
        if os.path.exists(exe_path):
            pytesseract.pytesseract.tesseract_cmd = exe_path
            return


def ensure_tesseract_available() -> None:
    _configure_tesseract_path()
    try:
        _ = pytesseract.get_tesseract_version()
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed or not available in PATH. "
            "Install it, then restart Streamlit. "
            "Windows quick install: `winget install UB-Mannheim.TesseractOCR`"
        ) from exc


def _prepare_image_variants(image: np.ndarray) -> List[np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Upscale small scans for better character separation.
    h, w = gray.shape[:2]
    if min(h, w) < 1300:
        gray = cv2.resize(gray, None, fx=1.8, fy=1.8, interpolation=cv2.INTER_CUBIC)

    denoised = cv2.bilateralFilter(gray, 7, 85, 85)
    adaptive_binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35,
        11,
    )
    adaptive_inv = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        35,
        11,
    )
    kernel = np.ones((1, 1), np.uint8)
    cleaned_binary = cv2.morphologyEx(adaptive_binary, cv2.MORPH_OPEN, kernel)
    cleaned_inv = cv2.morphologyEx(adaptive_inv, cv2.MORPH_OPEN, kernel)
    return [cleaned_binary, cleaned_inv, denoised]


def _score_ocr_text(text: str) -> int:
    if not text:
        return 0
    low = text.lower()
    lab_keywords = [
        "test",
        "result",
        "reference",
        "range",
        "glucose",
        "creatinine",
        "hemoglobin",
        "platelet",
        "sodium",
        "potassium",
        "chloride",
        "urea",
        "bilirubin",
        "wbc",
        "rbc",
    ]
    keyword_hits = sum(1 for k in lab_keywords if k in low)
    numbers = len(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    units = len(re.findall(r"\b(?:mg/dl|g/dl|meq/l|iu/l|u/l|mmol/l|%)\b", low))
    return keyword_hits * 10 + units * 4 + numbers


def _normalize_ocr_text(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "mEql": "mEq/L",
        "mEqI": "mEq/L",
        "mEq|L": "mEq/L",
        "C1": "Cl",
        "C02": "CO2",
        "Medica!": "Medical",
        "Date of test": "Date of test",
        "Reference  range": "Reference range",
    }
    out = text
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _ocr_image_array(image: np.ndarray, profile: str = "balanced") -> str:
    ensure_tesseract_available()
    variants = _prepare_image_variants(image)
    if profile == "fast":
        variants = variants[:1]
        rotations = [None]
        psm_modes = [6]
    elif profile == "max_accuracy":
        rotations = [
            None,
            cv2.ROTATE_90_CLOCKWISE,
            cv2.ROTATE_90_COUNTERCLOCKWISE,
            cv2.ROTATE_180,
        ]
        psm_modes = [4, 6, 11, 12]
    else:
        rotations = [None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE]
        psm_modes = [6, 11]

    best_text = ""
    best_score = -1
    for variant in variants:
        for rot in rotations:
            candidate = cv2.rotate(variant, rot) if rot is not None else variant
            for psm in psm_modes:
                config = f"--oem 3 --psm {psm}"
                text = pytesseract.image_to_string(candidate, config=config)
                score = _score_ocr_text(text)
                if score > best_score:
                    best_score = score
                    best_text = text

    return _normalize_ocr_text(best_text)


def _extract_from_pdf(pdf_bytes: bytes, profile: str = "balanced") -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text: List[str] = []

    for page in doc:
        direct_text = page.get_text("text").strip()
        if direct_text:
            pages_text.append(_normalize_ocr_text(direct_text))
            continue

        ensure_tesseract_available()
        pix = page.get_pixmap(dpi=220)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        pages_text.append(_normalize_ocr_text(_ocr_image_array(img, profile=profile)))

    return "\n".join([p for p in pages_text if p]).strip()


def extract_text_from_file(
    file_name: str, file_bytes: bytes, profile: str = "balanced"
) -> str:
    lower = file_name.lower()
    if lower.endswith(".pdf"):
        return _extract_from_pdf(file_bytes, profile=profile)

    image_np = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    if image is None:
        return ""
    return _ocr_image_array(image, profile=profile).strip()
