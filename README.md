# MotherlyPulse

MotherlyPulse is a multilingual maternal and infant health support system built for Ondo State and Southwest Nigeria. It combines deterministic emergency triage, curated clinical guidance, Ondo State Primary Health Centre (PHC) discovery, and routine immunization reminders across **English**, **Èdè Yorùbá**, and **Nigerian Pidgin**.

---

## Overview

Delayed recognition of obstetric and neonatal danger signs, language barriers, harmful self-medication practices (such as *agbo* herbal concoctions or contraindicated NSAIDs during pregnancy), and difficulty locating nearby clinics contribute significantly to preventable maternal and neonatal morbidity.

MotherlyPulse addresses these gaps through a safety-first architecture:

- **Operational Telegram Application:** Guides pregnant women and infant caregivers through onboarding, multilingual health queries, clinic discovery, and scheduled care reminders.
- **Deterministic Emergency Triage & Clinical Guardrails:** Screens every incoming message for life-threatening danger signs before any generative model is called, escalating emergencies immediately to Nigeria's national emergency number **`112`**.
- **Experimental Language Model Research (`Chewie 1.2`):** Includes training scripts, offline evaluation benchmarks, and optional `llama.cpp` / remote inference adapters for a QLoRA fine-tuned `google/gemma-2-2b-it` model. In the repository's default deployment configuration, `AI_MODEL_BACKEND=disabled` (deterministic-only mode).

## Intended Users

- **Pregnant women and infant caregivers** seeking accessible antenatal/postnatal information, danger-sign escalation, clinic locations, and immunization reminders in English, Yorùbá, or Nigerian Pidgin.
- **Digital health engineers, ML practitioners, and public health researchers** exploring safety-scaffolded healthcare messaging systems and multilingual maternal health benchmarks.

## Key Features

- **3-Tier Clinical Triage (`EMERGENCY`, `PRIORITY`, `ROUTINE`):** Deterministic keyword and fuzzy regex classification (`motherlypulse_app/classifier.py`) across English, Yorùbá, and Nigerian Pidgin, with immediate `112` escalation for emergencies.
- **Clinical Invariant Validation:** Post-generation filter (`ClinicalInvariantValidator` in `motherlypulse_app/ai_connector.py`) that enforces triage prefixes, blocks contraindicated substances (*aspirin, ibuprofen, agbo, ogogoro, kaun, tetracycline*, etc.), and falls back to vetted `DeterministicReference` passages on rejection or timeout.
- **Telegram Bot (`motherlypulse_app/telegram_bot.py`):** Supports onboarding (`/start`), language switching (`/language`), profile management (`/profile`), PHC lookup (`/clinic` and GPS location sharing), reminders (`/remind`, `/remind_apt`, `/remind_med`, `/remind_vax`), optional A/B model comparison (`/compare`), and user data deletion (`/delete`).
- **Ondo State PHC Directory:** Haversine distance and LGA/town lookup across 55 Primary Health Centre records (`MotherlyPulse_Data/05_Facilities_Ondo/facilities.json`).
- **Immunization & Antenatal Reminders:** Automated scheduling aligned with the Nigerian NPHCDA routine infant immunization schedule (`MotherlyPulse_Data/07_Immunization_Ondo/national_immunization_schedule_nigeria.csv`).
- **Standalone Maternal Risk Prediction (`maternal_risk_prediction/`):** Isolated `scikit-learn` Random Forest models trained on 30,000 synthetic antenatal care (ANC) records for structured clinical risk and complication classification.
- **HTTP API & CLI:** Lightweight Python standard-library HTTP server (`GET /health`, `POST /api/chat` in `motherlypulse_app/server.py`) and interactive CLI (`motherlypulse_app/cli.py`).

## How the System Works

1. A user sends a message via Telegram, HTTP API, or CLI.
2. `DynamicTriageClassifier` evaluates the message locally across English, Yorùbá, and Nigerian Pidgin rules.
3. If `Emergency` danger signs are detected, the system bypasses generative AI entirely and returns deterministic `112` escalation guidance.
4. For `Priority` and `Routine` queries, `PassageRetriever` fetches grounded clinical passages from `MotherlyPulse_Data/02_Passages/`.
5. When `AI_MODEL_BACKEND=disabled` (the default configuration), the system serves vetted deterministic guidance directly. When an optional AI backend (`remote` or `local`) is enabled, `AIModelConnector` queries the model and passes the output through `ClinicalInvariantValidator`, falling back to deterministic passages if validation fails or the endpoint times out.

## System Architecture

```text
Incoming Message (Telegram / HTTP API / CLI)
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│ DynamicTriageClassifier (English / Yorùbá / Pidgin)      │
└───────────────────────────┬──────────────────────────────┘
                            │
       Emergency? ──────────┼── YES ──► Immediate 112 Escalation
                            │           (Deterministic Bypass)
                            ▼ NO (Priority / Routine)
┌──────────────────────────────────────────────────────────┐
│ Context Retrieval & AIModelConnector                     │
│                                                          │
│  Default (AI_MODEL_BACKEND=disabled):                    │
│    └─► DeterministicReference Passages & Templates       │
│                                                          │
│  Optional / Experimental (AI_MODEL_BACKEND=remote|local):│
│    ├─► Optional llama-server / Cloud GPU / Local PEFT    │
│    └─► ClinicalInvariantValidator                        │
│          ├─ PASS ──► Validated AI Response               │
│          └─ FAIL / Timeout ──► Deterministic Fallback    │
└──────────────────────────────────────────────────────────┘
```

For component details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/SAFETY_AND_VALIDATION.md](docs/SAFETY_AND_VALIDATION.md).

## Technology Stack

- **Core Application:** Python 3.10+ standard library (`sqlite3`, `urllib.request`, `http.server`, `json`, `re`, `logging`) — no heavy ML dependencies are required to run the deterministic bot or HTTP server.
- **ML, Risk Prediction & Evaluation Tooling:** `numpy`, `scipy`, `scikit-learn`, `pandas` (`requirements.txt`).
- **Experimental Fine-Tuning & Export:** `google/gemma-2-2b-it` (4-bit NF4 QLoRA via `transformers`, `peft`, `bitsandbytes`, `accelerate`) with optional `Q4_K_M` GGUF export for `llama.cpp` (`deployment/Export_Chewie_1_2_GGUF.ipynb`).
- **Storage:** SQLite (`UserStore` with WAL mode and `/delete` erasure).
- **Messaging & Deployment:** Telegram Bot API (long polling), Docker, and shell/systemd deployment scripts (`deployment/`).

## Repository Structure

```text
motherlypulse/
├── motherlypulse_app/          # Core application: bot, triage, validator, API, CLI, tests
│   ├── ai_connector.py         # ClinicalInvariantValidator & AIModelConnector
│   ├── assistant.py            # Response orchestration & deterministic fallback
│   ├── classifier.py           # DynamicTriageClassifier (EN / YO / PCM)
│   ├── telegram_bot.py         # TelegramBotHandler
│   ├── server.py               # Stdlib HTTP API (GET /health, POST /api/chat)
│   ├── cli.py                  # Interactive CLI runner
│   ├── location_service.py     # Ondo State 55-PHC lookup & Haversine distance
│   ├── reminders.py            # Antenatal, medication & NPHCDA immunization scheduler
│   ├── retriever.py            # Clinical passage retriever
│   ├── user_store.py           # SQLite persistence & right-to-erasure
│   └── tests/                  # Automated unit and integration tests
├── maternal_risk_prediction/   # Standalone scikit-learn ANC risk prediction module
├── data/                       # Canonical train (420), val (60), test (120) JSONL splits
├── MotherlyPulse_Data/         # Passages, emergency rules, 55 Ondo PHCs, evaluation reports
├── deployment/                 # Server setup scripts, Colab inference & GGUF export notebooks
├── eval_results/               # Offline evaluation CSVs and blinded rating sheets
├── experiments/                # Reproducible Chewie 1.2 QLoRA experiment & reports
├── models/                     # Chewie 1.2 model card & metadata
├── docs/                       # Architecture, technical overview, safety & data docs
├── DATASET_CARD.md             # Dataset documentation
├── .env.example                # Environment variable template
├── requirements.txt            # Python dependencies for ML/risk/eval tooling
├── run_telegram_bot.py         # Telegram bot entry point
└── LICENSE                     # MIT License
```

## Core Application Components

- **`motherlypulse_app/classifier.py`:** Deterministic multilingual danger-sign classifier (`Emergency`, `Priority`, `Routine`).
- **`motherlypulse_app/ai_connector.py`:** `ClinicalInvariantValidator` and `AIModelConnector` supporting `disabled`, `mock`, `local`, and `remote` (OpenAI-compatible `/v1/chat/completions` and custom `/generate` + `/compare`) backends with bounded HTTP timeouts.
- **`motherlypulse_app/telegram_bot.py`:** Stateful Telegram bot for user registration, reminders, PHC lookup, optional `/compare`, and `/delete`.
- **`motherlypulse_app/server.py` & `cli.py`:** HTTP API and terminal interfaces.
- **`maternal_risk_prediction/src/predictor.py`:** Standalone `MaternalRiskPredictor` for structured ANC vitals and lab inputs.

See [docs/TECHNICAL_OVERVIEW.md](docs/TECHNICAL_OVERVIEW.md) for module-level details.

## AI Architecture & Model Integration Status

MotherlyPulse separates **offline model research** from **production application serving**:

- **Production Serving Status:** The repository's `.env.example` and recorded deployment configuration set `AI_MODEL_BACKEND=disabled` (deterministic-only mode). While `AI_MODEL_BACKEND=remote` (for `llama.cpp` `llama-server` or a remote GPU endpoint) is implemented and covered by unit/integration tests with mocked HTTP calls, **Chewie 1.2 is not represented as an active live production inference service**.
- **Research Model (`Chewie 1.2`):** `google/gemma-2-2b-it` (revision `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`) fine-tuned via 4-bit NF4 QLoRA (`r=16`, `lora_alpha=32`, `lora_dropout=0.05`, attention projections only, `6,389,760` trainable parameters) for `1.514` epochs (`80` steps) on `420` multilingual pairs (`140` EN, `140` PCM, `140` YO).
- **Saved Research Artifacts:** Training logs, adapter config, checksums, Colab notebooks, and raw evaluation CSVs are stored in `experiments/chewie_1_2_fresh_experiment/`.

### Offline Held-Out Evaluation (`n = 135`: 120 `test_*.jsonl` + 15 `fixed_15` prompts)

Metrics below are reconciled from `experiments/chewie_1_2_fresh_experiment/01_baseline/chewie_1_2_fresh_baseline_eval.csv` and `03_post_eval/chewie_1_2_fresh_finetuned_eval.csv`:

| Metric | Baseline (`gemma-2-2b-it` 4-bit) | Fine-Tuned (`Chewie 1.2 QLoRA`) | Delta |
| :--- | ---: | ---: | ---: |
| Triage Prefix Compliance (`has_prefix`) | `0.00%` (0/135) | `88.89%` (120/135) | `+88.89 pp` |
| Clinical Safety (Excl. Prefix) | `88.15%` (119/135) | `88.89%` (120/135) | `+0.74 pp` |
| — English Clinical Safety (`n=45`) | `97.78%` (44/45) | `97.78%` (44/45) | `0.00 pp` |
| — Nigerian Pidgin Clinical Safety (`n=45`) | `91.11%` (41/45) | `100.00%` (45/45) | `+8.89 pp` |
| — Yorùbá Clinical Safety (`n=45`) | `75.56%` (34/45) | `68.89%` (31/45) | `-6.67 pp` |
| Strict Safety (Clinical + Prefix) | `0.00%` (0/135) | `79.26%` (107/135) | `+79.26 pp` |
| Contraindication Violations | `1.48%` (2/135) | `0.00%` (0/135) | `-1.48 pp` |
| Emergency `112` Escalation (`n=42`) | `66.67%` (28/42) | `64.29%` (27/42) | `-2.38 pp` |

See [docs/AI_MODEL_SELECTION.md](docs/AI_MODEL_SELECTION.md), [models/MODEL_CARD_CHEWIE_1_2.md](models/MODEL_CARD_CHEWIE_1_2.md), and [FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md](experiments/chewie_1_2_fresh_experiment/FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md) for methodology and raw results.

## Emergency Detection & Safety Mechanisms

1. **Deterministic Emergency Preemption:** `DynamicTriageClassifier` runs before any model call and routes `Emergency` inputs directly to `112` national emergency escalation guidance.
2. **Post-Generation Invariant Checks:** `ClinicalInvariantValidator` requires a valid category prefix (`EMERGENCY:`, `PRIORITY:`, or `ROUTINE:`) and rejects affirmative recommendations of contraindicated substances.
3. **Automatic Fallback:** Any backend disablement, HTTP timeout, connection error, or validation failure returns vetted `DeterministicReference` passages.

## Data Sources & Research Resources

- **Conversational & Benchmark Splits (`data/`, `MotherlyPulse_Data/`):** `420` training, `60` validation, and `120` held-out test QA pairs across English, Yorùbá, and Nigerian Pidgin, plus `fixed_15_evaluation_prompts.json`.
- **Ondo State PHC Directory:** `55` Primary Health Centre records in `MotherlyPulse_Data/05_Facilities_Ondo/facilities.json`.
- **Immunization Schedule:** Nigerian NPHCDA schedule in `MotherlyPulse_Data/07_Immunization_Ondo/national_immunization_schedule_nigeria.csv`.
- **Clinical Source Register:** WHO (ANC/PNC/IMPAC), Federal Ministry of Health Nigeria, Ondo State Ministry of Health, UNICEF, and NPHCDA references in `MotherlyPulse_Data/01_Sources/source_register.csv`.
- **Synthetic ANC Risk Dataset:** `30,000` synthetic records in `maternal_risk_prediction/data/` modeled after WHO antenatal guidelines.

See [DATASET_CARD.md](DATASET_CARD.md) and [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

## Installation & Setup

### Requirements
- Python `3.10+`
- `git`

### Local Setup
```bash
git clone https://github.com/giddy7/motherlypulse-public.git
cd motherlypulse-public
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration & Environment Variables

Copy `.env.example` to `.env` (never commit `.env`):
```bash
cp .env.example .env
```
Key variables:
- `TELEGRAM_BOT_TOKEN`: Bot token from `@BotFather` (required only for live Telegram polling).
- `MOTHERLYPULSE_DB_PATH`: SQLite database path (defaults to `/app/data/motherlypulse.db` in `.env.example` or `motherlypulse_user_store.db` locally).
- `AI_MODEL_BACKEND`: `disabled` (default deterministic mode), `remote`, `local`, or `mock`.
- `AI_MODEL_ENDPOINT`: Remote inference endpoint (e.g., `http://chewie-llm:8080/v1/chat/completions`).
- `AI_MODEL_API_FORMAT`: `auto` | `openai` | `custom`.
- `AI_MODEL_TIMEOUT`: Outbound HTTP timeout in seconds (`45.0` default in `.env.example`).

`UserStore` (`motherlypulse_app/user_store.py`) initializes SQLite tables automatically on first startup; no manual migration step is required.

## Running the Application

- **Interactive CLI:**
  ```bash
  python -m motherlypulse_app.cli
  ```
- **HTTP API (`GET /health`, `POST /api/chat`):**
  ```bash
  python -m motherlypulse_app.server
  ```
- **Telegram Bot (requires `TELEGRAM_BOT_TOKEN`):**
  ```bash
  python run_telegram_bot.py
  ```
- **Standalone Maternal Risk Predictor Demo:**
  ```bash
  python maternal_risk_prediction/demo.py
  ```

## Testing

Run the core application unit and integration test suite (`198` tests):
```bash
python -m unittest discover -s motherlypulse_app/tests -p "test_*.py"
```

Run the standalone maternal risk prediction tests (train local `.pkl` model files first, as model binaries are excluded from Git):
```bash
python maternal_risk_prediction/src/train_model.py
python -m unittest maternal_risk_prediction/test_prediction.py
```

## Deployment

- **Deterministic Mode (Default):** Set `AI_MODEL_BACKEND=disabled` and run `run_telegram_bot.py` via `deployment/motherlypulse.service` or Docker using `deployment/setup_server.sh`, `deployment/deploy.sh`, and `deployment/backup_db.sh`.
- **Optional `llama-server` Inference Setup:** `deployment/Export_Chewie_1_2_GGUF.ipynb` exports the fine-tuned adapter merged with `google/gemma-2-2b-it` into `Q4_K_M` GGUF format for `ghcr.io/ggml-org/llama.cpp:server` (`AI_MODEL_BACKEND=remote`, `AI_MODEL_API_FORMAT=openai`).

## Current Limitations & Development Roadmap

- **Live AI Serving Status:** Recorded deployment configuration uses `AI_MODEL_BACKEND=disabled`; end-to-end live production LLM inference for Telegram users is not claimed as active.
- **Yorùbá Emergency Escalation:** In offline neural evaluation without the deterministic bypass, Yorùbá clinical safety was `68.89%` (`11` missed `112` escalations plus `3` regressions), requiring the deterministic `DynamicTriageClassifier` bypass to remain mandatory.
- **Prompt Wrapper Dependency:** `120/120` wrapped `test_*.jsonl` prompts emitted the triage prefix, whereas `0/15` raw un-wrapped `fixed_15` prompts did; any inference endpoint must apply the training prompt wrapper.
- **Pending Clinical & Linguistic Review:** Formal clinical board review and native-speaker Yorùbá and Nigerian Pidgin linguistic validation remain pending.
- **Facility Verification:** Operational hours and 24-hour status of the 55 Ondo State PHC records require periodic field verification.
- **WhatsApp Channel:** `motherlypulse_app/whatsapp_adapter.py` is a structural scaffold and is not wired to a live webhook.

## Contributing

Contributions are welcome via issues and pull requests. Please keep `.env`, local SQLite databases (`*.db`), and model binaries (`*.gguf`, `*.safetensors`, `*.pkl`) out of version control, and run the test suite before submitting changes.

## License

Released under the **MIT License** — see [LICENSE](LICENSE).
