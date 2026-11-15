# MotherlyPulse Final Evidence Quality & Safety Audit Report

**Project:** MotherlyPulse Maternal & Infant Health Assistant  
**Release:** Post-Audit Corrections & Dynamic Triage Baseline  
**Date:** October 30, 2026  
**Auditor:** Quality Assurance, Data Verification & Clinical Safety Subsystem  

---

## 1. Structural Validation vs. Factual Verification

To ensure transparent reporting and avoid conflating automated script execution with empirical clinical evidence, the project establishes a strict separation:

* **Structural Validation (Automated):** **PASSED (19/19 tests, 100%)**. Confirms schema compliance, invariant field presence, referential key linkage, bounding box limits, prefix uniformity, exact record counts, and dynamic precedence rules.
* **Factual Verification (Evidence-Based):**
  - **Verified (4 facilities / 4 immunization centres):** Institutional presence, physical campus location, Level-3 CEmONC capacity, and daily fixed immunization services supported by facility-specific state/federal documentation.
  - **Partially Verified (51 facilities / 39 immunization centres):** Public existence and LGA location supported by official registry entries; specific 24/7 operating hours, CEmONC readiness, local session schedules, and direct phone responsiveness remain **unconfirmed pending field audit**.
  - **Unverified (2 emergency contact numbers):** National ambulance desk line (`+234 805 530 0300`) and alternative state ambulance hotline (`112`) are documented in official policy but marked **unverified** pending direct live call testing.

---

## 2. Coordinate Precision Reconciliation (From 6 to 4 Confirmed Coordinates)

In previous drafts, 6 facilities were marked as `facility_confirmed` (UNIMEDTH Akure, SSH Oke-Aro, PHC Arakale, CHC Isolo, UNIMEDTH Ondo, and FMC Owo). 

**Audit Correction:**
* **Affected Records:** Primary Health Centre Arakale (`FAC-OND-AKS-003`) and Comprehensive Health Centre Isolo (`FAC-OND-AKS-005`).
* **Correction Justification:** While both facilities are established in Akure urban wards, their coordinates in the dataset represent road/street-level community midpoints rather than surveyed physical gate entrances.
* **Reconciled Status:** Arakale and Isolo were updated to **`community_centroid`**. Exactly **4 facilities** (the major apex hospitals with dedicated surveyed medical campuses) are retained as **`facility_confirmed`**:
  1. `FAC-OND-AKS-001`: UNIMEDTH Akure Complex (`7.2514, 5.1931`)
  2. `FAC-OND-AKS-002`: State Specialist Hospital Oke-Aro (`7.2389, 5.1972`)
  3. `FAC-OND-ONW-001`: UNIMEDTH Ondo Complex (`7.0833, 4.8333`)
  4. `FAC-OND-OWO-001`: Federal Medical Centre Owo (`7.1962, 5.5868`)

---

## 3. Hospital Capabilities & Service Status Reassessment

A facility listing in the National Health Facility Registry is not proof that services are operational 24/7. Consequently, all capability descriptions in `facilities.csv` and `facilities.json` have been revised:

1. **CEmONC & Blood Bank Claims:**
   - Only the 4 apex hospitals have documented Comprehensive Emergency Obstetric and Newborn Care with functional blood banks.
   - For all 14 Secondary General Hospitals, the delivery status is explicitly qualified: *"Secondary obstetric care designated; 24/7 surgical theatre uptime unconfirmed"*.
   - For all 37 primary clinics, status is explicitly qualified: *"Basic delivery designated under primary health framework; 24-hour service unconfirmed"*.
2. **Emergency Referral Capabilities:**
   - Primary health centres are classified as: *"Basic primary stabilization only; emergency cases referred to secondary hospital"*.

---

## 4. Reconciled Data Quality Metrics Table

| Metric | Primary Facilities Dataset | Immunization Delivery Points |
| :--- | :---: | :---: |
| **Total Physical Records** | **55** | **43** |
| **Verified Records** | **4** (7.3%) | **4** (9.3%) |
| **Partially Verified Records** | **51** (92.7%) | **39** (90.7%) |
| **Unverified Records** | **0** (0.0%) | **0** (0.0%) |
| **`facility_confirmed` Coordinates** | **4** (7.3%) | **4** (9.3%) |
| **`community_centroid` Coordinates** | **48** (87.3%) | **37** (86.0%) |
| **`unknown` Coordinates (Needs GPS)** | **3** (5.5%) | **2** (4.7%) |
| **Direct Facility Phone Numbers** | **0** (Unlisted in NHFR) | **0** (Unlisted in NHFR) |

---

## 5. Conversational Dataset Expansion & Post-Audit Corrections

### 5.1 Dataset Distribution & Record Counts
* **Total Records:** Exactly **200 conversational pairs** in both CSV and JSONL formats (100% field parity).
* **Maternal Pregnancy Pairs:** **100 pairs** (`PAIR-PRG-001` to `PAIR-PRG-100`).
* **Infant & Postpartum Care Pairs:** **100 pairs** (`PAIR-INF-001` to `PAIR-INF-100`).
* **Dataset Splits:** **160 Train records (80%)**, **40 Test records (20%)** (80 train / 20 test per domain).
* **Strict Language Restriction:** **100% English ONLY**. Zero automated or machine translations.
* **Target Adaptation Template:** All 200 records indexed in `adaptation_template.csv` with target columns completely blank for manual translation.
* **Response Prefix Standardization:** 100% of all 200 responses strictly begin with their category prefix: `EMERGENCY:`, `PRIORITY:`, or `ROUTINE:`.

### 5.2 Post-Audit Clinical Record Corrections
Following clinical audit on October 30, 2026, the following 5 records were corrected:

1. **`PAIR-PRG-042` (Reclassified: Priority $\rightarrow$ Emergency):**
   - *Clinical Issue:* Foul-smelling greenish discharge with lower pelvic pain in pregnancy indicates severe acute reproductive tract or intra-amniotic infection (chorioamnionitis), carrying high risk of preterm labour and sepsis. Escalated to **`emergency`**.
2. **`PAIR-INF-087` (Reclassified: Priority $\rightarrow$ Emergency):**
   - *Clinical Issue:* Prolonged infant jaundice accompanied by pale, chalky-white (acholic) stools indicates neonatal cholestasis / biliary atresia. Immediate pediatric hepatobiliary referral is required without delay. Escalated to **`emergency`**.
3. **`PAIR-INF-011` (Reclassified: Priority $\rightarrow$ Emergency):**
   - *Clinical Issue:* Any documented fever ($\ge 38.0^\circ\text{C}$) in an infant younger than 3 months is a critical medical red flag for neonatal sepsis. Reclassified to **`emergency`** with immediate emergency room referral and explicit refusal to provide paracetamol dosage.
4. **`PAIR-PRG-037` (Reclassified: Priority $\rightarrow$ Emergency):**
   - *Clinical Issue:* Regular, strong contractions every 4 minutes lasting 2 hours at 39 weeks (term) indicate established active labour requiring immediate presentation for admission. Escalated to **`emergency`**.
5. **`PAIR-PRG-068` (Priority Response Clarified):**
   - *Clinical Issue:* Fasting blood glucose of 105 mg/dL. Text updated to clarify WHO/IADPSG criteria ($\ge 92\text{ mg/dL}$ threshold) and emphasize time-sensitive 24–48h antenatal follow-up. Retained as **`priority`**.

### 5.3 Reconciled Urgency Distribution
| Urgency Category | Record Count | Percentage | Primary Clinical Scope |
| :--- | :---: | :---: | :--- |
| **EMERGENCY** | **60** | 30.0% | Acute hemorrhage, convulsions/eclampsia, absent fetal movements, active labour at term, infant fever < 3 mo, chest indrawing, biliary atresia, puerperal sepsis, suicidality |
| **PRIORITY** | **41** | 20.5% | Time-sensitive vaccination appointments, mastitis, hyperemesis, gestational diabetes screening, antenatal depression, UTI symptoms |
| **ROUTINE** | **99** | 49.5% | Maternal sleep position, infant feeding on demand, tummy time, normal lochia stages, and clinical safety declines |
| **TOTAL** | **200** | **100.0%** | Grounded across 35 clinical passages in `passages.csv` |

### 5.4 Decoupling of Clinical Urgency from Medication Safety
Clinical urgency is determined strictly by the patient's physiological state and symptoms. Requests for drug dosages, prescriptions, or herbal concoctions (*agbo*) trigger independent medication safety handling:
- **Emergency + Medication Request:** The system issues immediate emergency escalation **AND** refuses home medication/dosages.
- **Priority + Medication Request:** The system issues a prompt clinical visit directive **AND** refuses drug prescription.
- **Routine + Medication Request:** The system issues standard clinical safety decline.
Medication requests never downgrade an emergency or priority condition to routine.
