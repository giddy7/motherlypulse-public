# MotherlyPulse — Geospatial Health Facility & Immunization Directory Audit Report

## 1. Executive Summary

This audit establishes the ground-truth state of the Ondo State health facility and immunization post directories used by MotherlyPulse.

### Key Audit Findings:
- **True Facility Count:** Exactly **55 facilities** across all 18 Local Government Areas (LGAs) of Ondo State (correcting earlier unverified documentation claims of 82 facilities).
- **True Immunization Center Count:** Exactly **43 routine immunization posts** across all 18 LGAs (correcting earlier unverified documentation claims of 94 centers).
- **Verification Status:**
  - Facilities: **4 verified** (state hospitals / major specialist centers confirmed with ground coordinates), **51 partially verified** (sourced from National Health Facility Registry / Ondo State Ministry of Health gazettes, but coordinates are town centroids).
  - Immunization Centers: **4 verified**, **39 partially verified**.
- **Coordinate Precision:**
  - Facilities: 4 `facility_confirmed`, 48 `community_centroid`, 3 `unknown`.
  - Immunization Centers: 4 `facility_confirmed`, 37 `community_centroid`, 2 `unknown`.
- **Clinical Honesty Scaffolding Enforced:**
  - `LocationService` programmatically attaches transparency disclaimers:
    - `"Approximate town location; ask locally for the exact entrance"` whenever `coordinate_precision != 'facility_confirmed'`.
    - `"Session days may have changed; contact the clinic before travelling"` on all immunization centers.
    - Excludes any records with invalid coordinates or marked `unverified`.

---

## 2. Facilities Directory Breakdown by LGA (55 Total)

| Local Government Area (LGA) | Facility Count | Verified | Partially Verified | Primary Facility Types |
| :--- | :--- | :--- | :--- | :--- |
| **Akure South** | 8 | 2 | 6 | State Specialist Hospital, Comprehensive Health Centres, PHCs |
| **Akure North** | 4 | 0 | 4 | General Hospital, Primary Health Centres |
| **Akoko North-East** | 3 | 0 | 3 | State Specialist Hospital Ikare, PHCs |
| **Akoko North-West** | 3 | 0 | 3 | General Hospital Okeagbe, PHCs |
| **Akoko South-East** | 3 | 0 | 3 | General Hospital Isua, PHCs |
| **Akoko South-West** | 3 | 0 | 3 | General Hospital Oka, PHCs |
| **Idanre** | 3 | 0 | 3 | General Hospital Idanre, PHCs |
| **Ifedore** | 2 | 0 | 2 | Comprehensive Health Centre Igbara-Oke, PHCs |
| **Ilaje** | 3 | 0 | 3 | General Hospital Igbokoda, PHCs |
| **Ile Oluji/Okeigbo** | 2 | 0 | 2 | General Hospital Ile-Oluji, PHCs |
| **Irele** | 2 | 0 | 2 | General Hospital Ode-Irele, PHCs |
| **Odigbo** | 3 | 0 | 3 | General Hospital Ore, PHCs |
| **Okitipupa** | 3 | 1 | 2 | State Specialist Hospital Okitipupa, PHCs |
| **Ondo East** | 3 | 0 | 3 | Comprehensive Health Centre Bolorunduro, PHCs |
| **Ondo West** | 3 | 1 | 2 | Mother & Child Hospital / UNIMEDTH Ondo, PHCs |
| **Ose** | 2 | 0 | 2 | General Hospital Ifon, PHCs |
| **Owo** | 3 | 0 | 3 | State Specialist Hospital Owo, PHCs |
| **Ese Odo** | 2 | 0 | 2 | General Hospital Igbekebo, PHCs |
| **Total** | **55** | **4** | **51** | **All 18 LGAs Represented** |

---

## 3. Immunization Directory Breakdown by LGA (43 Total)

| Local Government Area (LGA) | Immunization Centers | Verified | Partially Verified | Schedule / Session Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Akure South** | 7 | 2 | 5 | Fixed daily sessions at specialist centres; weekly at PHCs |
| **Akure North** | 4 | 0 | 4 | Weekly routine immunization sessions |
| **Akoko North-East** | 2 | 0 | 2 | Fixed and outreach sessions |
| **Akoko North-West** | 2 | 0 | 2 | Fixed and outreach sessions |
| **Akoko South-East** | 2 | 0 | 2 | Fixed routine sessions |
| **Akoko South-West** | 2 | 0 | 2 | Fixed and outreach sessions |
| **Ese Odo** | 2 | 0 | 2 | Riverine health posts with cold-chain outreach |
| **Idanre** | 2 | 0 | 2 | Fixed weekly sessions |
| **Ifedore** | 2 | 0 | 2 | Fixed weekly sessions |
| **Ilaje** | 2 | 0 | 2 | Riverine outreach posts |
| **Ile Oluji/Okeigbo** | 2 | 0 | 2 | Fixed weekly sessions |
| **Irele** | 2 | 0 | 2 | Fixed weekly sessions |
| **Odigbo** | 2 | 0 | 2 | High-volume commercial junction PHCs |
| **Okitipupa** | 2 | 1 | 1 | State Specialist Hospital daily; PHC weekly |
| **Ondo East** | 2 | 0 | 2 | Fixed weekly sessions |
| **Ondo West** | 2 | 1 | 1 | Mother & Child UNIMEDTH daily; PHC weekly |
| **Ose** | 2 | 0 | 2 | Fixed weekly sessions |
| **Owo** | 2 | 0 | 2 | State Specialist Hospital daily; PHC weekly |
| **Total** | **43** | **4** | **39** | **All 18 LGAs Represented** |

---

## 4. Metadata Schema & Data Governance Audit

Both directory files (`facilities.csv` and `immunization_centers.csv`) adhere strictly to the Phase 2 schema:
- `source_id`: Sourced from official Ondo State Ministry of Health registry or Federal Ministry of Health Master Health Facility List (MHFL).
- `verification_status`: Categorized into `verified` (ground confirmed) or `partially_verified` (administrative record confirmed, awaiting physical coordinates).
- `coordinate_precision`: Explicitly distinguishes `facility_confirmed` (GPS taken at hospital gate) from `community_centroid` (approximate town GPS coordinates).

### Audit Verdict:
**PASS.** Earlier discrepancies in row counts have been reconciled with ground truth records. Clinical honesty caveats are systematically injected into all consumer endpoints (`LocationService`, Telegram bot, and WhatsApp adapter).

