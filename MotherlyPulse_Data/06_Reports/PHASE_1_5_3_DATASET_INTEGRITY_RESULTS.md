# PHASE 1.5.3 DATASET INTEGRITY RESULTS
**MotherlyPulse: Cryptographic Hash Verification & Dataset Baseline Audit**  
*Audit Date:* November 5, 2026  
*Auditor:* Independent Safety & Assurance Auditor (Antigravity Engineering Suite)

---

## 1. Executive Summary

This document establishes the cryptographic and structural integrity of all dataset assets within the MotherlyPulse repository following the completion of the Phase 1.5.3 independent adversarial audit.

**Integrity Verdict: 100% VERIFIED UNCHANGED**  
- All 12 primary knowledge bases, conversational datasets, emergency rule files, facility directories, and machine learning models match their documented baseline SHA-256 cryptographic hashes.
- Zero records were modified, overwritten, or corrupted by the execution of unit tests, adversarial scripts, or benchmark runners.
- The two automated validation suites (`validate_data.py` and `validate_multilingual_data.py`) continue to pass 31/31 checks with zero errors.

---

## 2. Master Cryptographic Hash Baseline Comparison

| Dataset / Asset File Path | Size (Bytes) | Baseline SHA-256 Hash | Phase 1.5.3 Audit SHA-256 Hash | Integrity Status |
| :--- | :--- | :--- | :--- | :--- |
| `MotherlyPulse_Data/04_Conversation_Data/english_pairs.csv` | 109,065 | `e28600f0d070c286ed1dd5a0437ef2f38e2372857eda58c9244ef9bb4dd1f56d` | `e28600f0d070c286ed1dd5a0437ef2f38e2372857eda58c9244ef9bb4dd1f56d` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/04_Conversation_Data/yoruba_pairs.csv` | 139,445 | `5c56e56ca6a87c31a10bb907fd1febfba958f935810fcc9bc7c4a2ddec83d3f3` | `5c56e56ca6a87c31a10bb907fd1febfba958f935810fcc9bc7c4a2ddec83d3f3` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/04_Conversation_Data/pidgin_pairs.csv` | 110,175 | `26003b85cfe11c1afa2a47541382bb01e914a6ed23d640769ab483e16c6ba2b0` | `26003b85cfe11c1afa2a47541382bb01e914a6ed23d640769ab483e16c6ba2b0` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/04_Conversation_Data/multilingual_pairs.csv`| 275,342 | `38ea5508de565483307674319dbb37aa5aa88ebc7498aea85e7a692857c60735` | `38ea5508de565483307674319dbb37aa5aa88ebc7498aea85e7a692857c60735` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/04_Conversation_Data/adaptation_template.csv`| 251,819 | `7b1d2c7cd63d0fb33703910d8d38326e2d2554669fbb125cb007c209b3a8fde3` | `7b1d2c7cd63d0fb33703910d8d38326e2d2554669fbb125cb007c209b3a8fde3` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/02_Passages/passages.csv` | 28,412 | `bc614ac3b4da99d7ff1050c202e24c4cde32ef98a10def381845820e89152df1` | `bc614ac3b4da99d7ff1050c202e24c4cde32ef98a10def381845820e89152df1` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/03_Emergency_Rules/emergency_rules.csv` | 17,179 | `00e50d5a6c1b2e4e5ee8869b4f3d5b7350957b5867fe880155cd5605a44a31f1` | `00e50d5a6c1b2e4e5ee8869b4f3d5b7350957b5867fe880155cd5605a44a31f1` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/05_Facilities_Ondo/facilities.csv` | 37,287 | `d34c871f577d1c9e2276d70ec00e5115a8f89962c1015b45951460917b585be2` | `d34c871f577d1c9e2276d70ec00e5115a8f89962c1015b45951460917b585be2` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/07_Immunization_Ondo/immunization_centers.csv`| 35,399 | `92814aea7a0f01dc6cc3d7723e9d8ea4ef2a97b54a0c2a1087476faca2ed6779` | `92814aea7a0f01dc6cc3d7723e9d8ea4ef2a97b54a0c2a1087476faca2ed6779` | **MATCH (Unchanged)** |
| `MotherlyPulse_Data/mamabench_evaluation/mamabench_cases.csv`| 156,626 | `18d104b21bde9fadd41f94bcaef979bd2af482d7af3176b28d7573b44e34d4be` | `18d104b21bde9fadd41f94bcaef979bd2af482d7af3176b28d7573b44e34d4be` | **MATCH (Unchanged)** |
| `models/risk_level_model.joblib` | 5,535,093 | `2fb0deeb50690e2618aeba8280a88244a8cc1aed1c70e432a27fec5f154eab57` | `2fb0deeb50690e2618aeba8280a88244a8cc1aed1c70e432a27fec5f154eab57` | **MATCH (Unchanged)** |
| `models/complication_model.joblib` | 26,539,577 | `9138b4ae5bb14848f2e91d80882d746e8723a81b5df275b65929534593c07ed8` | `9138b4ae5bb14848f2e91d80882d746e8723a81b5df275b65929534593c07ed8` | **MATCH (Unchanged)** |

---

## 3. Automated Validation Suite Results (31 / 31 Checks Passing)

Both official dataset validation scripts were executed independently from the terminal:

### 1. Core Dataset Validation (`validate_data.py`)
```bash
python MotherlyPulse_Data/validate_data.py
```
- **Result:** `19 / 19 checks passed`.
- **Verified Properties:**
  - `english_pairs.csv`: 200 pairs, 100% complete text, zero null fields, valid urgency category values (`routine`, `priority`, `emergency`).
  - `passages.csv`: 64 records, unique passage IDs, correct topic categorization.
  - `emergency_rules.csv`: 42 rules, all danger signs populated, valid facility referrals.
  - `facilities.csv`: 82 facilities across all 18 Local Government Areas (LGAs) of Ondo State.
  - `immunization_centers.csv`: 94 centers, verified operational days and vaccine lists.

### 2. Multilingual Dataset Validation (`validate_multilingual_data.py`)
```bash
python MotherlyPulse_Data/validate_multilingual_data.py
```
- **Result:** `12 / 12 checks passed`.
- **Verified Properties:**
  - `yoruba_pairs.csv`: Exactly 200 records, 1-to-1 sequential alignment with English `pair_id` (1..200).
  - `pidgin_pairs.csv`: Exactly 200 records, 1-to-1 sequential alignment with English `pair_id` (1..200).
  - `multilingual_pairs.csv`: Parallel alignment across English, Yoruba, and Nigerian Pidgin.
  - `adaptation_template.csv`: Exactly 200 decomposed records with all 4 slots populated.

---

## 4. Audit Safety Confirmation

- All adversarial test executions were run in-memory or through isolated scratch test scripts (`scratch/adversarial_audit.py`).
- No dataset CSV or JSON files were opened in write mode or modified in any way.
- The repository state remains completely aligned with the cryptographic baseline established prior to the audit.
