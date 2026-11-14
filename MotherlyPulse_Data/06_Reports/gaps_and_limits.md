# MotherlyPulse Gaps, Uncertainties, and Operational Limits

**Project:** MotherlyPulse Maternal Health Assistant  
**Date:** October 29, 2026  
**Auditor:** Technical & Research Lead  

---

### 1. Data and Content Coverage Limits

1. **Local-Language Adaptation Pending:**
   - The current data package delivers English content only. The 40 conversation pairs, 5 emergency scenarios, and 10 safety tests must be adapted into Yoruba, Hausa, Igbo, and Nigerian Pidgin by native fluent speakers using `adaptation_template.csv`.
   - Automated machine translation was intentionally rejected to prevent culturally inaccurate or clinically dangerous translations.

2. **Geographical Scope Narrowed to Akure:**
   - The facility directory is restricted to 12 facilities in Akure South and Akure North LGAs. Pregnant women or mothers residing in the remaining 16 LGAs of Ondo State (e.g., Owo, Ondo West, Okitipupa) or other Nigerian states cannot be geolocated to nearest local facilities without further dataset expansion.

3. **Immunization Directory Omission:**
   - As established in the two-week capstone boundary, comprehensive facility-level vaccine availability schedules (e.g., BCG, OPV, Pentavalent supply days) were excluded and remain future work.

---

### 2. Clinical & Technical Operational Boundaries

1. **Mandatory Clinical Verification Gate:**
   - Every emergency rule, passage, and dialogue pair is currently classified as `pending clinical review`. While extracted directly from authoritative WHO and Nigerian FMoH guidelines, clinical nuance and triage thresholds must be formally endorsed by a practicing obstetrician, nurse-midwife, or public health officer before production deployment.

2. **Missing Facility Coordinates & Direct Telephone Lines:**
   - Four basic health centres (Isolo, Oke-Aro BHC, Adegbola, Aule) lack verified geocoordinates in the electronic registry. Physical on-site GPS verification is required.
   - Public primary health clinics in Nigeria rarely possess fixed landlines or dedicated central call desks. Direct voice calling to PHCs is therefore unavailable; emergency escalation must rely on the national 112 emergency routing and ODEMSA state dispatchers.

3. **Inability to Diagnose or Prescribe:**
   - The system strictly refuses any diagnostic reasoning or therapeutic prescription. This boundary prevents the model from attempting to replace medical personnel or recommending toxic dosages.

---

### 3. Digital Divide & Equity Constraints
- The assistant operates exclusively via Telegram and WhatsApp, requiring a smartphone and active mobile data. Pregnant women who are non-literate, lack internet access, or rely on basic feature phones are excluded from direct interaction. An SMS or voice-interactive IVR pipeline represents a critical future avenue to ensure universal healthcare access.

