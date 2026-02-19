# Gujarati Cross-Lingual Voice Assistant
## Project Overview & Technical Documentation

---

## 1. Problem Statement

Millions of Gujarati speakers speak in **regional dialects** (Surti, Kathiawari, Charotari, etc.) that differ significantly from Standard Gujarati. Existing speech AI systems are trained only on Standard Gujarati, making them:

- **Inaccurate** for dialect speakers
- **Inaccessible** to rural and non-urban populations
- **Biased** toward urban, educated, formal speech

**The gap:** A Surti speaker says *"Poyro kem cho?"* — a Standard Gujarati ASR fails to recognize it. A Kathiawari speaker says *"Shu chho?"* — wrong transcription. People who understand one Gujarati dialect but not another are left without tools.

---

## 2. Project Vision

> Build a **dialect-aware Gujarati voice assistant** that understands what the user says in *any* major Gujarati dialect, processes it intelligently, and responds back in clear speech or text.

**Core idea in one sentence:**
*User speaks in their dialect → AI understands it → AI thinks → AI responds in speech or text.*

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER                             │
│         speaks in Gujarati dialect                  │
└──────────────────────┬──────────────────────────────┘
                       │ voice input
                       ▼
┌─────────────────────────────────────────────────────┐
│            ASR  (Speech-to-Text)                    │
│  Dialect-aware Whisper / wav2vec2 fine-tuned on:    │
│  • Standard Gujarati  • Surti                       │
│  • Kathiawari         • Charotari                   │
│  Output: Gujarati text transcript                   │
└──────────────────────┬──────────────────────────────┘
                       │ text
                       ▼
┌─────────────────────────────────────────────────────┐
│            NLU  (Language Understanding)            │
│  • Dialect identification (which dialect?)          │
│  • Intent + entity extraction                       │
│  • Normalize to Standard Gujarati for processing   │
└──────────────────────┬──────────────────────────────┘
                       │ normalized query
                       ▼
┌─────────────────────────────────────────────────────┐
│            AI BRAIN  (LLM / Response Gen)           │
│  • Generates response in Standard Gujarati          │
│  • Optionally translates back to user's dialect    │
└──────────────────────┬──────────────────────────────┘
                       │ response text
                       ▼
┌─────────────────────────────────────────────────────┐
│            TTS  (Text-to-Speech)                    │
│  • Synthesizes Gujarati speech                      │
│  • Dialect-appropriate pronunciation               │
└──────────────────────┬──────────────────────────────┘
                       │ audio / text
                       ▼
┌─────────────────────────────────────────────────────┐
│                    USER                             │
│       receives AI response as speech or text        │
└─────────────────────────────────────────────────────┘
```

---

## 4. Dialects Supported (Phase 1)

| Dialect | Region | Approx. Speakers | Script |
|---|---|---|---|
| Standard Gujarati | Ahmedabad, Gandhinagar | ~55M | Gujarati |
| Surti | Surat, South Gujarat | ~8M | Gujarati |
| Kathiawari | Rajkot, Saurashtra | ~15M | Gujarati |
| Charotari | Anand, Kheda, Charotar | ~5M | Gujarati |

---

## 5. Data Collection (Completed)

### Phase 1 — Scraping
- **Source:** YouTube comments (via `youtube-comment-downloader` + `yt-dlp`)
- **Method:** 3-phase: seed videos → auto search → regional news websites
- **Quality filters:** Gujarati script ≥50%, length 15–300 chars, no spam/duplicates

### Phase 2 — Balancing
- Each dialect balanced to exactly **500 sentences**
- Equal class weight → model does not lean toward any dialect
- Files: `*_balanced.csv` in `data/raw/<Dialect>/`

### Dataset Summary

| Dialect | Raw | Balanced | Status |
|---|---|---|---|
| Standard Gujarati | 994 | 500 | ✅ |
| Kathiawari | 479 | 500* | 🔄 top-up in progress |
| Surti | 500 | 500* | 🔄 top-up in progress |
| Charotari | 500 | 500* | 🔄 top-up in progress |

**Total: 2,000 balanced training sentences**

---

## 6. Technology Stack (Planned)

| Layer | Technology |
|---|---|
| **ASR** | OpenAI Whisper (fine-tuned) or Wav2Vec2 (gu) |
| **Dialect ID** | FastText / IndicBERT / multilingual BERT |
| **NLU / LLM** | IndicBERT, MuRIL, or fine-tuned LLaMA |
| **TTS** | Coqui TTS / IndicTTS (Gujarati voice) |
| **Backend API** | FastAPI (Python) |
| **Frontend** | React / Next.js or mobile app |

---

## 7. Model Training Plan

### Step 1 — Dialect Classifier
- Input: Gujarati sentence (text)
- Output: Dialect label (standard / surti / kathiawari / charotari)
- Training data: `data/combined/combined_train.csv`
- Model: Fine-tune IndicBERT or MuRIL

### Step 2 — ASR Fine-tuning
- Base: `openai/whisper-small` or `facebook/wav2vec2-base`
- Fine-tune on Gujarati dialect audio data (to be collected)
- Evaluation: WER (Word Error Rate) per dialect

### Step 3 — Response Generation
- Use existing Gujarati LLM or fine-tune on dialect corpus
- Normalize dialect → Standard → generate response

### Step 4 — TTS
- Use IndicTTS or Coqui TTS with Gujarati voice
- Post-process for dialect-appropriate output

---

## 8. Evaluation Metrics

| Component | Metric |
|---|---|
| Dialect Classifier | Accuracy, F1 per class |
| ASR | WER (Word Error Rate) per dialect |
| End-to-End | User comprehension score (human eval) |
| TTS | MOS (Mean Opinion Score) |

---

## 9. Project Phases

| Phase | Goal | Status |
|---|---|---|
| **Phase 1** | Data collection & balancing | ✅ In progress |
| **Phase 2** | Dialect classifier model | 🔜 Next |
| **Phase 3** | ASR fine-tuning + audio data | 🔜 Planned |
| **Phase 4** | End-to-end pipeline (ASR→NLU→LLM→TTS) | 🔜 Planned |
| **Phase 5** | API + Frontend / App | 🔜 Planned |

---

## 10. File & Folder Structure

```
Cross Lingual Project(gujarati)/
│
├── README.md                        ← quick start
├── docs/
│   └── project_overview.md          ← this file
│
├── data/
│   ├── raw/                         ← dialect-specific scraped data
│   │   ├── Standard Gujarati/
│   │   │   ├── standard_gujarati_final.csv
│   │   │   └── standard_gujarati_balanced.csv
│   │   ├── Kathiawari/
│   │   │   ├── kathiawari_final.csv
│   │   │   └── kathiawari_balanced.csv
│   │   ├── Surti/
│   │   │   ├── surti_final.csv
│   │   │   └── surti_balanced.csv
│   │   └── Charotari/
│   │       ├── charotari_final.csv
│   │       └── charotari_balanced.csv
│   ├── processed/                   ← cleaned, tokenized, encoded data
│   └── combined/                    ← merged training splits
│       ├── combined_train.csv       ← 80% (1600 rows)
│       ├── combined_val.csv         ← 10% (200 rows)
│       └── combined_test.csv        ← 10% (200 rows)
│
├── scrapers/                        ← data collection scripts
│   ├── scrape_top4.py               ← main 4-dialect scraper
│   ├── balance_data.py              ← equalizes to 500/dialect
│   ├── topup_gaps.py                ← fills shortfalls
│   └── dialect_cleaner.py           ← strict post-cleaner
│
├── notebooks/                       ← Jupyter exploration
│   └── (EDA, quality checks, model experiments)
│
├── src/                             ← application source code
│   ├── asr/                         ← Speech-to-Text module
│   ├── nlu/                         ← Dialect ID + understanding
│   ├── tts/                         ← Text-to-Speech module
│   └── api/                         ← FastAPI backend
│
├── models/                          ← saved model checkpoints
│   ├── asr/
│   ├── nlu/
│   └── tts/
│
└── total_lang.csv                   ← full dialect reference table
```

---

*Document version: 1.0 | Created: 2026-02-19*
