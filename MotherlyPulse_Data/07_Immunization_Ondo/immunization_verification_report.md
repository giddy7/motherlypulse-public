# Ondo State Routine Immunization Centers & Schedule Verification Report

**Project:** MotherlyPulse Maternal & Child Health Assistant  
**Cluster:** Akure South & Akure North Local Government Areas (LGAs), Ondo State, Nigeria  
**Reporting Date:** October 29, 2026  
**Auditor:** MotherlyPulse Data Engineering & Health Systems Subsystem  

---

### 1. Scope and Strategic Context
Following the expansion to include routine immunization data, 11 dedicated routine immunization delivery centres have been verified across **Akure South LGA** (7 centres) and **Akure North LGA** (4 centres). 

Routine immunization in Nigeria is coordinated federally by the **National Primary Health Care Development Agency (NPHCDA)** and implemented at state level by the **Ondo State Primary Health Care Development Agency (OSPHCDA)**. All routine childhood immunizations in government public health facilities are delivered **completely free of charge** under national policy.

---

### 2. Breakdown of Delivery Facilities by Level of Care

| Facility Level | Centres Catalogued | Key Representative Facilities | Operational Pattern |
| :--- | :--- | :--- | :--- |
| **Tertiary / Specialist** | 2 | UNIMEDTH Akure, State Specialist Hospital (Mother & Child) Oke-Aro | Daily fixed sessions (Monday–Friday) with continuous birth dose administration (BCG, OPV 0, Hep B 0). |
| **Comprehensive Health Centres (CHCs)** | 3 | CHC Isolo, CHC Oba-Ile, CHC Ita-Ogbolu | Fixed immunization clinic days (typically 2 days per week), cold chain supported by Solar Direct Drive (SDD) refrigeration. |
| **Primary / Basic Health Centres** | 6 | PHC Arakale, PHC Danjuma, PHC Iju, BHC Adegbola, BHC Aule, BHC Igoba | Weekly designated fixed immunization sessions (e.g., Wednesdays/Thursdays) with vaccine carrier replenishment from LGA cold store. |

---

### 3. Verification & Geographic Integrity
- **State Validation:** 100% of immunization centres are situated strictly within **Ondo State**.
- **LGA Compliance:** 7 centres in Akure South, 4 centres in Akure North.
- **Coordinates:** 9 out of 11 centres (81.8%) have verified GPS latitude/longitude. The 2 basic health centres (Adegbola and Aule) are explicitly marked `"needs coordinates"` to uphold the non-invention rule until on-ground field geotagging is completed.
- **Cold Chain Verification:** Cold chain reliability has been categorized based on OSPHCDA state inventory (Solar Direct Drive refrigerators vs. portable vaccine carriers).

---

### 4. Integration with MotherlyPulse Conversational Features
This immunization dataset directly empowers MotherlyPulse's core user journey:
1. **Automated Vaccination Reminders:** The assistant can schedule reminders based on the baby's date of birth aligning with the 6-week, 10-week, 14-week, 9-month, and 12-month national milestones documented in [`national_immunization_schedule_nigeria.csv`](MotherlyPulse_Data/07_Immunization_Ondo/national_immunization_schedule_nigeria.csv).
2. **Nearest Immunization Post Navigation:** When mothers inquire *"Where can I take my baby for 6-week injection around Arakale or Oba-Ile?"*, the system can query [`immunization_centers.csv`](MotherlyPulse_Data/07_Immunization_Ondo/immunization_centers.csv) to return the exact center, clinic days, and hours without guessing.

