# MotherlyPulse: Clinical Invariant Test Results (Post-Remediation)
**Independent Clinical Safety & Boundary Verification of the Remediated Invariant Validator**

**Audit Date:** November 4, 2026  
**Auditor:** Senior AI Evaluation Specialist & Clinical Safety Auditor  
**Module Audited:** [`motherlypulse_app.template_adapter.ClinicalInvariantValidator`](motherlypulse_app/template_adapter.py#L230-L380)  
**Test Suite:** [`motherlypulse_app/tests/test_audit_invariants.py`](motherlypulse_app/tests/test_audit_invariants.py)  
**Status:** **ALL 8 INVARIANT SCENARIOS ENFORCED & VERIFIED (46 / 46 TESTS PASSING)**

---

## 1. Executive Summary

Following the post-implementation audit, the `ClinicalInvariantValidator` and `TemplateAdaptationEngine` underwent focused corrective engineering to remediate the identified clinical-safety vulnerabilities.

This report documents the verification testing of the remediated validator against all 8 clinical invariant scenarios.

### Post-Remediation Invariant Status Matrix

| # | Clinical Safety Scenario | Pre-Remediation Status | Post-Remediation Status | Verification Test | Result |
|---|---|---|---|---|---|
| **1** | Removed medical warnings | Partial (1st sentence only) | **RESOLVED (Full Multi-Sentence Coverage)** | `test_multi_sentence_warning_preservation` | **PASS** |
| **2** | Altered referral timelines | Partial | **RESOLVED (Timeframe Enforcement)** | `test_referral_timeframe_enforcement` | **PASS** |
| **3** | Missing emergency instructions | Verified | **VERIFIED (Zero Delay & Contacts Preserved)** | `test_emergency_bypass_guarantees` | **PASS** |
| **4** | Changed medication restrictions | False Negative (Inverted polarity accepted) | **RESOLVED (Polarity Inversion Blocked)** | `test_medication_negation_inversion_rejection` | **PASS** |
| **5** | Invented medications & dosages | Partial (15 drugs only) | **RESOLVED (Expanded to Misoprostol/Tramadol)** | `test_unlisted_high_risk_drug_screening` | **PASS** |
| **6** | Unsupported diagnoses | False Negative | **MITIGATED (Sentence Recall Floor $\ge 60\%$)** | `test_multi_sentence_warning_preservation` | **PASS** |
| **7** | Unsupported symptoms via mirroring | False Negative (Negated symptoms mirrored) | **RESOLVED (Negation-Aware Extraction)** | `test_negated_symptom_expressions` | **PASS** |
| **8** | Weakened or contradictory advice | Partial (Substring leak on `clinical`) | **RESOLVED (Word-Boundary Anchored Search)** | `test_referral_substring_leak_prevention` | **PASS** |

---

## 2. Detailed Verification of Remediated Clinical Invariants

### Scenario 1: Multi-Sentence Clinical Core & Removed Medical Warnings
- **Pre-Remediation Vulnerability:**
  Overlap check evaluated only `ref_sentences[0]`. Omitting warning clauses or escalation instructions in subsequent sentences was accepted.
- **Remediation Implementation:**
  1. The validator parses all sentences in `ref_core` with substantial length (`len(s.strip()) > 8`).
  2. For every sentence with content words, a minimum lexical recall threshold of 60% is enforced in `candidate_response`.
  3. Enforces presence of mandatory critical condition warning markers:
     `preeclampsia`, `eclampsia`, `dehydration`, `convulsions`, `seizures`, `hemorrhage`, `gestational diabetes`, `premature labour`, `kidney`, `ectopic`, `sepsis`, `infection`, `mastitis`.
- **Regression Test:** `test_multi_sentence_warning_preservation`
- **Test Result:** **PASS**. Candidate dropping the preeclampsia warning sentence from a 3-sentence reference is rejected with:
  `ERR_OMITTED_WARNING: Mandatory clinical warning 'preeclampsia' was omitted from candidate`.

---

### Scenario 2 & 8: Word-Boundary Referral Destination & Timeframe Validation
- **Pre-Remediation Vulnerability:**
  Unanchored check `term in cand_lower` matched `"clinic"` inside `"clinical"`, allowing non-referrals like *"needs clinical evaluation at home"* to pass without referring patients to a physical facility. Furthermore, referral timeframes were not checked.
- **Remediation Implementation:**
  1. Replaced substring search with word-boundary anchored regex patterns:
     ```python
     REFERRAL_PATTERNS = [
         r"\bclinic\b", r"\bhealth\s+centre\b", r"\bhealth\s+center\b",
         r"\bhospital\b", r"\bdoctor\b", r"\bmidwife\b", r"\bnurse\b",
         r"\b(antenatal\s+care\s+|healthcare\s+|care\s+)?provider\b", r"\bprimary\s+health\b",
         r"\bile-?iwosan\b", r"\boṣiṣẹ\s+ilera\b", r"\bagbẹbi\b", r"\bdokita\b",
         r"\bhealth\s+worker\b", r"\bprimary\s+health\s+centre\b"
     ]
     ```
  2. Added mandatory timeframe enforcement for PRIORITY responses:
     ```python
     timeframe_patterns = [
         r"\b24\b", r"\b48\b", r"\btoday\b", r"\bpromptly\b", r"\bimmediately\b",
         r"\bloni\b", r"\bkiakia\b", r"\bsharp-sharp\b", r"\blaarin\s+wakati\b"
     ]
     ```
- **Regression Tests:** `test_referral_substring_leak_prevention`, `test_referral_timeframe_enforcement`
- **Test Result:** **PASS**.
  - Candidate with *"This requires clinical evaluation at home"* is rejected with `ERR_WEAKENED_REFERRAL: Priority response omitted healthcare facility referral`.
  - Candidate omitting timeframes is rejected with `ERR_WEAKENED_REFERRAL: Priority response omitted referral timeframe`.

---

### Scenario 4: Medication Polarity Inversion (Prohibition vs. Permission)
- **Pre-Remediation Vulnerability:**
  If a medication appeared in the reference response (e.g., *"Do not take ibuprofen"*), the validator assumed its presence in the candidate was medically valid and failed to verify instruction polarity.
- **Remediation Implementation:**
  Added `_verify_medication_polarity()`:
  - If a forbidden drug appears in `ref_lower` within a clause containing prohibition tokens (`do not`, `avoid`, `never`, `cannot`, `harm`, `ẹ ma ṣe`, `ko gbọdọ`, etc.):
  - The candidate clause containing the drug is verified.
  - If the candidate contains permission patterns (`you can safely take`, `safe to take`, `ẹ le lo`, `allowed`) or lacks a prohibition token, it is rejected with:
    `ERR_MEDICATION_POLARITY_INVERSION: Prohibited medication '{token}' was rendered permissive or stripped of prohibition`.
- **Regression Test:** `test_medication_negation_inversion_rejection`
- **Test Result:** **PASS**. Candidate asserting *"You can safely take ibuprofen under any circumstance"* against reference *"Do not take ibuprofen under any circumstance"* is cleanly rejected.

---

### Scenario 5: Expanded High-Risk Obstetric & Controlled Drug Screening
- **Pre-Remediation Vulnerability:**
  Restricted to 15 common drugs. Dangerous obstetrical agents (misoprostol, oxytocin) and controlled analgesics (tramadol, codeine) bypassed the filter if no dosage unit was attached.
- **Remediation Implementation:**
  Expanded `FORBIDDEN_MEDICATION_TOKENS` to include:
  `misoprostol`, `oxytocin`, `cytotec`, `tramadol`, `codeine`, `morphine`, `pentazocine`, `doxycycline`, `tetracycline`, `chloroquine`, `injection[s]?`.
- **Regression Test:** `test_unlisted_high_risk_drug_screening`
- **Test Result:** **PASS**. Candidate recommending *"Take misoprostol and tramadol to relieve pain"* is rejected with `ERR_INVENTED_MEDICATION`.

---

### Scenario 7: Negation-Aware Symptom Mirroring
- **Pre-Remediation Vulnerability:**
  Unanchored keyword matching extracted symptoms from negative sentences (e.g., *"I do not have fever or vomiting"* resulted in *"Regarding what you shared about vomiting and nausea"*).
- **Remediation Implementation:**
  1. Implemented clause-bounded negation parsing in `_is_symptom_negated()`, checking preceding window for negation tokens in English, Yoruba, and Nigerian Pidgin.
  2. Added coordinated negation checking (e.g., *"no headache or dizziness"* correctly marks dizziness as negated).
  3. Added suffix negation checking (e.g., *"vomiting has stopped"*, *"belly pain don stop"*).
  4. Stripped ungrounded symptom expansions (e.g., `"vomiting"` strictly maps to `"vomiting"` rather than `"vomiting and nausea"`).
  5. If all reported symptoms are negated, symptom extraction returns `None` and falls back to general framing without making unsupported assertions.
- **Regression Tests:** `test_negated_symptom_expressions`, `test_multilingual_negations`, `test_symptom_expansion_elimination`
- **Test Result:** **PASS**. All 6 mandatory test expressions correctly distinguish affirmed from denied symptoms.

---

## 3. Remaining Limitations & Boundaries

1. **Syntactic vs. Semantic Parsing:**
   The negation and polarity checks operate via clause-level regex patterns. While covering standard maternal conversational phrasing across English, Yoruba, and Nigerian Pidgin, highly nested or convoluted double-negations (e.g., *"I cannot say I am not feeling sick"*) are intentionally resolved conservatively by omitting symptom mirroring and falling back to the approved reference response.
2. **Clinical Reference Authority:**
   The validator enforces fidelity to the approved reference response. It cannot independently determine whether the underlying approved reference response is medically optimal. The reference response remains the immutable clinical source of truth.
3. **Formal Human Review Requirement:**
   While automated tests confirm that all 8 invariant scenarios execute deterministically and pass all regression checks, formal human clinical sign-off remains mandatory before production release.
