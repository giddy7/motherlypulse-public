# Ondo State Healthcare Facility Verification Report

**Project:** MotherlyPulse Maternal Health Assistant  
**Target Cluster:** Akure South & Akure North Local Government Areas (LGAs), Ondo State, Nigeria  
**Date of Verification:** October 29, 2026  
**Auditor:** MotherlyPulse Data Engineering & Preparation Subsystem  

---

### 1. Executive Summary & Registry Context
To support the nearest-facility lookup module without fabricating health data or hallucinating service availability, 12 healthcare facilities were identified and catalogued across **Akure South** (8 facilities) and **Akure North** (4 facilities).

Data sources used for cross-checking:
1. **Federal Ministry of Health and Social Welfare (FMoHSW) - National Health Facility Registry (NHFR)** (`SRC-FMOH-HFR-2024`): Official master facility list portal (`hfr.fmohconnect.gov.ng`).
2. **Ondo State Ministry of Health & Primary Health Care Development Agency (OSPHCDA)** (`SRC-ONDO-MOH-2024`): Official registry and facility locator (`ondostatemoh.gov.ng`).
3. **National Bureau of Statistics / Ondo State Contributory Health Commission (ODCHC)**: Health scheme accredited service provider listings.

---

### 2. Breakdown of Verification Status
Of the 12 verified facilities:
* **`cross_checked_second_source` (7 facilities):** Confirmed in both NHFR and official Ondo State Ministry of Health / ODCHC directories:
  - UNIMEDTH Akure Complex (`FAC-OND-AKS-001`)
  - State Specialist Hospital / Mother and Child Hospital Oke-Aro (`FAC-OND-AKS-002`)
  - Primary Health Centre, Arakale (`FAC-OND-AKS-003`)
  - Comprehensive Health Centre, Oba-Ile (`FAC-OND-AKN-001`)
  - Comprehensive Health Centre, Ita-Ogbolu (`FAC-OND-AKN-002`)
  - Primary Health Centre, Iju (`FAC-OND-AKN-003`)
  - Basic Health Centre, Igoba (`FAC-OND-AKN-004`)
* **`listed_in_registry_only` (5 facilities):** Documented in NHFR and official LGA primary health listings, but awaiting secondary field operational validation:
  - Primary Health Clinic, Danjuma (`FAC-OND-AKS-004`)
  - Basic Health Centre, Isolo (`FAC-OND-AKS-005`)
  - Basic Health Centre, Oke-Aro (`FAC-OND-AKS-006`)
  - Basic Health Centre, Adegbola (`FAC-OND-AKS-007`)
  - Basic Health Centre, Aule (`FAC-OND-AKS-008`)
* **`contact_confirmed`:** 0 facilities (telephonic audits could not be completed electronically without human telephone calls).
* **`unconfirmed`:** 0 facilities.

---

### 3. Geographical Coordinates Audit
* **Facilities with Geocoordinates:** 8 facilities (66.7%) have verified latitude and longitude coordinates.
* **Facilities Flagged "Needs Coordinates":** 4 facilities (33.3%) — namely Isolo, Oke-Aro Basic Health Centre, Adegbola, and Aule. In accordance with Rule 1 and Rule 6 (*No Invention*), coordinate fields were intentionally left blank rather than approximated. The team's on-ground field members in Akure will capture exact GPS coordinates during clinic baseline visits.

---

### 4. Service Capabilities & Operational Caveats
* **Emergency & Delivery Services:** Delivery capability is explicitly marked only where verified by primary health guidelines or state comprehensive designations. Basic Health Centres (BHCs) are recorded as `"needs confirmation"` regarding night delivery coverage.
* **Telephone Numbers:** The master registries do not reliably list public dispatch numbers for individual PHCs. National and State hotlines (**112**, **08055300300**, and ODEMSA lines) are therefore provided as the verified escalation conduits.

