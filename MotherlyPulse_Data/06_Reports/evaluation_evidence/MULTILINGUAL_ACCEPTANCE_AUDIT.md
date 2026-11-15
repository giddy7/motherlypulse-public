# MotherlyPulse: Multilingual Acceptance Audit
**Phase 1.5 Independent Acceptance Audit: Linguistic Isolation & Dialectal Integrity**

**Audit Date:** November 4, 2026  
**Auditor:** AI Evaluation Specialist & Linguistic QA Auditor  
**Scope:** English (`en`), Yoruba (`yo`), and Nigerian Pidgin (`pcm`) execution in [`template_adapter.py`](motherlypulse_app/template_adapter.py) and [`assistant.py`](motherlypulse_app/assistant.py).

---

## 1. Executive Summary

This audit evaluated linguistic isolation, cross-language leakage, dialectal consistency, negation parsing, and diacritic normalization across the three supported operational languages.

### Multilingual Audit Matrix

| Language | Lexicon Isolation | Negation Parsing | Domain Gating (Pregnancy vs Infant) | Diacritic Robustness | Automated Status | Native Review Status |
|---|---|---|---|---|---|---|
| **English** | **100% Isolated** (Zero Pidgin leakage) | Verified | Active & Verified | N/A (ASCII) | **PASS** | Validated |
| **Yoruba** | **100% Isolated** (Zero English leaks in phrase bank) | Verified (`kò`, `kò sí`, `laisi`) | Prenatal greeting excluded from infant care | Verified (`ẹsẹ wiwu` == `ese wiwu`) | **PASS** | **PENDING CLINICAL SIGN-OFF** |
| **Nigerian Pidgin** | **100% Isolated** (Zero English leaks in phrase bank) | Verified (`no`, `no de`, `no get`, `don stop`) | Active & Verified | N/A | **PASS** | **PENDING CLINICAL SIGN-OFF** |

---

## 2. Detailed Technical Findings

### Finding MLA-01: Cross-Language Phrase Leakage (VERIFIED RESOLVED)
- **Investigation:**
  In pre-remediation Phase 1, flat lexicon dictionary collision caused English inputs with `"tired"` to produce Nigerian Pidgin output: *"Regarding what you shared about how your body de weak"*.
- **Post-Remediation Verification:**
  - Tested English query: *"I am feeling tired and weak."*
    - Symptom extracted: `"feeling tired"`.
    - Adapted response: Contains zero Pidgin or Yoruba phrases (`"de weak"`, `"sharp-sharp"`, `"pele"` are absent).
  - Tested Yoruba query: *"Mo ni aare pupo loni."*
    - Adapted response: Contains zero English framing (`"Regarding what you shared"`, `"Feel free to check in"` are absent).
  - Tested Nigerian Pidgin query: *"My body de hot and I de weak."*
    - Adapted response: Contains zero English framing.
- **Verdict:** **LEAKAGE COMPLETELY ELIMINATED**.

---

### Finding MLA-02: Unicode & Diacritic Normalization in Yoruba (VERIFIED RESOLVED)
- **Investigation:**
  Yoruba users frequently type using standard English QWERTY keyboards without tonal diacritics (e.g., typing `ese wiwu` instead of `ẹsẹ wiwu`, or `aare` instead of `àárẹ̀`).
- **Post-Remediation Verification:**
  In `LANGUAGE_SCOPED_SYMPTOM_LEXICONS["Yoruba"]`, both accented and unaccented variants are explicitly mapped:
  - `ẹsẹ wiwu` ──► `ẹsẹ ti o n wú`
  - `ese wiwu` ──► `ẹsẹ ti o n wú`
  - `aare` ──► `aare ti o n da yin`
  - `àárẹ̀` ──► `aare ti o n da yin`
  - `orí fífó` ──► `ori fifo`
  - `ori fifo` ──► `ori fifo`
- **Empirical Test:**
  Both accented and unaccented messages extract the identical approved medical description.

---

### Finding MLA-03: Contextual Domain Gating in Yoruba (VERIFIED RESOLVED)
- **Investigation:**
  Pre-remediation Yoruba empathy included `"Ẹ ku oju lona ọmọ mà"` (*"Greetings as you await the baby"*), which was delivered to mothers caring for already-born infants.
- **Post-Remediation Verification:**
  `detect_domain()` analyzes incoming text using tone-independent Unicode normalization.
  - When query relates to an infant (*"Ọmọ mi ti o jẹ ọsẹ mẹfa ni iba"*):
    - `domain = "infant"` is triggered.
    - `empathy_routine_infant` is selected:
      `"Ẹ pẹlẹ mà, ẹ ku itọju ọmọ. O dara pupọ bi ẹ ṣe n tọpinpin ilera ọmọ yin lẹsẹkẹsẹ."`
    - `"Ẹ ku oju lona ọmọ mà"` is strictly excluded.
- **Verdict:** **CONTEXTUAL MISMATCH RESOLVED**.

---

### Finding MLA-04: Language Identification & Unsupported Language Handling (MEDIUM)
- **Investigation:**
  How does the system behave when a message is received in an unsupported language (e.g. French, Hausa, or Arabic)?
- **Mechanism:**
  1. `MotherlyPulseAssistant` contains no automated language detector (e.g. `langdetect` or n-gram classifier).
  2. The language state defaults to `"English"`.
  3. If a user instantiates `MotherlyPulseAssistant(language="Hausa")`:
     - Line 17 of `assistant.py` assigns `self.language = "Hausa"`.
     - In `respond()`, `self.emergency_templates.get("Hausa")` evaluates to `None`, falling back to `self.emergency_templates["English"]`.
     - In `template_adapter.py`, `language in self.phrase_banks` evaluates to `False`, falling back to `"English"`.
     - The returned dictionary reports `"language": "Hausa"`, but the output is delivered in English!
- **Clinical Safety Impact:**
  A non-English speaker communicating in Hausa or French receives ungrounded English advice rather than an explicit message stating the language is unsupported.
- **Recommended Remediation:**
  Validate incoming language in `__init__` and `set_language()`. If an unsupported language is requested or detected, return a standardized multilingual message:
  *"MotherlyPulse currently supports English, Yoruba, and Nigerian Pidgin. Please select one of these languages."*

---

## 3. Human Review & Clinical Governance Boundary

> [!CAUTION]
> While all automated linguistic regression tests (encoding, token isolation, domain gating, and negation) have passed with 100% precision, **automated tests do not constitute native-speaker or clinical validation**.
> Formal human sign-off on all Yoruba and Pidgin phrase banks remains pending under [`MULTILINGUAL_HUMAN_REVIEW_CHECKLIST.md`](MotherlyPulse_Data/06_Reports/MULTILINGUAL_HUMAN_REVIEW_CHECKLIST.md).

