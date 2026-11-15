# Technical Overview

## 1. Application Modules (`motherlypulse_app/`)

| Module | Responsibility |
| :--- | :--- |
| `telegram_bot.py` | Telegram Bot API long-polling handler, `/start`, `/language`, `/profile`, `/remind`, `/clinic`, `/compare`, `/delete`, and emergency preemption. |
| `assistant.py` | Core response orchestrator combining `DynamicTriageClassifier`, `PassageRetriever`, `AIModelConnector`, and `TemplateAdapter`. |
| `classifier.py` | Deterministic keyword + fuzzy regex triage engine (`Emergency`, `Priority`, `Routine`) and multilingual detection (`English`, `Yoruba`, `Nigerian Pidgin`). |
| `ai_connector.py` | `ClinicalInvariantValidator` and `AIModelConnector` supporting `disabled`, `mock`, `local`, and `remote` (custom `/generate`+`/compare` and OpenAI `/v1/chat/completions`) backends with bounded HTTP timeouts. |
| `user_store.py` | SQLite persistence for user profiles, registration state, reminders, and GDPR-style right-to-erasure (`/delete`). |
| `location_service.py` | Haversine distance lookup and LGA/town search across 55 Primary Health Centres (PHCs) in Ondo State. |
| `reminders.py` | Antenatal appointment, daily medication, and NPHCDA routine infant immunization scheduling (BCG, OPV, Pentavalent, Measles, Yellow Fever). |
| `retriever.py` | Grounded passage retrieval over `MotherlyPulse_Data/02_Passages/`. |
| `server.py` | Zero-dependency Python stdlib HTTP server (`GET /health`, `POST /api/chat`). |
| `cli.py` | Interactive terminal runner for local testing without Telegram. |
| `whatsapp_adapter.py` | Adapter scaffold for future WhatsApp Business Cloud API integration. |

## 2. Standalone Maternal Risk Prediction (`maternal_risk_prediction/`)

An isolated `scikit-learn` module trained on 30,000 synthetic ANC records across low-, moderate-, and high-burden LMIC settings (`age_years`, `gravidity`, `parity`, `gestational_age_weeks`, `bmi_pre_pregnancy`, `systolic_bp_mmhg`, `diastolic_bp_mmhg`, `hemoglobin_gdl`, `fasting_glucose_mgdl`, `proteinuria`, `hiv_status`, `anc_visits`). Exposes `MaternalRiskPredictor` in `src/predictor.py` with WHO-aligned clinical rules.

## 3. Runtime Dependencies & Deployment Footprint

The core `motherlypulse_app` runtime relies on Python 3.10+ standard library (`sqlite3`, `urllib.request`, `http.server`, `json`, `re`, `logging`) with zero heavy ML packages inside the bot container. In the Docker Compose VPS deployment, the bot container runs alongside an isolated `llama.cpp` server container; see [DEPLOYMENT.md](DEPLOYMENT.md) and [`../docker-compose.example.yml`](../docker-compose.example.yml). `requirements.txt` lists `numpy`, `scipy`, `scikit-learn`, and `pandas` for the standalone risk-prediction and evaluation pipelines.

