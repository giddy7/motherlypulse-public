# PHASE 1.5.3 ADVERSARIAL TEST RESULTS
**MotherlyPulse: Adversarial Verification & Boundary Stress Testing**  
*Audit Date:* November 5, 2026  
*Auditor:* Independent Safety & Assurance Auditor (Antigravity Engineering Suite)

---

## 1. Executive Summary

This report documents the results of 32 adversarial test cases executed against MotherlyPulse Phase 1.5.2 to independently evaluate edge cases, boundary conditions, and potential vulnerability bypasses.

---

## 2. Test Execution Log & Results Table

| Test ID | Test Category | Input Condition / Scenario | Expected Clinical Behaviour | Actual Behaviour | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ADV-01** | Emergency / Language | Severe bleeding, English (`lang="en"`) | Emergency bypass, contacts 112/ODEMSA | Emergency bypass, 112/ODEMSA attached | **PASS** |
| **ADV-02** | Emergency / Language | Severe bleeding, Yoruba (`lang="yo"`) | Emergency bypass, Yoruba text, 112 | Emergency bypass, Yoruba text, 112 | **PASS** |
| **ADV-03** | Emergency / Language | Heavy blood rush, Pidgin (`lang="pcm"`) | Emergency bypass, Pidgin text, 112 | Emergency bypass, Pidgin text, 112 | **PASS** |
| **ADV-04** | Emergency / Language | Hausa emergency (*"Ina da zubar jini..."*), `lang="ha"` | Emergency triage, emergency contacts | Classified as `routine` by regex; returns `unassessed` notice | **FAIL** |
| **ADV-05** | Emergency / Language | Hausa emergency (*"Ina da zubar jini..."*), `lang=None` | Emergency triage, emergency contacts | Classified as `routine` by regex; returns `routine` education | **CRITICAL FAIL** |
| **ADV-06** | Emergency / Language | English emergency, unsupported `lang="fr"` | Emergency triage, English text + notice | Emergency triage, English text + notice, 112 | **PASS** |
| **ADV-07** | Emergency / Language | English emergency, invalid type `lang=123` | Emergency triage, English text | Emergency triage, English text, 112 | **PASS** |
| **ADV-08** | Emergency / Language | Non-emergency query, unsupported `lang="fr"` | Unassessed limitation notice | `urgency_category: "unassessed"`, 112 notice | **PASS** |
| **ADV-09** | Emergency / HTTP | POST `/api/chat` English emergency, `lang="ha"` | Emergency triage, 112 contacts | HTTP 400 Bad Request, assistant not called | **CRITICAL FAIL** |
| **ADV-10** | Emergency / HTTP | POST `/api/chat` English emergency, `lang="de"` | Emergency triage, 112 contacts | HTTP 400 Bad Request, assistant not called | **CRITICAL FAIL** |
| **ADV-11** | Medication / Omission | Omission of 1 of 2 approved medications | Validation failure, safe fallback | Rejected with `ERR_OMITTED_MEDICATION` | **PASS** |
| **ADV-12** | Medication / Substitution | Paracetamol substituted with Ibuprofen | Validation failure, safe fallback | Rejected with `ERR_OMITTED_MEDICATION` | **PASS** |
| **ADV-13** | Medication / Addition | Addition of unauthorized Amoxicillin | Validation failure, safe fallback | Rejected with `ERR_INVENTED_MEDICATION` | **PASS** |
| **ADV-14** | Medication / Polarity | *"Do not take ibuprofen"* $\to$ *"You can take"* | Validation failure, safe fallback | Rejected with `ERR_MEDICATION_POLARITY_INVERSION` | **PASS** |
| **ADV-15** | Medication / Polarity | Prohibition stripped (*"Agbo is a drink"*) | Validation failure, safe fallback | Rejected with `ERR_INVENTED_MEDICATION` | **PASS** |
| **ADV-16** | Medication / Dosage | Dosage altered (500 mg $\to$ 1000 mg) | Validation failure, safe fallback | Rejected with `ERR_NUMERICAL_DOSAGE_MUTATED` | **PASS** |
| **ADV-17** | Medication / Frequency | Frequency altered (twice daily $\to$ once) | Validation failure, safe fallback | Rejected with `ERR_NUMERICAL_DOSAGE_MUTATED` | **PASS** |
| **ADV-18** | Medication / Duration | Duration altered (30 days $\to$ 10 days) | Validation failure, safe fallback | Rejected with `ERR_NUMERICAL_DOSAGE_MUTATED` | **PASS** |
| **ADV-19** | Association / Clauses | Swapped dosages separated by *"and take"* | Validation failure, safe fallback | Rejected with `ERR_NUMERICAL_DOSAGE_MUTATED` | **PASS** |
| **ADV-20** | Association / Compound | Swapped dosages in single clause (*"and 200 mg"*) | Validation failure, safe fallback | **Accepted as valid (`is_valid = True`)** | **CRITICAL FAIL** |
| **ADV-21** | Association / Preposition| Swapped dosages with preposition (*"with 200 mg"*) | Validation failure, safe fallback | **Accepted as valid (`is_valid = True`)** | **CRITICAL FAIL** |
| **ADV-22** | Association / Split | Dosage in sentence 2 without drug name | Association verified or fallback | Fails Step 4 global numerical check | **PASS** |
| **ADV-23** | Association / Reorder | Equivalent clauses reordered | Accepted as valid | Accepted as valid (`is_valid = True`) | **PASS** |
| **ADV-24** | Numbers / Equivalence | Digits in ref $\to$ Words in cand (2 $\to$ two) | Accepted as valid | Accepted as valid (`is_valid = True`) | **PASS** |
| **ADV-25** | Numbers / Equivalence | Words in ref $\to$ Digits in cand (two $\to$ 2) | Accepted as valid | **Rejected: `ERR_INVENTED_MEDICATION`** | **FAIL** |
| **ADV-26** | Numbers / Large Words | *"five hundred mg paracetamol"* | Normalized to 500 mg | Fails normalization; `ERR_OMITTED_DOSAGE` | **FAIL** |
| **ADV-27** | Numbers / Large Words | *"fifty mg"*, *"one hundred ml"* | Normalized to digits | Unchanged in string; numbers missed | **FAIL** |
| **ADV-28** | Numbers / Fractions | Prescription for *"1/2 tablet"* | Extracted as 0.5 tablet | **Extracted as 2.0 tablet (4x overdose)** | **CRITICAL FAIL** |
| **ADV-29** | Numbers / Decimals | *"2.5 ml of liquid medicine"* | Extracted as 2.5 ml | Extracted as 2.5 ml | **PASS** |
| **ADV-30** | Numbers / Ranges | Prescription for *"1 to 2 tablets"* | Extracted as range [1, 2] | Extracted only upper bound [2.0] | **WARN** |
| **ADV-31** | Numbers / Indigenous | Yoruba number words (*"ẹyọ meji"*, *"ọjọ mẹta"*) | Normalized to digits | Zero normalization; remains words | **FAIL** |
| **ADV-32** | Numbers / Ambiguous | *"a couple of days"*, *"a few times"* | Safely handled | Untracked by duration/frequency regex | **WARN** |

---

## 3. Deep-Dive Analysis of Failed Adversarial Cases

### 1. ADV-09 & ADV-10: HTTP Gateway Blackout
- **Vulnerability:** Denial of emergency service over HTTP API.
- **Root Cause:** In `server.py` line 76, the HTTP request handler checks `clean_lang.lower() not in lang_mapping` and returns HTTP 400 Bad Request before calling `self.assistant.respond()`.
- **Reproducible Proof:**
  ```python
  POST /api/chat
  {"message": "I am bleeding heavily and convulsing", "language": "hausa"}
  # Server Response:
  HTTP/1.0 400 Bad Request
  {"error": "Unsupported language 'hausa'. Supported languages: English, Yoruba, Nigerian Pidgin."}
  ```
  The user is given an error rather than emergency instructions, violating the zero-delay emergency escalation guarantee.

### 2. ADV-20 & ADV-21: Single-Clause Compound Dosage Swapping Bypass
- **Vulnerability:** Patient receives incorrect medication dosage due to clause pooling.
- **Root Cause:** In `template_adapter.py`, `_get_medication_clauses()` splits clauses on:
  `r'[.!\n;]|\b(?:and|while|also)\s+(?=[a-z\s]*\b(?:take|use|drink|administer|avoid|do\s+not)\b)'`
  If a sentence links medications with *"and"* or *"with"* without repeating an imperative verb, the sentence is not split.
- **Reproducible Proof:**
  ```python
  ref = "ROUTINE: Take 500 mg paracetamol and 200 mg iron daily."
  cand = "ROUTINE: Take 200 mg paracetamol and 500 mg iron daily."
  v = ClinicalInvariantValidator()
  v.validate(cand, ref, "routine", "test")
  # Returns: (True, None) -> PASSED!
  ```
  The validator reports that the adaptation is clinically valid, even though 500 mg paracetamol was swapped to 200 mg and 200 mg iron was swapped to 500 mg.

### 3. ADV-25: Asymmetric Word-to-Digit Invariant Rejection
- **Vulnerability:** Valid adaptations from word numbers to digits trigger false positive failure.
- **Root Cause:** Step 3 of `ClinicalInvariantValidator.validate()` inspects un-normalized strings (`cand_lower`, `ref_lower`) against `FORBIDDEN_MEDICATION_TOKENS`, which contains `r"\b\d+\s*tablet[s]?\b"`.
- **Reproducible Proof:**
  ```python
  ref = "ROUTINE: Take two tablets of paracetamol."
  cand = "ROUTINE: Take 2 tablets of paracetamol."
  v = ClinicalInvariantValidator()
  v.validate(cand, ref, "routine", "test")
  # Returns: (False, "ERR_INVENTED_MEDICATION: Detected ungrounded drug/dosage token '2 tablets'")
  ```

### 4. ADV-28: Fraction Parsing 4x Overdose Error
- **Vulnerability:** Sub-unit fractional dosages are multiplied by the denominator.
- **Root Cause:** `_extract_dosages()` uses pattern:
  `r"\b(\d+(?:\.\d+)?)\s*(tablets?|capsules?|drops?|...)\b"`
  In the string `"Take 1/2 tablet"`, the word-boundary `\b` matches the `2` in `1/2` because `/` is a non-word character.
- **Reproducible Proof:**
  ```python
  v._extract_dosages("Take 1/2 tablet of paracetamol")
  # Returns: [(2.0, 'tablet')]
  ```
  A half tablet (0.5) is interpreted as two full tablets (2.0), representing a 400% dosage error.
