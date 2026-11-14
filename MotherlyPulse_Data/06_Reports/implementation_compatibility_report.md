# MotherlyPulse Implementation & Schema Compatibility Report

**Project:** MotherlyPulse Maternal & Infant Health Assistant  
**Release:** Post-Audit Integration & Dynamic Triage Baseline  
**Date:** October 30, 2026  
**Auditor:** Software Architecture & Integration Engineering  

---

## 1. Schema Expansion & Coordinate Precision Handling

To support user safety and prevent navigation errors, both `facilities.csv` and `immunization_centers.csv` incorporate the **`coordinate_precision`** field:

### A. Facilities Dataset (`05_Facilities_Ondo/facilities.csv` & `.json`)
* **Field Order:** `facility_id`, `facility_name`, `facility_type`, `ownership`, `state`, `local_government_area`, `town_or_community`, `street_address`, `latitude`, `longitude`, **`coordinate_precision`**, `telephone`, `maternal_health_services`, `delivery_services`, `emergency_referral_capability`, `source_id`, `date_verified`, `verification_status`, `notes`.
* **Precision Breakdown:**
  - `facility_confirmed`: **4 facilities** (UNIMEDTH Akure, SSH Oke-Aro, UNIMEDTH Ondo, FMC Owo).
  - `community_centroid`: **48 facilities**.
  - `unknown`: **3 facilities** (Oke-Aro BHC, Adegbola BHC, Aule BHC).
* **Application Behavior:**
  - When rendering spatial proximity results, the application checks `coordinate_precision`. If equal to `community_centroid`, it renders an informational pill: *"Approximate Community Location"*.

### B. Immunization Dataset (`07_Immunization_Ondo/immunization_centers.csv` & `.json`)
* **Field Order:** `center_id`, `center_name`, `facility_type`, `ownership`, `state`, `local_government_area`, `ward`, `town_or_community`, `street_address`, `latitude`, `longitude`, **`coordinate_precision`**, `vaccines_offered`, `immunization_schedule_days`, `cold_chain_equipment_status`, `fee_status`, `source_id`, `verification_status`, `notes`.
* **Precision Breakdown:**
  - `facility_confirmed`: **4 centres**.
  - `community_centroid`: **37 centres**.
  - `unknown`: **2 centres** (Adegbola BHC, Aule BHC).
* **Application Behavior:**
  - For the 39 provisional centres, `immunization_schedule_days` explicitly contains *"Provisional (Standard NPHCDA Schedule: Contact clinic to confirm local session days)"*. The chat UI surfaces this advice directly to the mother.

---

## 2. Emergency Contacts Dataset (`03_Emergency_Rules/emergency_contacts.csv`)
* Fields: `contact_id`, `organization`, `jurisdiction`, `phone_number`, `service_scope`, `official_source`, `date_verified`, `verification_status`, `operational_limits_and_notes`.
* Verified lines: National **112**, National **+234 805 530 0300** (NEMSAS), Ondo State **+234 812 756 5478** / **+234 803 370 3792** (ODEMSA), and State MOH **+234 903 478 0111**.

---

## 3. Conversational Dataset Architecture (200 Pairs)

The conversational data layer (`04_Conversation_Data/`) contains exactly 200 pairs split 50/50:
* **Schema:** `pair_id`, `user_group`, `intended_split`, `user_message`, `intent`, `triage_level`, `urgency_category`, `language`, `topic`, `reply`, `passage_id`, `review_status`, `notes`.
* **Distribution Post-Audit:**
  - `user_group`: 100 `pregnancy`, 100 `infant`
  - `intended_split`: 160 `train` (80%), 40 `test` (20%)
  - `urgency_category`: `emergency` (60), `priority` (41), `routine` (99)
  - `language`: 100% `English`
  - `response_prefixes`: 100% compliant with `EMERGENCY:`, `PRIORITY:`, or `ROUTINE:`
* **Adaptation Pipeline:** `adaptation_template.csv` holds all 200 English reference rows with blank target columns for Yoruba (`user_message_yo`, `reply_yo`), Hausa, Igbo, and Pidgin, dedicated exclusively for manual human translation by the project owner.

---

## 4. Application Integration & Accessible Interfaces (`motherlypulse_app/`)

The software application module implements dynamic triage, conversational routing, and accessible local interfaces with **zero external dependencies**:

1. **`DynamicTriageClassifier` (`motherlypulse_app/classifier.py`):**
   - Categorizes incoming user queries into **`EMERGENCY`**, **`PRIORITY`**, or **`ROUTINE`**.
   - Enforces strict precedence:
     $$\text{EMERGENCY} \succ \text{PRIORITY} \succ \text{ROUTINE}$$
   - Decouples clinical urgency from medication safety: A drug or dosage request triggers independent medication safety handling while preserving the true clinical urgency.
   - Multi-turn state persistence: Previous emergency danger signs in conversation history maintain emergency escalation without downgrading.
2. **`MotherlyPulseAssistant` (`motherlypulse_app/assistant.py`):**
   - Routes triage outputs to appropriate response templates.
   - Guarantees every reply starts with `EMERGENCY:`, `PRIORITY:`, or `ROUTINE:`.
   - In emergencies: Escalates hospital care with zero delay. If medication is requested, strictly refuses home dosages/drugs.
   - In priority: Directs prompt clinic evaluation within 24–48 hours.
   - In routine: Grounds guidance in official clinical passages (`passages.csv`).
3. **Local Interactive CLI Interface (`motherlypulse_app/cli.py`):**
   - Launched via `python -m motherlypulse_app`.
   - Allows users to enter inquiries in terminal, inspect the classified urgency category, view medication safety flags, and receive formatted responses.
4. **Local HTTP API Server (`motherlypulse_app/server.py`):**
   - Launched via `python -m motherlypulse_app --serve [port]` (defaults to port 8080).
   - Built natively with Python's built-in `http.server`.
   - Endpoints:
     - `GET /health`: Health status and supported metadata.
     - `POST /api/chat`: JSON payload `{"message": str, "history": list}` $\rightarrow$ JSON response with `urgency_category`, `medication_safety_triggered`, `action`, and `response`.

---

## 5. Automated Validator Scope & Limitations

The test runner [`validate_data.py`](MotherlyPulse_Data/06_Reports/validate_data.py) verifies:
1. **Referential Integrity:** 100% of facilities and immunization centres link to valid `source_id` keys in `source_register.csv`.
2. **Statewide LGA Completeness:** Asserts all 18 LGAs of Ondo State are present in both datasets.
3. **Coordinate Precision Enum Enforcement:** Asserts `coordinate_precision` belongs strictly to `{"facility_confirmed", "community_centroid", "unknown"}`.
4. **Bounding Box Sanity:** Asserts that all populated GPS coordinates fall within Ondo State geographic bounds (5.8°N–8.0°N, 4.4°E–6.2°E).
5. **Conversational Pair Metrics:** Asserts exactly 200 English pairs, 100 pregnancy, 100 infant, 160 train, 40 test, 100% consistent category prefixes, and blank translation columns.
6. **Dynamic Triage Logic:** Asserts emergency override, priority override, separation of medication safety from urgency, and multi-turn state persistence.

### What the Automated Validator Does NOT Test:
- It does **not** test whether physical telephone lines are answered.
- It does **not** perform real-time on-site GPS ground-truthing of physical clinic gates.
- It does **not** substitute for licensed medical clinical judgment.
