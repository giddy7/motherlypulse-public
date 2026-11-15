# PHASE 1.5.3 INDEPENDENT ACCEPTANCE AUDIT
**MotherlyPulse: Maternal & Infant Health Conversational Adaptation Engine**  
*Audit Date:* November 5, 2026  
*Auditor:* Independent Safety & Assurance Auditor (Antigravity Engineering Suite)  
*Status:* **CONDITIONAL REJECTION / SAFETY REMEDIATION REQUIRED**

---

## 1. Executive Summary & Verdict

This independent acceptance audit evaluated the Phase 1.5.2 critical safety remediation of MotherlyPulse. The implementation agent reported that all four vulnerabilities identified in Phase 1.5.1 were resolved and that the test suite achieved an 86/86 pass rate.

While significant engineering progress was made—specifically in isolating medication token omissions and structuring emergency bypass within `assistant.py`—**adversarial stress testing revealed that three of the four remediations are only PARTIALLY RESOLVED, and two critical new vulnerabilities were discovered.**

### Remediation Status Verdicts

| Vulnerability ID | Description | Claimed Status | Audit Verdict | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **VULN-01** | Unsupported-Language Emergency Downgrade | Fully Resolved | **PARTIALLY RESOLVED** | **CRITICAL** |
| **VULN-02** | Medication Instruction Omission | Fully Resolved | **VERIFIED RESOLVED** | **LOW** (Pass) |
| **VULN-03** | Dosage-to-Medication Association | Fully Resolved | **PARTIALLY RESOLVED** | **HIGH** |
| **VULN-04** | Word-Based Numerical Invariance | Fully Resolved | **PARTIALLY RESOLVED** | **HIGH** |

### Critical New Findings

1. **HTTP Gateway Emergency Blackout (VULN-01b):** While `assistant.py` correctly handles emergencies with unsupported language tags, `server.py` (lines 76–84) intercepts requests before calling `assistant.respond()` and returns HTTP 400 Bad Request if the `language` parameter is unsupported (e.g. `ha`, `de`, `fr`). Life-threatening obstetric emergencies submitted via HTTP with unsupported language parameters are completely blocked, and emergency contacts (112, ODEMSA) are never delivered.
2. **Compound Single-Clause Dosage Swapping Bypass (VULN-03b):** The clause splitter in `_get_medication_clauses()` fails to split compound sentences lacking explicit verbs after conjunctions (e.g., *"Take 500 mg paracetamol and 200 mg iron daily"*). Both medications are pooled into a single clause, allowing dosage swapping (*"Take 200 mg paracetamol and 500 mg iron daily"*) to bypass validation undetected (`is_valid = True`).
3. **Word-to-Digit False Positive Invariant Rejection (VULN-04b):** Step 3 of `ClinicalInvariantValidator.validate()` inspects un-normalized text against `FORBIDDEN_MEDICATION_TOKENS`. When reference contains number words (*"two tablets"*) and candidate adapts to digits (*"2 tablets"*), the candidate is falsely rejected with `ERR_INVENTED_MEDICATION`.
4. **Fraction Parsing 4x Overdose Error (VULN-04c):** `_extract_dosages()` does not parse fraction slashes. A prescription for `1/2 tablet` matches the `2` in `1/2` and is extracted as `2.0 tablet`, causing a 400% dosage calculation error.

---

## 2. Granular Audit of the Four Remediations

### A. Emergency Classification Independent of Language Support
- **Files Inspected:** [`motherlypulse_app/assistant.py`](motherlypulse_app/assistant.py#L156-L194), [`motherlypulse_app/classifier.py`](motherlypulse_app/classifier.py#L31-L91), [`motherlypulse_app/server.py`](motherlypulse_app/server.py#L69-L86)
- **Status:** **PARTIALLY RESOLVED**

#### Findings & Evidence
1. **Execution Order in `assistant.py`:**
   In `assistant.py` line 157, `self.classifier.classify(message, conversation_history)` is now executed before language gating.
   - For English, Yoruba, and Pidgin emergency messages, passing unsupported language codes (e.g. `language="de"`, `language=123`, `language=None`) correctly returns `urgency_category: "emergency"`, bypasses the template adapter, and attaches national (112) and state (ODEMSA: 112) contacts.
   - Non-emergency messages with unsupported languages correctly return `urgency_category: "unassessed"` with an informative limitation notice and referral to 112/local facilities.
2. **Classifier Language Scope Limitation:**
   `classifier.py` only contains regex patterns for English, Yoruba, and Nigerian Pidgin. It contains **zero patterns for Hausa, Igbo, French, Arabic, or other Nigerian minority languages**.
   - An emergency written in Hausa (e.g. *"Ina da zubar jini mai tsanani"* - severe bleeding) is NOT recognized by `classifier.py` and returns `routine`.
   - If `language="ha"` is specified, it returns `unassessed` (treating life-threatening hemorrhage as non-emergency unassessed).
   - If the language parameter is omitted, it defaults to English and returns `routine`!
3. **HTTP Server Blackout Bug:**
   In `motherlypulse_app/server.py` lines 76–84:
   ```python
   if clean_lang.lower() not in lang_mapping:
       self.send_response(400)
       self.send_header("Content-Type", "application/json; charset=utf-8")
       self.end_headers()
       err_payload = {"error": f"Unsupported language '{clean_lang}'."}
       self.wfile.write(json.dumps(err_payload).encode("utf-8"))
       return
   ```
   If a client POSTs an emergency with `language: "hausa"` or `language: "french"` to `/api/chat`, the HTTP server returns HTTP 400 Bad Request. `assistant.respond()` is never invoked, and the patient receives no emergency escalation.

---

### B. Medication Instruction Preservation
- **Files Inspected:** [`motherlypulse_app/template_adapter.py`](motherlypulse_app/template_adapter.py#L426-L525)
- **Status:** **VERIFIED RESOLVED**

#### Findings & Evidence
1. **Omission Detection:** `_get_medication_clauses()` identifies all active pharmaceuticals in `MEDICATION_AND_SUPPLEMENT_TOKENS`. If any reference medication token is missing from the candidate, validation fails immediately with `ERR_OMITTED_MEDICATION`.
2. **Unauthorized Addition:** Any candidate medication token not present in reference triggers `ERR_INVENTED_MEDICATION`.
3. **Prohibition & Polarity Retention:** `_verify_medication_polarity()` verifies that prohibition markers (*"do not take"*, *"avoid"*) are not stripped or inverted into permission markers (*"you can take"*).
4. **Dosage, Frequency, Duration Retention:** Specific extractors ensure that associated dosages, durations, and frequencies are not dropped.

---

### C. Dosage-to-Medication Association
- **Files Inspected:** [`motherlypulse_app/template_adapter.py`](motherlypulse_app/template_adapter.py#L393-L405), [`motherlypulse_app/template_adapter.py`](motherlypulse_app/template_adapter.py#L447-L507)
- **Status:** **PARTIALLY RESOLVED**

#### Findings & Evidence
1. **Multi-Clause Protection Works:**
   When sentences are separated by punctuation or conjunctions followed by action verbs (e.g. *"Take 500 mg paracetamol and take 200 mg iron"*), clauses are separated, and swapped dosages trigger `ERR_NUMERICAL_DOSAGE_MUTATED`.
2. **Single-Clause Compound Bypasses Association:**
   In `_get_medication_clauses()` line 398:
   ```python
   clauses = re.split(r'[.!\n;]|\b(?:and|while|also)\s+(?=[a-z\s]*\b(?:take|use|drink|administer|avoid|do\s+not)\b)', text)
   ```
   If the sentence is written without repeating the verb after "and" (e.g. *"Take 500 mg paracetamol and 200 mg iron daily"* or *"Take 500 mg paracetamol with 200 mg iron daily"*), `re.split` does not split the clause.
   - `ref_meds['paracetamol']` and `ref_meds['iron']` both receive the entire clause.
   - `_extract_dosages()` extracts `[(500.0, 'mg'), (200.0, 'mg')]` for both medications.
   - When candidate swaps the values (*"Take 200 mg paracetamol and 500 mg iron daily"*), the validator checks if each reference dosage is in the candidate list. Since both 500.0 and 200.0 are in the list, **validation passes with `(True, None)`!**

---

### D. Word-Based Numerical Invariance
- **Files Inspected:** [`motherlypulse_app/template_adapter.py`](motherlypulse_app/template_adapter.py#L272-L281), [`motherlypulse_app/template_adapter.py`](motherlypulse_app/template_adapter.py#L333-L375)
- **Status:** **PARTIALLY RESOLVED**

#### Findings & Evidence
1. **Basic Word-Number Normalization:**
   `WORD_TO_NUMBER` successfully normalizes English numbers 0–20, 24, 30, 40, 48 when adjacent to target units (days, weeks, tablets, etc.).
2. **Missing Essential Clinical Numbers:**
   `WORD_TO_NUMBER` stops at 20 (with a few exceptions). It does not include:
   - "fifty" (50)
   - "one hundred" (100)
   - "two hundred" (200)
   - "two hundred and fifty" (250)
   - "five hundred" (500)
   - "one thousand" (1000)
   References or candidates containing *"five hundred mg paracetamol"* fail normalization and trigger false `ERR_OMITTED_DOSAGE` rejections.
3. **Word-to-Digit Asymmetry:**
   When reference contains words (*"Take two tablets"*) and candidate contains digits (*"Take 2 tablets"*), Step 3 in `ClinicalInvariantValidator` evaluates un-normalized strings and falsely flags `"2 tablets"` as `ERR_INVENTED_MEDICATION`.
4. **Fraction Overdose Error:**
   `_extract_dosages('1/2 tablet')` returns `[(2.0, 'tablet')]` because the regex `\b(\d+(?:\.\d+)?)\s*tablet` matches the denominator.
5. **Absence of Indigenous Number Normalization:**
   Zero support for Yoruba (*ẹyọ meji*, *ọjọ mẹta*, *eemeji*) or Pidgin numerical words.

---

## 3. Analysis of the 86-Test Result

The reported 86/86 test pass rate was independently reproduced (`Ran 86 tests in 6.954s, OK`). However, critical inspection reveals why the suite failed to catch these defects:

1. **Symmetric Test Omission:** In `test_phase1_5_2_remediation.py`, `test_digit_and_word_unambiguous_equivalence_accepted` tested DIGIT in reference $\to$ WORD in candidate. The reciprocal case (WORD in reference $\to$ DIGIT in candidate) was never tested.
2. **Constructed Regex Accommodation:** In `test_swapped_dosages_between_two_medications_rejected`, the author explicitly wrote `"and take 200mg iron"`, providing the exact verb token required by their own clause splitter. They never tested compound clauses without the repeated verb.
3. **HTTP Server Isolation:** Existing server tests only tested supported languages (`en`, `yo`, `pcm`). No test ever sent an emergency with an unsupported language parameter to `server.py`.
4. **Fraction Absence:** No tests tested fractional numbers (`1/2`, `half`).

---

## 4. Required Corrective Recommendations

1. **HTTP Server (`server.py`):**
   Remove the premature language gate in `do_POST`. Delegate language handling to `self.assistant.respond()`. If an unsupported language is requested, allow `assistant.respond()` to return the emergency response or unassessed notice with HTTP 200 or structured 422.
2. **Clause Splitting (`template_adapter.py`):**
   Split clauses on commas and conjunctions (`and`, `with`, `plus`) regardless of following verbs, or associate dosages to medications by proximity (character distance or dependency parse).
3. **Un-Normalized Token Check (`template_adapter.py`):**
   In Step 3 of `validate()`, run `FORBIDDEN_MEDICATION_TOKENS` against normalized text (`cand_norm` and `ref_norm`), not raw text.
4. **Fraction & Numerical Scope Expansion:**
   Add fraction handling to `_extract_dosages()` and expand `WORD_TO_NUMBER` to include 50, 100, 200, 250, 500, 1000.
