# MotherlyPulse Data Package (Capstone Scope)

**Project:** MotherlyPulse Maternal & Child Health Assistant  
**Institution:** Federal University of Technology, Akure (FUTA) — Africa AI Upskilling Program  
**Release Version:** v1.0 (Capstone Baseline Data Package)  
**Date:** October 29, 2026  
**Primary Architect / Maintainer:** Goodness Ajayi & Project Team  

---

## 1. Overview and Purpose
MotherlyPulse is an AI-powered conversational maternal health assistant designed to operate over Telegram and WhatsApp for pregnant women and mothers up to 12 months after delivery in Nigeria. The project aims to provide scheduled appointment/medication reminders, culturally appropriate health education, rule-based emergency triage, and verified local facility referral.

This dataset package serves as the verified data substrate for:
1. Grounding a quantized/fine-tuned language model (Gemma 3 1B using LoRA).
2. Supplying a deterministic rule-based emergency triage engine.
3. Powering a localized primary healthcare facility referral directory for Akure, Ondo State.

---

## 2. Directory Structure
```text
MotherlyPulse_Data/
├── 00_Project_Docs/                  # Project proposals, scope definitions, data cards
├── 01_Sources/                       # Authoritative source summaries and master register
│   ├── source_register.csv           # Master register of all clinical and registry sources
│   └── source_summaries.txt          # Summaries of WHO, FMoH, and state guidelines
├── 02_Passages/                      # Grounding passages for RAG and QA
│   ├── passages.csv                  # 35 structured plain-English health passages
│   ├── passages.json                 # JSON formatted equivalent
│   └── create_passages.py            # Transformation & validation script
├── 03_Emergency_Rules/               # Deterministic safety triage engine definitions
│   ├── emergency_rules.csv           # 24 danger sign triage rules
│   ├── emergency_rules.json          # JSON formatted equivalent
│   ├── rule_traceability.csv         # Clinical lineage from guideline to rule
│   ├── emergency_contacts.csv        # Confirmed national & Ondo State emergency dispatch lines
│   ├── emergency_response_notes.md   # Architectural principles for emergency routing
│   └── create_emergency_rules.py     # Rule generation script
├── 04_Conversation_Data/             # SFT and alignment dialogue dataset
│   ├── english_pairs.jsonl           # 40 dialogue pairs (32 train, 8 test)
│   ├── english_pairs.csv             # Tabular version
│   ├── emergency_scenarios_en.csv    # 5 full emergency scenario dialogues
│   ├── safety_tests_en.csv           # 10 adversarial boundary and safety unit tests
│   ├── adaptation_template.csv       # Multi-language adaptation template (Yo, Ha, Ig, Pcm)
│   ├── intent_definitions.md         # Intent disambiguation and boundary specifications
│   └── create_conversation_pairs.py  # Pair compilation script
├── 05_Facilities_Ondo/               # Verified healthcare facility directory
│   ├── facilities.csv                # 12 verified facilities in Akure North & South
│   ├── facilities.json               # JSON formatted equivalent
│   ├── facility_verification_report.md # Verification methodology and registry audit
│   └── create_facilities.py          # Directory compilation script
└── 06_Reports/                       # Governance, quality, and clinical review audits
    ├── README.md                     # This file
    ├── data_quality_report.md        # Comprehensive integrity metrics and field audits
    ├── gaps_and_limits.md            # Transparent operational constraints and known gaps
    ├── clinical_review_checklist.md  # Formal verification sheet for clinical auditors
    ├── completion_report.md          # Project deliverable reconciliation report
    └── validate_data.py              # Automated dataset integrity validator
```

---

## 3. Data Provenance & Authoritative Citations
All medical content originates strictly from official, non-copyright-infringing, public-domain or CC BY-NC-SA 3.0 IGO licensed health guidelines:
- **World Health Organization (WHO):**
  - *WHO recommendations on antenatal care for a positive pregnancy experience (2016)*
  - *WHO recommendations on maternal and newborn care for a positive postnatal experience (2022)*
  - *Managing Complications in Pregnancy and Childbirth (IMPAC 2nd Ed, 2017)*
- **Federal Ministry of Health and Social Welfare (Nigeria):**
  - *National Antenatal Care Guidelines and Training Manual (2020)*
  - *National Life Saving Skills (LSS) Protocol for Primary Healthcare (2019)*
  - *Nigeria Health Facility Registry (NHFR) Master List (2024)*
- **Ondo State Authorities:**
  - *Ondo State Ministry of Health & Primary Health Care Development Agency (OSPHCDA) Directory (2024)*
  - *Ondo State Emergency Medical Services Agency (ODEMSA)*
- **UNICEF:**
  - *Facts for Life: Maternal and Newborn Danger Signs Community Guide (2021)*

---

## 4. Key Rules and System Boundaries
1. **No Medical Hallucination / Invention:** The assistant never invents diseases, medications, or facility records.
2. **Deterministic Emergency Escalation:** Red flags bypass the LLM and output an immediate fixed urgent-care referral with emergency dispatch numbers.
3. **Clinical Role Boundary:** The assistant explicitly declines to diagnose conditions, prescribe medications, or recommend dosages.
4. **Pending Clinical Review:** All rules, passages, and conversation pairs are marked provisional pending review by certified Nigerian midwives and medical officers.

