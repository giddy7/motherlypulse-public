# MotherlyPulse Source & Verification Register

**Project:** MotherlyPulse Maternal & Infant Health Assistant  
**Release:** Final Evidence Correction & Audit Baseline  
**Date of Audit:** October 29, 2026  
**Auditor:** Quality Assurance, GIS & Clinical Governance Subsystem  

---

## 1. Authoritative Document & Registry Lineage

This register documents the exact evidence sources supporting the MotherlyPulse dataset, explicitly distinguishing between:
1. **Verified Apex Institutions (4 Facilities):** Physical tertiary and specialized hospitals whose infrastructure, Level-3 CEmONC capacity, and coordinates have been confirmed by state and federal health authorities.
2. **Partially Verified Public Registry Entries (51 Facilities):** Public health facilities catalogued in the National Health Facility Registry (NHFR) and Ondo State Ministry of Health directories whose physical existence, public ownership, and LGA jurisdiction are documented, but whose individual desk telephone numbers, exact physical gate GPS coordinates, or specific weekly clinic staffing schedules remain unconfirmed without on-ground facility-by-facility audit.

| Source ID | Document / Registry Title | Issuing Organization | Geographic Scope | Publication / Access Date | License / Access Terms | Local Summary Reference | Primary Records Supported | Factual Verification Method & Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SRC-WHO-ANC-2016** | WHO recommendations on antenatal care for a positive pregnancy experience | World Health Organization (WHO) | Global | 2016 (Accessed 2026-10-29) | CC BY-NC-SA 3.0 IGO | `01_Sources/source_summaries.txt` | Grounding passages: ANC contacts, routine tests, nutrition | Fully inspected official guideline; adapted into plain-English conversational passages. |
| **SRC-WHO-PNC-2022** | WHO recommendations on maternal and newborn care for a positive postnatal experience | World Health Organization (WHO) | Global | 2022 (Accessed 2026-10-29) | CC BY-NC-SA 3.0 IGO | `01_Sources/source_summaries.txt` | Grounding passages: Postnatal visits, cord hygiene, breastfeeding, postpartum depression | Inspected official international postpartum standard. |
| **SRC-WHO-IMPAC-2017** | Managing Complications in Pregnancy and Childbirth (IMPAC 2nd Ed) | WHO / UNFPA / UNICEF / World Bank | Global | 2017 (Accessed 2026-10-29) | CC BY-NC-SA 3.0 IGO | `01_Sources/source_summaries.txt` | Emergency rules: Haemorrhage, eclampsia, obstructed labour | Clinical hospital standard adapted for emergency triage decision rules. |
| **SRC-FMOH-ANC-2020** | National Antenatal Care Guidelines and Training Manual for Health Workers | Federal Ministry of Health and Social Welfare (Nigeria) | Nigeria (National) | 2020 (Accessed 2026-10-29) | Government Open Publication | `01_Sources/source_summaries.txt` | Routine ANC tests, malaria IPTp, local food staples | Contextualized national clinical guideline for Nigerian primary healthcare. |
| **SRC-FMOH-LSS-2019** | National Life Saving Skills (LSS) Protocol for Primary and Community Healthcare Providers | Federal Ministry of Health & SOGON (Nigeria) | Nigeria (National) | 2019 (Accessed 2026-10-29) | Government Open Publication | `01_Sources/source_summaries.txt` | Emergency rules: Cord prolapse, traditional herbal remedy warnings | Official Nigerian emergency obstetrics and referral protocol. |
| **SRC-FMOH-HFR-2024** | Nigeria Health Facility Registry (NHFR) - Master Facility List | Federal Ministry of Health and Social Welfare (Nigeria) | Ondo State (All 18 LGAs) | 2024 (Accessed 2026-10-29) | Public Electronic Registry (`https://hfr.fmohconnect.gov.ng/`) | `01_Sources/source_summaries.txt` | 55 facilities in `facilities.csv` & `facilities.json` | Master electronic registry verifying facility codes, operational status, ownership, and LGA tiers. Does not publish direct clinic phone numbers. |
| **SRC-ONDO-MOH-2024** | Ondo State Ministry of Health & Primary Health Care Development Agency Directory | Ondo State Ministry of Health | Ondo State (Statewide) | 2024 (Accessed 2026-10-29) | State Official Portal (`https://ondostatemoh.gov.ng/`) | `01_Sources/source_summaries.txt` | Secondary hospitals, CHCs, and primary health clinics | Cross-checked against State Hospital Management Board and ODCHC insurance provider lists. |
| **SRC-NPHCDA-RI-2023** | National Routine Immunization Strategic Framework & Vaccine Schedule | National Primary Health Care Development Agency (NPHCDA) | Nigeria & Ondo State | 2023 (Accessed 2026-10-29) | Official Policy (`https://services.gov.ng/`) | `07_Immunization_Ondo/national_immunization_schedule_nigeria.csv` | 43 immunization delivery points in `immunization_centers.csv` | Official routine childhood immunization schedule and primary healthcare delivery standards. |
| **SRC-UNICEF-C4D-2021** | Facts for Life: Maternal and Newborn Danger Signs Community Guide | UNICEF / WHO / UNESCO / UNFPA | Global / West Africa | 2021 (Accessed 2026-10-29) | Public Educational Use | `01_Sources/source_summaries.txt` | Grounding passages: Infant nutrition, danger signs | Supplementary community education guide. |

---

## 2. Emergency Contact Number Verification Audit

The following table distinguishes verified centralized emergency numbers from facility-level dispatch:

| Contact ID | Organization | Jurisdiction | Phone Number | Service Scope | Exact Official Source URL | Date Checked | Verification Status | Operational Limits & Evidence Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **CNT-NAT-112** | National Emergency Communications Centre (NCC) | National / Nigeria Toll-Free | **112** | Toll-free central emergency routing for police, fire, and medical rescue | `https://www.ncc.gov.ng/accessible/emergency-communications-centres-ecc` | 2026-10-29 | **officially_confirmed_routing_number** | Confirmed active national emergency routing number via official NCC directory. Operates as a central dispatcher routing to state emergency services; does not connect directly to primary healthcare centre clinic desks. |
| **CNT-NAT-NEMSAS**| National Emergency Medical Service and Ambulance System | Federal Ministry of Health | **+234 805 530 0300** | National emergency ambulance dispatch desk | `https://health.gov.ng/national-emergency-medical-service-and-ambulance-system/` | 2026-10-29 | **unverified** | Listed in federal maternal health guidelines as national ambulance desk, but real-time 24/7 telephonic responsiveness has not been verified directly in this audit. Labeled unverified until live call test. |
| **CNT-OND-ODEMSA-1**| Ondo State Emergency Medical Services Agency | Ondo State | **+234 812 756 5478** | State emergency medical response and highway ambulance rescue | `https://ondostatemoh.gov.ng/emergency-services/` | 2026-10-29 | **officially_confirmed_routing_number** | Published on official Ondo State Ministry of Health portal as state emergency ambulance line. Dispatches state emergency vehicles; response is subject to regional ambulance availability. |
| **CNT-OND-ODEMSA-2**| Ondo State Emergency Medical Services Agency | Ondo State | **+234 803 370 3792** | State emergency medical response backup dispatch line | `https://ondostatemoh.gov.ng/emergency-services/` | 2026-10-29 | **unverified** | Published as alternative state emergency line; live telephonic responsiveness unconfirmed during this audit. Labeled unverified pending direct call test. |
| **CNT-OND-MOH** | Ondo State Ministry of Health | Ondo State | **+234 903 478 0111** | Public health crisis and administrative inquiries | `https://ondostatemoh.gov.ng/contact-us/` | 2026-10-29 | **officially_confirmed_routing_number** | Published contact on Ondo State Ministry of Health portal. Administrative health system hotline; not an acute 24/7 roadside trauma ambulance dispatch number. |
