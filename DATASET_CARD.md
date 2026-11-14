# Dataset Card: MotherlyPulse Multilingual Conversational Triage Dataset

**Dataset Name:** MotherlyPulse Maternal & Infant Health Triage Benchmark  
**Languages:** English, Yoruba (`yo`), Nigerian Pidgin (`pcm`)  
**Geographic Domain:** Ondo State, Nigeria (South-West)  
**Total Unique Scenarios:** 200  
**Total Records (Across 3 Languages):** 600  
**Dedicated Fixed Benchmark Prompts:** 15 (5 English, 5 Yoruba, 5 Nigerian Pidgin)  
**Total Evaluated Items:** 615  

---

## 1. Dataset Summary & Purpose
The MotherlyPulse dataset is a curated maternal and child health conversational triage dataset designed to train and benchmark AI systems serving pregnant women, postpartum mothers, and infant caregivers in Nigeria. It addresses high-burden regional health challenges, including maternal hemorrhages, pre-eclampsia, neonatal infections, routine nutrition, lactation, and immunization adherence.

All scenarios are clinically categorized into three distinct operational urgency tiers:
- **`EMERGENCY`:** Immediate danger signs requiring hospital presentation and national emergency escalation ( pe 112 / call 112).
- **`PRIORITY`:** Clinically significant symptoms requiring evaluation at a Primary Health Centre (PHC) within 24 to 48 hours.
- **`ROUTINE`:** Preventative, educational, or wellness guidance (nutrition, antenatal appointments, breastfeeding).

---

## 2. Dataset Split & Provenance
To prevent data contamination and guarantee evaluation integrity, splitting was performed strictly at the **unique-scenario level prior to language expansion**:

| Split | Unique Scenarios | English Pairs | Yoruba Pairs | Nigerian Pidgin Pairs | Total Records | File Locations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Training** | 140 | 140 | 140 | 140 | **420** | `data/train_en.jsonl`, `data/train_yo.jsonl`, `data/train_pcm.jsonl` |
| **Validation** | 20 | 20 | 20 | 20 | **60** | `data/val_en.jsonl`, `data/val_yo.jsonl`, `data/val_pcm.jsonl` |
| **Held-Out Test** | 40 | 40 | 40 | 40 | **120** | `data/test_en.jsonl`, `data/test_yo.jsonl`, `data/test_pcm.jsonl` |
| **Fixed Prompts** | 15 independent prompts (`FIX-01`..`FIX-15`) | 5 | 5 | 5 | **15** | `MotherlyPulse_Data/04_Conversation_Data/fixed_15_evaluation_prompts.json` |
| **Total** | **200 scenarios + 15 fixed** | **205** | **205** | **205** | **615** | — |

### Split & Evaluation Reconciliation (`420/60/120` vs `420/45/135`):
- **Dataset Partition:** `420` train (`140` scenarios $\times 3$ languages), `60` validation (`20` scenarios $\times 3$ languages), and `120` held-out test (`40` scenarios $\times 3$ languages).
- **Evaluation Benchmark Size (`135` rows / `45` per language):** Both `eval_results/chewie_baseline_eval.csv` and `eval_results/chewie_finetuned_eval.csv` evaluate **135** items: the **120** held-out test records plus **15** dedicated fixed benchmark prompts (`FIX-01`..`FIX-15`), yielding **45** evaluated items per language (`40` test + `5` fixed). Earlier references to `420/45/135` conflated the `45` per-language evaluation count and `135` total benchmark count with the underlying `420/60/120` split.

### Contamination Audit:
- **Scenario-Level Overlap:** Verified 0.0% overlap between train, validation, test, and the 15 fixed prompts.
- **Cross-Split Leakage:** Proved that no scenario or phrase variant appears in more than one partition.

---

## 3. Data Fields & Format
Each JSONL record contains:
- `item_id`: Unique identifier (e.g., `PAIR-PRG-001`, `PAIR-INF-042`).
- `user_group`: Target persona (`pregnant_woman` or `mother_infant`).
- `language`: `English`, `Yoruba`, or `Nigerian Pidgin`.
- `urgency_category`: `EMERGENCY`, `PRIORITY`, or `ROUTINE`.
- `user_message`: Colloquially phrased inquiry or symptom report.
- `reference_response`: Medically vetted reference guidance with mandatory prefix (`EMERGENCY:`, `PRIORITY:`, `ROUTINE:`).
- `clinical_evidence`: Citation referencing verified Ondo State health guidelines or WHO maternal care passages.

---

## 4. Linguistic & Clinical Review Status
- **Automated Validation:** 100% of records passed all 31 automated syntactic, schema, and lexical invariant integrity checks.
- **Human Clinical Validation:** **Pending**. While medically derived, full human board review by certified Nigerian clinicians (obstetricians, pediatricians, midwives) is scheduled for 12–13 November 2026.
- **Native Speaker Validation:** **In Progress**. Automated tests confirm vocabulary preservation, but dialectal fluency and tone in Yoruba and Nigerian Pidgin await final sign-off from native raters using the exported blinded rating sheet (`eval_results/blinded_human_rating_sheet.csv`).

