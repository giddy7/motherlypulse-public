# MotherlyPulse System Architecture

MotherlyPulse separates **application safety and logic** from **containerized VPS deployment** so that emergency triage, clinical guardrails, and user persistence remain independent of any generative model backend.

---

## 1. Application Architecture

All clinical triage, retrieval, validation, and user-state management execute inside the Python application (`motherlypulse_app/`):

```text
User Input (Telegram Bot / HTTP API / CLI)
   │
   ▼
[1. DynamicTriageClassifier]  ──(Emergency detected)──► Immediate 112 Escalation
   │                                                      (Deterministic Bypass)
   ▼ (Priority / Routine)
[2. Context Retrieval & Language Detection] (English / Yorùbá / Nigerian Pidgin)
   │
   ▼
[3. AIModelConnector]
   ├── backend=disabled (Safe template default)  ──► DeterministicReference Passages
   ├── backend=remote (/v1/chat/completions)     ──► chewie-llm (llama-server Q4_K_M GGUF)
   ├── backend=remote (/generate, /compare)      ──► Optional Dual-Model GPU Demo Server
   └── backend=local                             ──► Local Transformers + PEFT Adapter
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

---

## 2. Deployment Architecture

In production on the Linux VPS, MotherlyPulse runs as a two-container Docker Compose stack (`motherlypulse`), isolated within `/opt/apps/motherlypulse/`:

- **`motherlypulse-bot` (`python:3.11-slim-bookworm`, non-root `10001:10001`, `1.0` CPU, `512 MiB` RAM):** Handles outbound HTTPS Telegram long polling (`@MotherlyPulse_bot`), `DynamicTriageClassifier`, `ClinicalInvariantValidator`, `LocationService`, `ReminderEngine`, and SQLite WAL persistence (`./data/motherlypulse_user_store.db`).
- **`chewie-llm` (`ghcr.io/ggml-org/llama.cpp:server`, `3.0` CPUs, `2560 MiB` RAM):** Serves `chewie-1.2-q4_k_m.gguf` (mounted read-only `:ro`) over an internal-only Docker bridge network (`http://chewie-llm:8080/v1/chat/completions`) with zero public host ports.

See [DEPLOYMENT.md](DEPLOYMENT.md) for full container topology, backup arrangements, security hardening, and verification results.

---

## 3. Component Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| Deterministic Triage & `112` Bypass | **Implemented & Verified** | `motherlypulse_app/classifier.py` (runs locally in `motherlypulse-bot`) |
| Telegram Bot & Multilingual Flows | **Implemented & Verified** | `motherlypulse_app/telegram_bot.py` (`@MotherlyPulse_bot`) |
| `ClinicalInvariantValidator` & Fallbacks | **Implemented & Verified** | `motherlypulse_app/ai_connector.py` |
| VPS `chewie-llm` (`llama.cpp:server` `Q4_K_M`) | **Deployed & Verified** | Internal bridge inference (`8.91s` verified check); `.env.example` defaults to `disabled` |
| `/compare` Dual-Model A/B Demo | **Partially Implemented** | Works with dual-model GPU endpoint; unavailable on single-model `chewie-llm` VPS stack |
| Stdlib HTTP API (`GET /health`, `POST /api/chat`) | **Implemented (Local/API)** | `motherlypulse_app/server.py` |
| Isolated Maternal Risk ML Module | **Implemented (Standalone)** | `maternal_risk_prediction/` (not wired into Telegram bot) |
| WhatsApp Production Webhook | **Scaffold Only** | `motherlypulse_app/whatsapp_adapter.py` |
