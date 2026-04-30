# SehatNama AI - Pakistani Lab Report Analyzer

Real-world healthcare AI project for Pakistan: upload a lab report image/PDF, extract test values with OCR, detect abnormal ranges, and explain findings in English + Urdu.

## Why this project is real (not API glue)

- Solves a local problem: most patients receive technical lab reports without understandable explanation.
- Runs without paid LLM APIs (no OpenRouter/Apify).
- Uses your core AI strengths:
  - Computer Vision / OCR for report reading
  - Clinical-NLP style parsing from noisy text
  - Rule-based medical interpretation with Pakistani lab ranges
- Produces patient-friendly bilingual output.

## Current MVP Features

- Upload report files (`PDF`, `JPG`, `PNG`)
- OCR extraction from scans and image-based PDFs
- Multi-mode OCR (`fast`, `balanced`, `max_accuracy`) for latency/accuracy tradeoff
- Parsing common CBC/LFT/RFT/diabetes markers
- Abnormality flagging (high/low) with reference ranges
- Per-row confidence scoring and low-confidence warnings
- Unit normalization + sanity checks to catch OCR outliers
- Template profile detection (`CBC`, `BMP`, `LFT`, `RFT`, `GENERIC`)
- English + Urdu patient explanation
- Downloadable summary text report + structured JSON export

## Tech Stack

- Python
- Streamlit
- OpenCV
- PyMuPDF
- pytesseract
- Rule-based clinical parser and range engine
- Optional local translation model (`Helsinki-NLP/opus-mt-en-ur`)

## Project Structure

```text
pakistan-lab-report-ai/
  app.py
  requirements.txt
  src/
    ocr_engine.py
    parser.py
    range_checker.py
    explainer.py
    translator.py
```

## Setup

1. Create and activate a virtual environment
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR engine (required by `pytesseract`)
   - Windows (recommended):

```powershell
winget install UB-Mannheim.TesseractOCR
```

   - Then close and reopen terminal/Streamlit so PATH refreshes.

4. Run app:

```bash
streamlit run app.py
```

5. Optional benchmark dashboard:

```bash
streamlit run pages/01_Benchmark_Dashboard.py
```

Use `benchmark-data/sample_benchmark_dataset.json` as starter dataset.

## Demo Flow

1. Upload a Pakistani lab report (CBC/LFT/RFT style).
2. Choose patient sex and age.
3. Review:
   - parsed results table
   - abnormal flags
   - English explanation
   - Urdu explanation
4. Download summary for sharing with family/doctor.

## Safety and Ethics

- This project is **not** a diagnosis tool.
- It is for educational support and report readability.
- Final medical decisions must be made by licensed doctors.

## Roadmap (for strong GitHub progression)

- [ ] Add OCR quality confidence scoring
- [ ] Add table-cell extraction with document layout models
- [ ] Add pediatric and pregnancy-specific ranges
- [ ] Add chest X-ray module with Grad-CAM explainability
- [ ] Add clinical validation sheet with doctor-reviewed cases
- [ ] Expand benchmark set to 100+ anonymized local reports with versioned metrics

## Portfolio Positioning

Use this repo title/description on GitHub:

- **Title:** `SehatNama AI: Pakistan Lab Report Interpreter`
- **Description:** `Computer Vision + Clinical NLP system that converts Pakistani lab report scans into bilingual patient explanations and abnormality alerts.`
