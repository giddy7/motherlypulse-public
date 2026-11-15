# Models & Model Metadata

This directory holds model documentation and evaluation metadata for MotherlyPulse. Large model binaries (`*.joblib`, `*.pkl`, `*.safetensors`, `*.gguf`) are excluded from Git via `.gitignore`.

---

## 1. Tracked Files in `models/`

| File | Description |
| :--- | :--- |
| `MODEL_CARD_CHEWIE_1_2.md` | Model card for the experimental `Chewie 1.2` QLoRA fine-tune (`google/gemma-2-2b-it`). |
| `model_metadata.json` | Evaluation metadata (`30,000` synthetic ANC records; `6,000` held-out test split) for the standalone `maternal_risk_prediction/` classifiers. |
| `README.md` | This overview. |

> **Artifact Availability Note:** The serialized Random Forest bundles (`risk_level_model.joblib`, `complication_model.joblib`) are **not** stored in `models/`. They are generated locally inside `maternal_risk_prediction/models/` when you run `python maternal_risk_prediction/src/train_model.py`.

---

## 2. Chewie 1.2 (Experimental Multilingual LLM)

- **Base Model & Method:** `google/gemma-2-2b-it` (revision `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`) fine-tuned with 4-bit NF4 QLoRA (`r=16`, `lora_alpha=32`, `6,389,760` trainable parameters) on `420` multilingual QA pairs (`140` EN, `140` PCM, `140` YO).
- **Offline Evaluation (`n=135`):** `88.89%` triage prefix compliance, `88.89%` clinical safety (excl. prefix), `79.26%` strict safety, `0.00%` contraindication violations. See [MODEL_CARD_CHEWIE_1_2.md](MODEL_CARD_CHEWIE_1_2.md) and [../experiments/chewie_1_2_fresh_experiment/FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md](../experiments/chewie_1_2_fresh_experiment/FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md).
- **Production Integration Status:** Deployed in the VPS Docker Compose stack as an isolated `chewie-llm` (`ghcr.io/ggml-org/llama.cpp:server`) container serving `chewie-1.2-q4_k_m.gguf` over an internal Docker bridge (`http://chewie-llm:8080/v1/chat/completions`), with end-to-end inference and `ClinicalInvariantValidator` verified (`8.91s` latency). Note that `.env.example` keeps `AI_MODEL_BACKEND=disabled` as the safe local/template default; see [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md).

---

## 3. Standalone Maternal Risk Classifiers (`maternal_risk_prediction/`)

- **Integration Status:** **Standalone module only — NOT integrated into the Telegram bot (`motherlypulse_app/telegram_bot.py`).**
- **Training & Evaluation Data:** Trained and evaluated exclusively on **`30,000` synthetic ANC records** (`24,000` train / `6,000` held-out synthetic test split) modeled after WHO guidelines. **These metrics have not been validated on real clinical patient data.**
- **Recorded Metrics in `model_metadata.json` (`n=6,000` synthetic test split):**
  - **`risk_level` (`low`, `moderate`, `high`):** `93.95%` accuracy (`0.9395`), `92.67%` balanced accuracy (`0.9267`).
  - **`primary_complication` (`6` classes):** `78.48%` accuracy (`0.7848`), `77.64%` balanced accuracy (`0.7764`) — `preeclampsia` F1 `0.95`, `severe_anemia` F1 `0.89`, `gestational_diabetes` F1 `0.76`, `none` F1 `0.85`, `eclampsia` F1 `0.59`, `hemorrhage` F1 `0.28`.

### Generating and Using the Local Risk Models

```bash
python maternal_risk_prediction/src/train_model.py
python maternal_risk_prediction/demo.py
```

```python
from maternal_risk_prediction.src.predictor import MaternalRiskPredictor

predictor = MaternalRiskPredictor()  # loads from maternal_risk_prediction/models/
```
