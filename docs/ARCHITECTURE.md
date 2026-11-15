# MotherlyPulse System Architecture

## 1. High-Level Pipeline

MotherlyPulse uses a **deterministic-first clinical safety pipeline** in which emergency triage always precedes any optional generative AI inference:

```text
User Input (Telegram Bot / HTTP API / CLI)
   │
   ▼
[1. DynamicTriageClassifier]  ──(Emergency detected)──► Immediate 112 Escalation
   │                                                      (Deterministic Bypass)
   ▼ (Priority / Routine)
[2. Context Retrieval & Language Detection]
   │
   ▼
[3. AIModelConnector]
   ├── backend=disabled (Default)                ──► DeterministicReference Passages
   ├── backend=remote (/v1/chat/completions)     ──► Optional llama-server (Chewie 1.2 GGUF)
   ├── backend=remote (/generate, /compare)      ──► Optional Cloud GPU FastAPI Server
   └── backend=local                             ──► Optional Local Transformers + PEFT
   │
   ▼
[4. ClinicalInvariantValidator] (for AI outputs)
   ├── Category Prefix Check (EMERGENCY: / PRIORITY: / ROUTINE:)
   ├── Contraindicated Substance Check (aspirin, ibuprofen, agbo, ogogoro, kaun, etc.)
   └── Emergency 112 Escalation Check (when urgency == Emergency)
   │
   ├── PASS ──► Validated AI Response
   └── FAIL / Timeout ──► DeterministicReference Fallback (MotherlyPulse_Data passages)
```

## 2. Deployment Modes

- **Deterministic Mode (Default — `AI_MODEL_BACKEND=disabled`):** Runs Telegram long polling (`run_telegram_bot.py`), SQLite user/reminder persistence (`UserStore`), `DynamicTriageClassifier`, `PassageRetriever`, `LocationService`, and `ReminderEngine` using Python's standard library.
- **Optional Self-Hosted AI Mode (`AI_MODEL_BACKEND=remote`):** Connects `motherlypulse-bot` to an isolated `ghcr.io/ggml-org/llama.cpp:server` container over Docker's internal `ai_internal_net` network (`http://chewie-llm:8080/v1/chat/completions`) serving the exported `chewie-1.2-q4_k_m.gguf` model.

## 3. Component Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| Deterministic Triage & `112` Bypass | **Implemented & Active** | `motherlypulse_app/classifier.py` |
| Telegram Bot & Multilingual Flows | **Implemented & Active** | `motherlypulse_app/telegram_bot.py` |
| `ClinicalInvariantValidator` & Fallbacks | **Implemented & Active** | `motherlypulse_app/ai_connector.py` |
| Stdlib HTTP API (`GET /health`, `POST /api/chat`) | **Implemented (Local/API)** | `motherlypulse_app/server.py` |
| Chewie 1.2 QLoRA + `Q4_K_M` GGUF Adapter | **Experimental / Optional** | Offline-evaluated (`n=135`); disabled in default `.env.example` |
| Isolated Maternal Risk ML Module | **Implemented (Standalone)** | `maternal_risk_prediction/` (not wired into Telegram bot) |
| WhatsApp Production Webhook | **Scaffold Only** | `motherlypulse_app/whatsapp_adapter.py` |
