# MotherlyPulse System Architecture

## 1. High-Level Pipeline

MotherlyPulse implements a **Zero-Trust Hybrid Safety Pipeline** in which deterministic clinical triage always precedes and wraps generative AI inference:

```text
User Input (Telegram Bot / HTTP API / CLI)
   │
   ▼
[1. DynamicTriageClassifier]  ──(Emergency detected)──► Immediate 112 Escalation
   │                                                      (0.05 ms, Zero Neural Risk)
   ▼ (Priority / Routine)
[2. Context Retrieval & Language Detection]
   │
   ▼
[3. AIModelConnector]
   ├── backend=remote (OpenAI /v1/chat/completions) ──► VPS llama-server (chewie-1.2-q4_k_m.gguf)
   ├── backend=remote (/generate, /compare)         ──► Cloud GPU FastAPI Server
   ├── backend=local                                ──► Local Transformers + PEFT Adapter
   └── backend=disabled / timeout / error           ──► DeterministicReference Fallback
   │
   ▼
[4. ClinicalInvariantValidator]
   ├── Category Prefix Check (EMERGENCY: / PRIORITY: / ROUTINE:)
   ├── Contraindicated Substance Check (aspirin, ibuprofen, agbo, ogogoro, kaun, etc.)
   └── Emergency 112 Escalation Check (when urgency == Emergency)
   │
   ├── PASS ──► Verified AI Response
   └── FAIL ──► Approved Deterministic Fallback (MotherlyPulseData passages)
```

## 2. Deployment Topology (24/7 VPS Setup)

- **`motherlypulse-bot` Container:** `python:3.11-slim-bookworm` (~18 MiB RAM / 512 MiB limit). Runs Telegram long polling, SQLite user/reminder persistence (`UserStore`), `DynamicTriageClassifier`, `ClinicalInvariantValidator`, `LocationService`, and `ReminderEngine`.
- **`chewie-llm` Container:** `ghcr.io/ggml-org/llama.cpp:server` (~1.18 GiB RAM / 2.5 GiB limit) serving `chewie-1.2-q4_k_m.gguf` on CPU (`--ctx-size 2048 --threads 3 --n-gpu-layers 0`).
- **Network Isolation:** `chewie-llm` has zero public ports and communicates with `motherlypulse-bot` strictly over Docker's internal `ai_internal_net` network (`http://chewie-llm:8080/v1/chat/completions`).

## 3. Completed vs. Proposed Components

| Component | Status | Notes |
| :--- | :--- | :--- |
| Deterministic Triage & `112` Bypass | **Completed & Deployed** | `motherlypulse_app/classifier.py` |
| Telegram Bot & Multilingual Flows | **Completed & Deployed** | `motherlypulse_app/telegram_bot.py` (`@MotherlyPulse_bot`) |
| `ClinicalInvariantValidator` & Fallbacks | **Completed & Deployed** | `motherlypulse_app/ai_connector.py` |
| Chewie 1.2 QLoRA + `Q4_K_M` GGUF Server | **Completed & Deployed** | `chewie-llm` + `motherlypulse-bot` on Netcup VPS |
| Stdlib HTTP API (`GET /health`, `POST /api/chat`) | **Completed (Local/API)** | `motherlypulse_app/server.py` |
| Isolated Maternal Risk ML Module | **Completed (Standalone)** | `maternal_risk_prediction/` (awaiting live bot integration) |
| WhatsApp Production Webhook | **Proposed / Adapter Stub** | `motherlypulse_app/whatsapp_adapter.py` |

