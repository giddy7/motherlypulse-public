# MotherlyPulse Data and Evaluation Resources

This directory and its sibling folders under `MotherlyPulse_Data/` contain the curated clinical reference passages, deterministic emergency triage rules, multilingual conversational/evaluation datasets, Ondo State healthcare facility and immunization directories, and evaluation artifacts for **MotherlyPulse**—a maternal and infant (0–1 year) health support system for Nigeria.

---

## 1. Purpose and Scope

`MotherlyPulse_Data/` provides the structured knowledge and evaluation substrate for:
1. **Deterministic Emergency Triage & Escalation:** Rule definitions (`EMERGENCY`, `PRIORITY`, `ROUTINE`) and national `112` emergency routing guidance.
2. **Grounded Clinical Guidance:** Curated antenatal, postnatal, and infant-care passages used by `PassageRetriever` and as deterministic fallbacks.
3. **Multilingual Training & Evaluation:** Aligned English, Èdè Yorùbá, and Nigerian Pidgin conversational pairs and safety/triage benchmarks (with canonical `420/60/120` train/val/test JSONL splits stored in root `data/`).
4. **Local Care Navigation:** Ondo State Primary Health Centre (PHC) and NPHCDA routine immunization schedules.

---

## 2. Supported Languages, Formats, and Triage Categories

- **Languages:** English (`en`), Èdè Yorùbá (`yo`), and Nigerian Pidgin (`pcm`).
- **Formats:** CSV, JSON, JSONL, Parquet, and Markdown.
- **Triage Categories:**
  - **`EMERGENCY`:** Life-threatening obstetric or neonatal danger signs requiring immediate hospital care and national **`112`** emergency escalation (handled deterministically before any generative model).
  - **`PRIORITY`:** Symptoms or questions requiring prompt clinical assessment within 24 hours.
  - **`ROUTINE`:** General antenatal, postnatal, nutrition, hygiene, and immunization guidance.

---

## 3. Directory Structure (Verified Contents)

```text
MotherlyPulse_Data/
├── 01_Sources/
│   ├── source_register.csv                  # 10 authoritative clinical/registry source entries
│   └── source_summaries.txt                 # Summaries of WHO, FMoH, Ondo MOH, UNICEF, NPHCDA sources
├── 02_Passages/
│   ├── passages.csv / passages.json         # 35 curated clinical guidance passages
│   └── create_passages.py                   # Passage generation script
├── 03_Emergency_Rules/
│   ├── emergency_rules.csv / .json          # 24 emergency/triage rules
│   ├── rule_traceability.csv                # 24 guideline-to-rule traceability records
│   ├── emergency_contacts.csv               # 1 confirmed national emergency routing record (112)
│   ├── emergency_response_notes.md          # Emergency routing protocol notes
│   └── create_emergency_rules.py            # Rule compilation script
├── 04_Conversation_Data/
│   ├── english_pairs.{csv,jsonl}            # 200 English QA pairs
│   ├── yoruba_pairs.{csv,jsonl}             # 200 Yorùbá QA pairs
│   ├── pidgin_pairs.{csv,jsonl}             # 200 Nigerian Pidgin QA pairs
│   ├── multilingual_pairs.{csv,jsonl}       # 200 aligned EN/YO/PCM records
│   ├── adaptation_template.csv              # 200-row multilingual adaptation template
│   ├── emergency_scenarios_en.csv           # 6 emergency scenario cases
│   ├── safety_tests_en.csv                  # 11 boundary & safety test cases
│   ├── fixed_15_evaluation_prompts.json     # 15 cross-lingual benchmark prompts (5 EN, 5 YO, 5 PCM)
│   └── intent_definitions.md                # Intent and clinical boundary definitions
├── 05_Facilities_Ondo/
│   ├── facilities.csv / facilities.json     # 55 Ondo State Primary Health Centre records
│   ├── facility_verification_report.md      # Facility registry audit notes
│   └── create_facilities.py                 # Facility compilation script
├── 06_Reports/
│   ├── README.md                            # This documentation & index
│   ├── data_quality_report.md               # Dataset integrity and field checks
│   ├── gaps_and_limits.md                   # Known dataset gaps and operational limits
│   ├── clinical_review_checklist.md         # Checklist for clinical reviewers
│   ├── MULTILINGUAL_HUMAN_REVIEW_CHECKLIST.md # Checklist for native-speaker review
│   ├── source_and_verification_register.md  # Source verification register
│   ├── statewide_coverage_report.md         # Ondo State geographic coverage summary
│   ├── implementation_compatibility_report.md # Application schema compatibility notes
│   ├── RETRIEVAL_EVALUATION_REPORT.md       # Passage retrieval benchmark output
│   ├── mamabench_evaluation_report.md       # MamaBench evaluation output
│   ├── COMPARATIVE_EVALUATION_RESULTS.md    # Comparative evaluation summary
│   ├── *.csv                                # Raw comparative & error-analysis CSVs
│   ├── validate_data.py / validate_multilingual_data.py # Dataset validation scripts
│   └── evaluation_evidence/                 # Preserved historical benchmark, safety & QA reports
├── 07_Immunization_Ondo/
│   ├── immunization_centers.csv / .json     # 43 Ondo State immunization center records
│   ├── national_immunization_schedule_nigeria.csv # 21 NPHCDA schedule entries
│   └── immunization_verification_report.md  # Immunization dataset notes
└── mamabench_evaluation/
    ├── mamabench_cases.{csv,parquet}        # 434 MamaBench evaluation vignettes
    ├── helpmum_mamabench_classified.csv     # 434 classified vignettes
    └── helpmum_human_review_cases.csv       # 1 human-review sample record
```

---

## 4. Data Provenance and Sources

Clinical content is derived from public-health guidelines listed in `01_Sources/source_register.csv`:
- **World Health Organization (WHO):** *Antenatal Care (2016)*, *Postnatal Care (2022)*, and *Managing Complications in Pregnancy and Childbirth (IMPAC, 2017)*.
- **Federal Ministry of Health and Social Welfare (Nigeria):** *National Antenatal Care Guidelines (2020)*, *National Life Saving Skills (LSS) Protocol (2019)*, and *Nigeria Health Facility Registry (NHFR)*.
- **Ondo State Authorities:** *Ondo State Ministry of Health / OSPHCDA Directory*.
- **UNICEF & NPHCDA:** *Facts for Life (2021)* and Nigeria's routine infant immunization schedule.

---

## 5. Limitations, Privacy, and Responsible Use

- **No Patient PII:** All conversational, passage, and benchmark files contain curated reference or synthetic examples—no real patient records or personal health information are included.
- **Pending Clinical & Linguistic Review:** Formal review by certified Nigerian clinicians/midwives and native-speaker Yorùbá/Nigerian Pidgin reviewers remains pending.
- **Facility Operational Status:** The 55 Ondo State PHC records and 43 immunization center records require periodic on-ground verification for current opening hours and 24-hour staffing.
- **Clinical Boundary:** These resources support health education, triage routing, and clinic discovery; they do not provide medical diagnosis or prescriptions.

---

## 6. Inspecting and Validating the Data

Run the dataset validation scripts from the repository root:
```bash
python MotherlyPulse_Data/06_Reports/validate_data.py
python MotherlyPulse_Data/06_Reports/validate_multilingual_data.py
```

### Documentation Index
- **Core Data & Coverage Docs (Category A):** [data_quality_report.md](data_quality_report.md), [gaps_and_limits.md](gaps_and_limits.md), [statewide_coverage_report.md](statewide_coverage_report.md), [source_and_verification_register.md](source_and_verification_register.md), [clinical_review_checklist.md](clinical_review_checklist.md), [MULTILINGUAL_HUMAN_REVIEW_CHECKLIST.md](MULTILINGUAL_HUMAN_REVIEW_CHECKLIST.md).
- **Research & Evaluation Evidence (Category B):** [evaluation_evidence/](evaluation_evidence/), [RETRIEVAL_EVALUATION_REPORT.md](RETRIEVAL_EVALUATION_REPORT.md), [mamabench_evaluation_report.md](mamabench_evaluation_report.md), [COMPARATIVE_EVALUATION_RESULTS.md](COMPARATIVE_EVALUATION_RESULTS.md), and root [DATASET_CARD.md](../../DATASET_CARD.md).
