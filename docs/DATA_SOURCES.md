# Data Sources & Clinical References

## 1. Conversational & Triage Datasets (`data/` & `MotherlyPulse_Data/`)

- **`data/` (Canonical Split):**
  - Training (`420` rows): `train_en.jsonl` (140), `train_pcm.jsonl` (140), `train_yo.jsonl` (140)
  - Validation (`60` rows): `val_en.jsonl` (20), `val_pcm.jsonl` (20), `val_yo.jsonl` (20)
  - Held-Out Test (`120` rows): `test_en.jsonl` (40), `test_pcm.jsonl` (40), `test_yo.jsonl` (40)
- **`MotherlyPulse_Data/04_Conversation_Data/fixed_15_evaluation_prompts.json`:** `15` fixed cross-lingual benchmark prompts (`5` EN, `5` YO, `5` PCM) with mandatory actions and contraindications.
- **`MotherlyPulse_Data/02_Passages/`:** Curated clinical educational passages used by `PassageRetriever` and as deterministic fallback references.
- **`MotherlyPulse_Data/03_Emergency_Rules/`:** Danger-sign rule definitions across maternal and neonatal categories.

*Privacy Note:* All conversational JSONL/JSON records are curated, synthetic/reference clinical QA pairs—no real patient conversations or personally identifiable health records are included.

## 2. Ondo State Healthcare Facility & Immunization Data

- **`MotherlyPulse_Data/05_Facilities_Ondo/facilities.json` & `facilities.csv`:** Directory of `52` verified Primary Health Centres (PHCs) across Ondo State LGAs (Akure, Ondo, Owo, etc.) with coordinates and addresses for `LocationService`.
- **`MotherlyPulse_Data/07_Immunization_Ondo/`:** Nigerian National Primary Health Care Development Agency (NPHCDA) routine infant immunization schedule (BCG, OPV, Pentavalent, Measles, Yellow Fever) powering `ReminderEngine`.

## 3. Maternal Risk Prediction Synthetic Dataset (`maternal_risk_prediction/data/`)

- `30,000` synthetic ANC records (`maternal_low_burden.csv`, `maternal_moderate_burden.csv`, `maternal_high_burden.csv`, `10,000` each) modeled after WHO antenatal care guidelines (`DATASET_README.md`). No real patient records are used.

