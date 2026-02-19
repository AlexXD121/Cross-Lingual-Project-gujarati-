# Gujarati Cross-Lingual Voice Assistant

> A dialect-aware voice AI for Gujarati speakers — understands regional dialects, responds in speech or text.

---

## What It Does

**User speaks in their dialect → AI understands → AI responds in speech or text**

Supports 4 major Gujarati dialects, each with 500 balanced training sentences:

| Dialect | Region |
|---|---|
| Standard Gujarati | Ahmedabad / Gandhinagar |
| Surti | Surat / South Gujarat |
| Kathiawari | Rajkot / Saurashtra |
| Charotari | Anand / Kheda |

---

## Pipeline

```
Voice Input → ASR → Dialect ID + NLU → AI LLM → TTS → Voice/Text Output
```

See [`docs/project_overview.md`](docs/project_overview.md) for full architecture.

---

## Project Structure

```
├── docs/               ← project documentation
├── data/
│   ├── raw/            ← scraped dialect data (500 rows each)
│   ├── processed/      ← cleaned & tokenized
│   └── combined/       ← train / val / test splits
├── scrapers/           ← data collection scripts
├── src/
│   ├── asr/            ← Speech-to-Text
│   ├── nlu/            ← Dialect understanding
│   ├── tts/            ← Text-to-Speech
│   └── api/            ← FastAPI backend
├── models/             ← saved model checkpoints
└── notebooks/          ← experiments & EDA
```

---

## Current Status

- [x] Phase 1 — Data collection & balancing (2,000 rows, 500/dialect)
- [ ] Phase 2 — Dialect classifier model
- [ ] Phase 3 — ASR fine-tuning
- [ ] Phase 4 — End-to-end pipeline
- [ ] Phase 5 — API + App
