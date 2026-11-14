# MotherlyPulse: Multilingual Maternal & Infant Health Assistant

**MotherlyPulse** is an AI-assisted maternal and infant health support system designed for Ondo State and Southwest Nigeria. It combines deterministic emergency triage, a fine-tuned multilingual LLM (`Chewie 1.2`, `google/gemma-2-2b-it` + QLoRA), strict clinical safety invariant validation, Ondo State Primary Health Centre (PHC) discovery, and NPHCDA routine immunization reminders across **English**, **Èdè Yorùbá**, and **Nigerian Pidgin**.

---

## 1. Problem Statement & Motivation

Maternal and neonatal mortality remain critical public health challenges across Nigeria, where delayed recognition of obstetric/neonatal danger signs, language barriers, misinformation (including harmful herbal concoctions such as *agbo* or unsafe NSAIDs like aspirin/ibuprofen during pregnancy), and difficulty locating nearby Primary Health Centres delay life-saving care. Standard general-purpose LLMs are unsuitable for unguarded medical deployment due to hallucination risks, missing emergency escalation (`112`), and inconsistent formatting.

## 2. Project Objectives

1. **Zero-Trust Emergency Preemption:** Detect life-critical maternal and neonatal emergencies deterministically (`0.05 ms`) and escalate immediately to Nigeria's national emergency line **`112`**, bypassing generative AI.
2. **Safe Multilingual Guidance:** Provide culturally grounded `PRIORITY` and `ROUTINE` guidance in English, Yorùbá, and Nigerian Pidgin using a lightweight, fine-tuned `2.62B` model guarded by `ClinicalInvariantValidator` and approved deterministic fallbacks.
3. **Practical Care Navigation:** Deliver Ondo State PHC facility lookup (GPS Haversine distance & LGA/town search across 55 PHC records) and automated antenatal/NPHCDA infant vaccination reminders via Telegram.
4. **Reproducible Deployment Architecture:** Support lightweight deterministic-only operation (`AI_MODEL_BACKEND=disabled`) as well as optional CPU-only VPS `llama.cpp` `llama-server` (`Q4_K_M` GGUF) or remote GPU inference (`AI_MODEL_BACKEND=remote`).

## 3. Intended Users

- **Pregnant women** seeking antenatal guidance, danger-sign triage, and clinic appointment reminders.
- **Mothers and caregivers of infants** tracking postnatal health and NPHCDA routine immunizations.
- **Academic supervisors, clinical reviewers, and developers** evaluating safety-scaffolded healthcare AI.

## 4. Key Features & Capabilities

- **3-Tier Clinical Triage (`EMERGENCY`, `PRIORITY`, `ROUTINE`):** Deterministic keyword + fuzzy regex classification with immediate `112` escalation for emergencies.
- **Multilingual Support:** English, Èdè Yorùbá, and Nigerian Pidgin across registration, triage, reminders, and guidance.
- **Clinical Invariant Guardrails:** Rejects missing triage prefixes, contraindicated substances (*aspirin, ibuprofen, agbo, ogogoro, kaun, tetracycline*, etc.), and missing emergency escalations, automatically triggering verified fallbacks.
- **Telegram Bot (`@MotherlyPulse_bot`):** Multi-turn onboarding (`/start`), language switching (`/language`), profile (`/profile`), PHC lookup (`/clinic` + GPS location), reminders (`/remind`, `/remind_apt`, `/remind_med`, `/remind_vax`), A/B model demo (`/compare <question>`), and GDPR-style right-to-erasure (`/delete`).
- **Ondo State PHC Directory:** 55 Primary Health Centre records with coordinates and LGA metadata (`MotherlyPulse_Data/05_Facilities_Ondo/facilities.json`).
- **Standalone Maternal Risk Prediction Module (`maternal_risk_prediction/`):** Isolated `scikit-learn` Random Forest risk-level and complication classifiers trained on 30,000 synthetic ANC records.
- **Zero-Dependency HTTP API & CLI:** Built-in Python stdlib HTTP API (`GET /health`, `POST /api/chat`) and interactive CLI (`motherlypulse_app/cli.py`).

## 5. System Architecture

```text
Incoming Message (Telegram / HTTP API / CLI)
   │
   ▼
┌──────────────────────────────────────────┐
│ DynamicTriageClassifier (0.05 ms)        │
└──────────────────┬───────────────────────┘
                   │
     Is Emergency? ├── YES ──► Immediate 112 National Escalation (Deterministic Only)
                   │
                   ▼ NO (Priority / Routine)
┌──────────────────────────────────────────┐
│ AIModelConnector (Chewie 1.2)            │
│ - remote: VPS llama-server (Q4_K_M GGUF) │
│ - remote: Cloud GPU (/generate, /compare)│
│ - local:  Transformers + PEFT Adapter    │
│ - disabled / timeout ──► Fallback        │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│ ClinicalInvariantValidator               │
│ - Prefix (EMERGENCY:/PRIORITY:/ROUTINE:) │
│ - Contraindication & Negation Gate       │
└──────────────────┬───────────────────────┘
                   │
       Passed? ────┼── YES ──► Validated AI Response
                   └── NO  ──► Approved Deterministic Fallback
```

For deeper architectural details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/SAFETY_AND_VALIDATION.md](docs/SAFETY_AND_VALIDATION.md).

## 6. Technology Stack

- **Core Runtime & API:** Python 3.11+ standard library (`sqlite3`, `urllib.request`, `http.server`, `json`, `re`, `logging`) — zero heavy ML dependencies inside the bot container (`~17.8 MiB` RAM).
- **Neural Model & Fine-Tuning:** `google/gemma-2-2b-it` (4-bit NF4 QLoRA via `transformers`, `peft`, `bitsandbytes`, `accelerate`, `datasets`) exported to `Q4_K_M` GGUF and served via `llama.cpp` (`ghcr.io/ggml-org/llama.cpp:server`).
- **Risk Prediction & Data Tooling:** `numpy`, `scipy`, `scikit-learn`, `pandas`.
- **Database:** SQLite (`UserStore` with WAL/integrity checks and `/delete` erasure).
- **Messaging & Deployment:** Telegram Bot API (long polling), Docker, systemd/shell scripts (`deployment/`).

## 7. Project Directory Structure

```text
motherlypulse/
├── motherlypulse_app/          # Core application: bot, triage, validator, API, CLI, tests
│   ├── ai_connector.py         # ClinicalInvariantValidator & AIModelConnector
│   ├── assistant.py            # Response orchestration & fallback handling
│   ├── classifier.py           # DynamicTriageClassifier (EN / YO / PCM)
│   ├── telegram_bot.py         # TelegramBotHandler (/start, /clinic, /remind, /compare, /delete)
│   ├── server.py               # Stdlib HTTP server (GET /health, POST /api/chat)
│   ├── cli.py                  # Interactive CLI runner
│   ├── location_service.py     # Ondo State 55-PHC distance & LGA lookup
│   ├── reminders.py            # Antenatal, medication & NPHCDA immunization scheduler
│   ├── retriever.py            # Clinical passage retriever
│   ├── user_store.py           # SQLite persistence & right-to-erasure
│   └── tests/                  # Automated unittest suite (198 tests)
├── maternal_risk_prediction/   # Isolated scikit-learn ANC risk & complication module
├── data/                       # Canonical train (420), val (60), test (120) JSONL splits
├── MotherlyPulse_Data/         # Curated passages, emergency rules, 55 Ondo PHCs, fixed_15 prompts
├── deployment/                 # VPS deploy scripts, Colab server & GGUF export notebooks
├── eval_results/               # Offline evaluation outputs & blinded rating sheets (key excluded)
├── experiments/                # Fresh verified Colab experiment & historical archive
├── docs/                       # Architecture, technical, model selection, safety & data docs
├── models/                     # Chewie 1.2 model card & metadata
├── DATASET_CARD.md             # Canonical dataset card
├── EXPERIMENTAL_PROVENANCE_RECONCILIATION.md # Reconciled benchmark & artifact audit
├── .env.example                # Safe environment variable template
├── requirements.txt            # Python dependencies for ML/risk/eval tooling
├── run_telegram_bot.py         # Telegram bot entry point
└── LICENSE                     # MIT License
```

## 8. Major Application Modules

- **`motherlypulse_app/classifier.py`:** Deterministic multilingual danger-sign classifier (`Emergency`, `Priority`, `Routine`).
- **`motherlypulse_app/ai_connector.py`:** `ClinicalInvariantValidator` + `AIModelConnector` supporting `disabled`, `mock`, `local`, and `remote` (OpenAI `/v1/chat/completions` for `llama-server` and custom `/generate` + `/compare`).
- **`motherlypulse_app/telegram_bot.py`:** Stateful Telegram bot supporting registration, reminders, PHC lookup, `/compare`, and `/delete`.
- **`motherlypulse_app/server.py` & `cli.py`:** Local REST API and terminal interfaces.
- **`maternal_risk_prediction/src/predictor.py`:** Standalone `MaternalRiskPredictor` for structured ANC vitals/labs.

See [docs/TECHNICAL_OVERVIEW.md](docs/TECHNICAL_OVERVIEW.md) for full module details.

## 9. AI Architecture, Offline Evaluation & Production Status

### Component & Production Serving Separation
- **Operational Telegram Application (`motherlypulse_app/telegram_bot.py`):** Implemented and operational for onboarding (`/start`), multilingual menus (`en`/`yo`/`pcm`), profile management, 55-PHC lookup (`/clinic`), NPHCDA/ANC reminders, and `/delete` erasure.
- **Deterministic Emergency Classification & Safety System (`classifier.py`, `ai_connector.py`):** Runs locally on every message (`DynamicTriageClassifier` + `ClinicalInvariantValidator` + `DeterministicReference` fallback), preempting generative AI on `EMERGENCY` inputs with immediate `112` escalation.
- **Trained Chewie 1.2 QLoRA Research Model:** **`google/gemma-2-2b-it`** (pinned revision `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`) fine-tuned with **4-bit NF4 QLoRA** (`r=16`, `lora_alpha=32`, `lora_dropout=0.05`, attention projections only, `6,389,760` trainable params / `0.2438%`) for `1.514` epochs (`80` steps, `148.34s` on an `NVIDIA A100-SXM4-40GB`, `11.098 GB` peak VRAM).
- **Current Production Model-Serving Status:** The repository's recorded live VPS deployment configuration uses **`AI_MODEL_BACKEND=disabled`** (deterministic-only mode). While `AI_MODEL_BACKEND=remote` (for `llama.cpp` `llama-server` OpenAI-compatible `/v1/chat/completions` and Colab `/generate` + `/compare`) is implemented and verified in automated unit/integration tests, **this repository does not claim live end-to-end production serving of Chewie 1.2 to live Telegram users**.

### Verified Offline Held-Out Evaluation (`n = 135`: 120 `test_*.jsonl` + 15 `fixed_15` prompts)

Reconciled directly from `experiments/chewie_1_2_fresh_experiment/01_baseline/chewie_1_2_fresh_baseline_eval.csv` and `03_post_eval/chewie_1_2_fresh_finetuned_eval.csv`:

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

See [docs/AI_MODEL_SELECTION.md](docs/AI_MODEL_SELECTION.md), [models/MODEL_CARD_CHEWIE_1_2.md](models/MODEL_CARD_CHEWIE_1_2.md), [EXPERIMENTAL_PROVENANCE_RECONCILIATION.md](EXPERIMENTAL_PROVENANCE_RECONCILIATION.md), and [FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md](experiments/chewie_1_2_fresh_experiment/FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md) for full breakdowns.

## 10. Emergency Classification & Safety Mechanisms

1. **Deterministic Preemption:** `DynamicTriageClassifier` runs before any LLM call and routes emergencies directly to `112` escalation.
2. **Post-Generation Invariant Validation:** `ClinicalInvariantValidator` enforces `EMERGENCY:`/`PRIORITY:`/`ROUTINE:` prefixes and blocks affirmative contraindication recommendations.
3. **Automatic Fallback:** Any timeout, connection failure, or validator rejection triggers `DeterministicReference` passages.

## 11. Multilingual Functionality

Supports **English (`en`)**, **Èdè Yorùbá (`yo`)**, and **Nigerian Pidgin (`pcm`)** in `interface_strings.py`, `classifier.py`, `telegram_bot.py`, and the `420/60/120` train/val/test JSONL splits.

## 12. Data Sources & Clinical References

- Curated maternal/infant clinical QA splits (`data/{train,val,test}_{en,pcm,yo}.jsonl`) and `fixed_15_evaluation_prompts.json`.
- `55` Ondo State Primary Health Centre records (`MotherlyPulse_Data/05_Facilities_Ondo/facilities.json`).
- NPHCDA routine immunization schedules (`MotherlyPulse_Data/07_Immunization_Ondo/`).
- `30,000` synthetic ANC records in `maternal_risk_prediction/data/` modeled after WHO guidelines.

See [DATASET_CARD.md](DATASET_CARD.md) and [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

## 13. Installation & Local Setup

### Requirements
- Python `3.10+` (tested on Python `3.10` and `3.11`)
- `git`

### Step-by-Step Setup
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

## 14. Environment Variable Configuration

Copy `.env.example` to `.env` (never commit `.env`):
```bash
cp .env.example .env
```
Key variables:
- `TELEGRAM_BOT_TOKEN`: Bot token from `@BotFather` (required only for live Telegram polling).
- `MOTHERLYPULSE_DB_PATH`: SQLite path (defaults to local `motherlypulse_user_store.db`).
- `AI_MODEL_BACKEND`: `disabled` (deterministic-only), `remote` (`llama-server` or Colab FastAPI), `local`, or `mock`.
- `AI_MODEL_ENDPOINT`: e.g. `http://chewie-llm:8080/v1/chat/completions`.
- `AI_MODEL_API_FORMAT`: `auto` | `openai` | `custom`.
- `AI_MODEL_TIMEOUT`: HTTP timeout in seconds (e.g. `45.0` for CPU `llama-server`).

## 15. Database Setup

`UserStore` (`motherlypulse_app/user_store.py`) initializes SQLite tables automatically on first startup (`users`, `reminders`, `registration_state`) at `MOTHERLYPULSE_DB_PATH`. No manual migration command is required.

## 16. Running Backend, Frontend (CLI) & Telegram Bot

- **Interactive CLI:**
  ```bash
  python -m motherlypulse_app.cli
  ```
- **Local HTTP API Server (`GET /health`, `POST /api/chat`):**
  ```bash
  python -m motherlypulse_app.server
  ```
- **Telegram Bot (requires `TELEGRAM_BOT_TOKEN` in `.env` or environment):**
  ```bash
  python run_telegram_bot.py
  ```
- **Standalone Maternal Risk Predictor Demo:**
  ```bash
  python maternal_risk_prediction/demo.py
  ```

## 17. Automated Tests

Run the full unit and integration test suite (`198` tests covering triage, clinical safety invariants, remote OpenAI/custom backends, `/compare`, storage, reminders, and Telegram flows):
```bash
python -m unittest discover -s motherlypulse_app/tests -p "test_*.py"
```
Run the isolated maternal risk prediction tests (train the local `.pkl` models first, as model binaries are excluded from Git):
```bash
python maternal_risk_prediction/src/train_model.py
python -m unittest maternal_risk_prediction/test_prediction.py
```

## 18. Optional AI Deployment Architecture (`llama-server`)

> **Status Note:** The recorded live VPS configuration uses `AI_MODEL_BACKEND=disabled` (deterministic-only mode). The optional `llama-server` setup below is provided for reproducible self-hosted testing and deployment:

1. Export the quantized `Q4_K_M` GGUF once using [deployment/Export_Chewie_1_2_GGUF.ipynb](deployment/Export_Chewie_1_2_GGUF.ipynb) (`chewie-1.2-q4_k_m.gguf`, `~1.59 GiB`).
2. Run `ghcr.io/ggml-org/llama.cpp:server` on an internal Docker network (`ai_internal_net`, `2.5 GiB` RAM limit, `--ctx-size 2048 --threads 3 --n-gpu-layers 0`).
3. Run `motherlypulse-bot` with `AI_MODEL_BACKEND=remote`, `AI_MODEL_ENDPOINT=http://chewie-llm:8080/v1/chat/completions`, `AI_MODEL_API_FORMAT=openai`, and `AI_MODEL_TIMEOUT=45.0`.
4. See `deployment/` (`setup_server.sh`, `deploy.sh`, `backup_db.sh`, `motherlypulse.service`) for server scripts.

## 19. Known Limitations & Pending Validation

- **Live AI Serving Unverified in Production:** Recorded VPS deployment evidence uses `AI_MODEL_BACKEND=disabled`; end-to-end live production serving of Chewie 1.2 to Telegram users has not been independently verified here.
- **Yoruba Emergency `112` Escalation:** In pure neural evaluation without the deterministic bypass, Yoruba clinical safety was `68.89%` (`11` missed `112` escalations + `3` regressions), underscoring that `DynamicTriageClassifier` must remain mandatory.
- **Prompt Wrapper Dependency:** `120/120` wrapped `test_*.jsonl` prompts emitted the triage prefix, while `0/15` raw un-wrapped `fixed_15` prompts did; production inference must always apply the system/wrapper prompt.
- **Clinical Board & Native-Speaker Validation Pending:** Automated software tests (`198/198` + `8/8`) do not replace formal clinical board validation or native-speaker Yorùbá and Nigerian Pidgin linguistic review, both of which remain pending.
- **WhatsApp Channel:** `motherlypulse_app/whatsapp_adapter.py` is a structural scaffold, not a live production webhook.
- **PHC Field Verification:** 24-hour operational status of the 55 Ondo State PHC records requires periodic on-ground field verification.

## 20. Security & Privacy Considerations

- **No Secrets in Source Control:** `.env`, `*.db`, `*.pem`, `*.key`, `*.safetensors`, and `*.gguf` are excluded via `.gitignore`.
- **No Patient PII:** Datasets in `data/`, `MotherlyPulse_Data/`, and `maternal_risk_prediction/data/` contain curated reference/synthetic data only.
- **Blinded Rating Key Excluded:** `eval_results/blinded_rating_key.csv` is excluded from the public repository so blinded rating sheets remain unspoiled.
- **Right-to-Erasure:** Users can erase their stored profile and reminders at any time via `/delete`.

## 21. Supervisor Documentation Map & References

- **Overview & Architecture:** [docs/TECHNICAL_OVERVIEW.md](docs/TECHNICAL_OVERVIEW.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Model & Dataset Cards:** [models/MODEL_CARD_CHEWIE_1_2.md](models/MODEL_CARD_CHEWIE_1_2.md), [DATASET_CARD.md](DATASET_CARD.md), [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)
- **Training & Reproducibility:** [EXPERIMENT_PROTOCOL.md](experiments/chewie_1_2_fresh_experiment/EXPERIMENT_PROTOCOL.md), [FINE_TUNING_METHODOLOGY_AND_ANTI_OVERFITTING_REPORT.md](experiments/chewie_1_2_fresh_experiment/FINE_TUNING_METHODOLOGY_AND_ANTI_OVERFITTING_REPORT.md), [CHECKSUMS.json](experiments/chewie_1_2_fresh_experiment/CHECKSUMS.json)
- **Evaluation & Safety:** [BASELINE_MODEL_EVALUATION_REPORT.md](experiments/chewie_1_2_fresh_experiment/BASELINE_MODEL_EVALUATION_REPORT.md), [FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md](experiments/chewie_1_2_fresh_experiment/FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md), [docs/SAFETY_AND_VALIDATION.md](docs/SAFETY_AND_VALIDATION.md)
- **Clinical Source Register:** [MotherlyPulse_Data/01_Sources/source_register.csv](MotherlyPulse_Data/01_Sources/source_register.csv) (WHO ANC/PNC/IMPAC, FMoH Nigeria, Ondo State MOH, UNICEF, NPHCDA)

## 22. Contribution & License

Contributions via pull requests and issues are welcome. Released under the **MIT License** — see [LICENSE](LICENSE).
