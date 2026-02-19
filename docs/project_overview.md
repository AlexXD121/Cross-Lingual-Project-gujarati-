# Gujarati Cross-Lingual Voice Assistant
## Full Technical Documentation v2.0

---

## 1. Problem Statement

Millions of Gujarati speakers use regional dialects (Surti, Kathiawari, Charotari) that current speech AI systems fail to understand. Existing tools are biased toward Standard Gujarati, leaving dialect speakers without accessible AI tools.

**Key challenge:** A Surti speaker saying *"Poyro kem cho?"* fails in standard Gujarati ASR. A person who understands one Gujarati dialect but not another has no way to bridge the gap today.

---

## 2. Vision

> Build a **dialect-aware Gujarati voice assistant** powered by RAG + LLM that understands dialect speech, thinks intelligently, responds in voice or text, and **learns from every mistake it makes**.

---

## 3. Full System Architecture

### 3.1 Pipeline Overview

```
Voice Input (any dialect)
    ↓
[ASR] Speech-to-Text — Whisper fine-tuned on 4 Gujarati dialects
    ↓
[NLU] Dialect Identification — MuRIL/IndicBERT classifier
    ↓
[RAG] Context Retrieval — FAISS/ChromaDB vector store
    ↓
[LLM] Response Generation — IndicBERT / LLaMA 3
    ↓
[SELF-LEARNING] Mistake log → auto-update RAG knowledge base
    ↓
[TTS] Text-to-Speech — Coqui TTS / IndicTTS
    ↓
Voice or Text Response
```

### 3.2 RAG Architecture (Retrieval-Augmented Generation)

Instead of the model relying only on its weights, RAG retrieves real dialect knowledge at inference time:

```
User query text
    │
    ▼
sentence-transformers  →  query embedding (768-dim vector)
    │
    ▼
FAISS / ChromaDB       →  top-k similar chunks retrieved
    │                      from dialect knowledge base
    ▼
Prompt construction    →  [CONTEXT: retrieved dialect chunks]
                          [QUERY: user input]
    │
    ▼
LLM (IndicBERT/LLaMA)  →  context-grounded response
```

**What the RAG knowledge base contains:**
- 2,000 balanced dialect sentences (500 per dialect)
- Dialect vocabulary mappings (e.g., Surti "poyro" = Standard "chokro")
- Intent-response pairs per dialect
- Error corrections from self-learning store

### 3.3 Self-Learning from Mistakes

The model improves continuously without full retraining:

```python
# Conceptual flow
if user_corrects_response or confidence < THRESHOLD:
    mistake = {
        "input": original_query,
        "wrong_output": model_response,
        "correction": user_correction,
        "dialect": detected_dialect,
        "timestamp": now()
    }
    mistake_store.append(mistake)           # log the error
    embedding = embed(mistake["correction"]) # re-embed correction
    vector_db.upsert(embedding, mistake)    # inject into RAG
    # Next time same query → correct context retrieved → correct answer
```

**Effect:** Every correction makes the model smarter for *all future users* with similar queries, without retraining.

---

## 4. Technology Stack

### Core ML
| Component | Tool | Notes |
|---|---|---|
| ASR | `openai/whisper-small` | Fine-tune on Gujarati dialect audio |
| ASR alt | `facebook/wav2vec2-base` | Lower latency option |
| Dialect ID | `google/muril-base-cased` | 17 Indian languages pretrained |
| Embeddings | `sentence-transformers/paraphrase-multilingual` | Gujarati-aware embeddings |
| Vector DB | `FAISS` (local) / `ChromaDB` (persistent) | RAG retrieval |
| LLM | `ai4bharat/indic-gpt` or `LLaMA-3-8B` fine-tuned | Response generation |
| TTS | `Coqui TTS` / `IndicTTS` | Gujarati speech synthesis |

### Infrastructure
| Component | Tool |
|---|---|
| Backend API | `FastAPI` + `Uvicorn` |
| Frontend | `React` / `Next.js` |
| Experiment tracking | `MLflow` or `Weights & Biases` |
| Data versioning | `DVC` |
| Containerization | `Docker` |

### Data Collection (done ✅)
| Tool | Purpose |
|---|---|
| `yt-dlp` | YouTube video discovery |
| `youtube-comment-downloader` | Extract dialect comments |
| `requests` + `BeautifulSoup` | Regional news site scraping |

---

## 5. Dataset

### 5.1 What was collected
| Dialect | Region | Balanced Rows | File |
|---|---|---|---|
| Standard Gujarati | Ahmedabad | 500 | `standard_gujarati_balanced.csv` |
| Surti | Surat | 500 | `surti_balanced.csv` |
| Kathiawari | Rajkot/Saurashtra | 500 | `kathiawari_balanced.csv` |
| Charotari | Anand/Kheda | 500 | `charotari_balanced.csv` |

**Total: 2,000 rows — equal class weight — model will not lean toward any dialect.**

### 5.2 Quality filters applied
- Gujarati script ratio ≥ 50%
- Length: 15–300 characters
- No duplicates
- No spam (emoji-only, pure English, subscribe bait)

---

## 6. Model Training Plan

### Step 1 — Dialect Classifier
- **Input:** Gujarati sentence (text)
- **Output:** `standard` / `surti` / `kathiawari` / `charotari`
- **Model:** Fine-tune `google/muril-base-cased`
- **Data:** `data/combined/combined_train.csv`
- **Metric:** F1 per class, overall accuracy

### Step 2 — RAG Knowledge Base Setup
- Embed all 2,000 sentences using `sentence-transformers`
- Index in FAISS (local) and ChromaDB (persistent)
- Add dialect vocabulary mappings as additional documents

### Step 3 — ASR Fine-tuning
- **Base:** `openai/whisper-small`
- **Data needed:** Gujarati dialect audio (to be recorded/crowdsourced)
- **Metric:** WER (Word Error Rate) per dialect — target <15%

### Step 4 — LLM Integration + RAG
- Prompt = `[Context from RAG] + [User query]`
- Model generates dialect-normalized response
- Log all low-confidence outputs for self-learning

### Step 5 — TTS
- Gujarati Coqui TTS voice synthesis
- Optionally adapt prosody for each dialect

---

## 7. Self-Learning Implementation

### 7.1 Trigger conditions
- User explicitly corrects the response
- Model confidence score < 0.70
- User rates response as "wrong" in UI

### 7.2 Error store schema
```json
{
  "id": "uuid",
  "timestamp": "2026-02-19T20:00:00Z",
  "dialect": "surti",
  "input_text": "poyro kem cho bhai",
  "model_output": "...",
  "correction": "...",
  "confidence": 0.42,
  "embedded": true
}
```

### 7.3 Update cycle
- Errors embedded immediately (real-time RAG update)
- Full model re-fine-tune: weekly batch job using accumulated errors

---

## 8. Project Phases

| Phase | Goal | Status |
|---|---|---|
| **Phase 1** | Data collection & balancing | ✅ Done |
| **Phase 2** | Dialect classifier (MuRIL) | 🔜 Next |
| **Phase 3** | RAG pipeline (FAISS + embeddings) | 🔜 Planned |
| **Phase 4** | ASR fine-tuning (Whisper) | 🔜 Planned |
| **Phase 5** | LLM + RAG integration | 🔜 Planned |
| **Phase 6** | Self-learning loop | 🔜 Planned |
| **Phase 7** | TTS integration | 🔜 Planned |
| **Phase 8** | FastAPI backend + Frontend | 🔜 Planned |

---

## 9. Evaluation Metrics

| Component | Metric | Target |
|---|---|---|
| Dialect Classifier | F1 per dialect | > 0.85 |
| ASR | WER per dialect | < 15% |
| RAG retrieval | Precision@k | > 0.80 |
| End-to-end | Human comprehension score | > 80% |
| TTS | MOS (Mean Opinion Score) | > 3.5/5.0 |

---

*Version 2.0 | 2026-02-19*
