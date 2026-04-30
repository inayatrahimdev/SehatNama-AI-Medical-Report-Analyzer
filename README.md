# SehatNama AI - Medical Report znalyzer

SehatNama AI is a healthcare document Analyzer system designed for Pakistan-focused use cases. It processes medical PDFs/images, extracts structured findings, highlights risky values when present, and generates bilingual patient-facing summaries in English and Urdu.

This is not a chatbot wrapper and does not depend on paid LLM APIs for core functionality.

## Problem We Solve

Medical reports are often difficult for patients and families to understand, especially when:

- report format changes across hospitals and clinics,
- scans are noisy or rotated,
- content mixes narrative sections with numeric findings,
- the patient needs explanation in Urdu.

SehatNama AI turns those reports into structured, readable output with quality warnings and machine-friendly JSON export.

## Product Capabilities

- Accepts `PDF`, `JPG`, `JPEG`, and `PNG` medical reports.
- Multi-pass OCR pipeline with configurable modes:
  - `fast` for lower latency
  - `balanced`
  - `max_accuracy` for strongest extraction
- Handles both:
  - numeric result reports
  - clinical narrative reports (symptoms, diagnosis, treatment, prescription, follow-up)
- Per-row confidence scoring with low-confidence warnings.
- Unit normalization and sanity checks for reliability.
- Structured bilingual summaries (English + Urdu).
- Structured JSON export for API/backoffice integration.
- Benchmark dashboard with precision/recall/F1 and latency analytics.

## Architecture (Industry Style)

1. **Ingestion Layer**  
   File upload, type detection, PDF rendering, image decode.

2. **OCR Layer**  
   Multi-variant preprocessing + rotation + OCR mode search.

3. **Normalization Layer**  
   OCR cleanup, unit normalization, numeric standardization.

4. **Extraction Layer**  
   Rule-based parsers for numeric rows and narrative sections.

5. **Validation Layer**  
   Confidence scoring + physiological sanity checks + warnings.

6. **Output Layer**  
   English/Urdu clinical summaries + machine-readable JSON.

7. **Evaluation Layer**  
   Dataset benchmarking with error analysis and latency metrics.

## Stack

- Python
- Streamlit
- OpenCV
- PyMuPDF
- pytesseract (Tesseract OCR)
- pandas
- unittest / pytest-compatible workflow

## Repository Layout

```text
pakistan-lab-report-ai/
  app.py
  requirements.txt
  benchmark-data/
  pages/
    01_Benchmark_Dashboard.py
  src/
    ocr_engine.py
    parser.py
    report_fallback.py
    quality.py
    range_checker.py
    explainer.py
    benchmarking.py
    translator.py
  tests/
    test_pipeline.py
```

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR (Windows):

```powershell
winget install UB-Mannheim.TesseractOCR
```

3. Restart terminal, then run:

```bash
streamlit run app.py
```

4. Optional benchmark dashboard:

```bash
streamlit run pages/01_Benchmark_Dashboard.py
```

Use `benchmark-data/sample_benchmark_dataset.json` as starter dataset.

## Reliability and Quality Controls

- Low-confidence row detection with configurable threshold.
- Sanity-bound validation for implausible values.
- Template/profile detection for document routing.
- Structured error analysis through benchmark dashboard.

## Safety

- Not a diagnosis system.
- Not a replacement for licensed medical advice.
- Intended for report readability, triage support, and workflow acceleration.

## Deployment

Designed to deploy on Streamlit Cloud with minimal setup:

- Keep repo lightweight and modular.
- Use benchmark dashboard before each release.
- Track precision/recall/F1 and latency per version.

## Roadmap

- Add 100+ anonymized local report benchmark set.
- Add model-assisted layout detection for complex table documents.
- Add stronger Urdu medical phrasing coverage.
- Add clinical governance checklist and release QA gates.
