# 🔷 Transforge

**Intelligent document transformation powered by Amazon Bedrock Data Automation + Claude.**

Transforge takes unstructured documents (`.docx`, `.pdf`) and transforms them into clean, structured reports — automatically detecting the document type and applying the right extraction pipeline.

## Supported Document Types

| Input Document | Output Report | Extraction Method |
|---|---|---|
| Pharmacy Prescription Dispensing Record | 7-section Medication Dispensing Report | BDA Blueprint (single-page) / Claude (multi-page) |
| Clinical Trial Safety Report | 7-section Clinical Trial Analysis Report | BDA standard output + Claude |

---

## Architecture

```
                              ┌─────────────────────────────────────────────┐
                              │              Amazon Bedrock                  │
                              │                                             │
┌──────────┐   ┌─────────┐   │  ┌─────────────────────────────────────┐    │   ┌──────────────┐
│  Browser  │──▶│  Flask   │──▶│  │  BDA (Data Automation)             │    │──▶│  Structured  │
│  Upload   │   │  Server  │   │  │  ┌─────────────┐ ┌──────────────┐ │    │   │  .docx       │
│ (.docx/   │   │          │   │  │  │  Standard   │ │   Custom     │ │    │   │  Download    │
│  .pdf)    │   │          │   │  │  │  Output     │ │   Output     │ │    │   └──────────────┘
└──────────┘   │          │   │  │  │  (per-page  │ │  (blueprint  │ │    │
                │          │   │  │  │   text)     │ │   fields)    │ │    │
                │          │   │  │  └──────┬──────┘ └──────┬───────┘ │    │
                │          │   │  └─────────┼───────────────┼─────────┘    │
                │          │   │            │               │              │
                │          │   │            ▼               ▼              │
                │          │   │  ┌─────────────────────────────────────┐  │
                │          │   │  │  Claude Sonnet 4.5 (InvokeModel)   │  │
                │          │   │  │  • Document classification         │  │
                │          │   │  │  • Multi-page field extraction     │  │
                │          │   │  │  • Clinical trial structuring      │  │
                │          │   │  └─────────────────────────────────────┘  │
                │          │   └─────────────────────────────────────────────┘
                │          │
                │    ┌─────┴──────┐
                │    │  Amazon S3  │
                │    │  (staging)  │
                │    └────────────┘
                └─────────┘
```

### Request Flow

```
User Upload
    │
    ▼
Flask /transform endpoint
    │
    ├── Upload file to S3
    │
    ├── Invoke BDA Async (InvokeDataAutomationAsync)
    │       │
    │       ├── Standard Output → per-page text with layout analysis
    │       └── Custom Output   → blueprint-extracted fields (40+ pharmacy fields)
    │
    ├── Poll GetDataAutomationStatus until complete
    │
    ├── Read standard output (per-page text)
    │
    ├── Claude classifies document type
    │       │
    │       ├── "prescription" ──┐
    │       │                    ├── Single-page → use BDA custom output directly
    │       │                    └── Multi-page  → Claude extracts per-prescription
    │       │
    │       └── "clinical_trial" → Claude extracts structured trial data
    │
    ├── Generate .docx in target format (python-docx)
    │
    ├── Cleanup S3 artifacts
    │
    └── Return .docx to browser
```

---

## Technical Components

### 1. Amazon Bedrock Data Automation (BDA)

BDA is the core document processing engine. It handles file ingestion, layout analysis, and structured extraction.

| Component | Resource | Purpose |
|---|---|---|
| **Blueprint** | `pharmacy-prescription-extractor` | Defines 40+ extraction fields with natural-language instructions per field. Each field has `inferenceType: "explicit"` so BDA looks for exact matches in the document. |
| **Project** | `doc-transformer-project` (ASYNC) | Wraps the blueprint into a deployable project. Configured with page-level granularity for standard output and the blueprint for custom output. |
| **S3 Bucket** | `doc-transformer-bda-*` | Staging area — input files are uploaded here, BDA writes output here, then artifacts are cleaned up after processing. |
| **Profile** | `us.data-automation-v1` | Cross-region inference profile for BDA runtime invocation. |

**Why BDA and not just Claude?**
- BDA provides native document understanding — layout analysis, bounding boxes, page segmentation
- The blueprint ensures consistent, schema-driven extraction across varying document formats
- Standard output gives per-page text with structural awareness (not just raw OCR)
- Works with both `.docx` and `.pdf` without custom parsing
- Async processing scales for production workloads

### 2. Claude Sonnet 4.5 (via Bedrock InvokeModel)

Claude handles three tasks that complement BDA:

| Task | When Used | Why |
|---|---|---|
| **Document Classification** | Every upload | Reads the first ~3000 chars of BDA's extracted text and classifies as `prescription` or `clinical_trial`. This routes the document to the correct extraction + generation pipeline. |
| **Multi-page Prescription Extraction** | Multi-page pharmacy docs | BDA's custom blueprint output treats the entire document as one unit. For multi-page prescriptions, Claude extracts fields from each prescription's text individually. |
| **Clinical Trial Structuring** | Clinical trial reports | Extracts ~50 structured fields across 10 categories (sponsor info, study overview, enrollment, efficacy, safety, PK, regulatory, risk-benefit) from the full document text. |

**Model**: `us.anthropic.claude-sonnet-4-5-20250929-v1:0` — chosen for high-quality structured extraction tasks.

### 3. Flask Backend

- Serves the frontend and handles `/transform` POST requests
- Manages the full BDA lifecycle: S3 upload → async invocation → polling → result parsing → cleanup
- Routes to the correct Doc2 generator based on document type
- Generates `.docx` output using `python-docx` with Courier New monospace formatting and ASCII table borders

### 4. Frontend

- Vanilla HTML/CSS/JS (no framework dependencies)
- S3-bucket-style drag-and-drop UI for upload and download
- Responsive pipeline layout: Input Bucket → Transform → Output Bucket
- Handles loading states, error display, and dynamic filename from server response

### 5. Amazon S3

- Used as a transient staging layer — BDA requires S3 URIs for input/output
- Files are uploaded under `input/{job_id}/` and BDA writes results to `output/{job_id}/`
- All artifacts are cleaned up after each transformation

---

## Project Structure

```
├── backend/
│   ├── app.py              # Flask app, BDA integration, Claude extraction, Doc2 generation
│   ├── bda_config.json     # BDA project/blueprint ARNs and S3 bucket name
│   └── setup_bda.py        # One-time script to create BDA Blueprint + Project
├── frontend/
│   ├── index.html          # Main UI template
│   └── static/
│       ├── app.js          # Upload, transform, download logic
│       └── style.css       # Dark theme, bucket UI, animations
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1

# One-time: Create BDA Blueprint + Project + S3 bucket
python3 backend/setup_bda.py

# Run the app
python3 backend/app.py
```

Open `http://localhost:5000` in your browser.

### Prerequisites

- Python 3.10+
- AWS account with Bedrock Data Automation access in `us-east-1`
- IAM user/role with `AmazonBedrockFullAccess` and `AmazonS3FullAccess`

---

## Adding New Document Types

Transforge is designed to be extensible. To add a new document type:

### Step 1: Update the Classifier

In `_classify_document()` in `backend/app.py`, add your new category:

```python
Categories:
- prescription
- clinical_trial
- invoice          # ← new
```

### Step 2: Create an Extraction Function

Write a `_extract_invoice(bedrock_rt, full_text)` function that prompts Claude with the JSON schema you want extracted. Follow the pattern of `_extract_clinical_trial()`:

```python
def _extract_invoice(bedrock_rt, full_text):
    prompt = f"""Extract structured data from this invoice. Return ONLY valid JSON...
    {{
      "vendor": {{ "name": "", "address": "" }},
      "line_items": [],
      "totals": {{ "subtotal": "", "tax": "", "total": "" }}
    }}
    ...
    Invoice text:
    {full_text}
    """
    # invoke Claude, parse JSON, return dict
```

### Step 3: Create a Doc2 Generator

Write a `generate_invoice_doc2(data)` function that takes the extracted dict and produces a `.docx`. Use the existing generators as templates — they use `python-docx` with ASCII table formatting.

### Step 4: Wire It Up in the Transform Route

In the `/transform` endpoint, add a branch for your new type:

```python
if doc_type == "clinical_trial":
    output_path = generate_clinical_trial_doc2(data)
elif doc_type == "invoice":
    output_path = generate_invoice_doc2(data)
```

### Optional: Add a BDA Blueprint

For document types where you want BDA's native extraction (instead of Claude), create a new blueprint in `setup_bda.py` with field definitions specific to your document type. This gives you schema-driven extraction with layout awareness.

---

## How BDA + Claude Work Together

```
┌─────────────────────────────────────────────────────────────────┐
│                    SINGLE-PAGE PRESCRIPTION                     │
│                                                                 │
│  BDA Blueprint ──▶ Custom Output (40+ fields) ──▶ Doc2 .docx   │
│  (direct extraction, no Claude needed)                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   MULTI-PAGE PRESCRIPTIONS                      │
│                                                                 │
│  BDA Standard Output ──▶ Per-page text ──▶ Group by Rx          │
│       │                                        │                │
│       └── Claude classifies as "prescription"  │                │
│                                                ▼                │
│                              Claude extracts fields per Rx      │
│                                                │                │
│                                                ▼                │
│                                    Multi-page Doc2 .docx        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CLINICAL TRIAL REPORT                        │
│                                                                 │
│  BDA Standard Output ──▶ Full text ──▶ Claude classifies        │
│                                              │                  │
│                              Claude extracts structured data    │
│                                              │                  │
│                              Clinical Trial Doc2 .docx          │
└─────────────────────────────────────────────────────────────────┘
```
