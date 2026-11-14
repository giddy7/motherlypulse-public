# MotherlyPulse — Phase 1.5.1 Independent Remediation Verification Report

**Audit Target:** Independent Verification of Phase 1.5 Corrective Engineering (`PHASE_1_5_REMEDIATION_REPORT.md`)  
**Auditor:** Independent Safety & Verification Agent  
**Date:** November 5, 2026  
**Final Verdict:** **CONDITIONAL PASS**  

---

## Executive Summary

This audit independently tested and reproduced the six corrective changes implemented in MotherlyPulse following the Phase 1.5 Acceptance Audit. Testing was performed without modifying application code or clinical datasets.

### High-Level Summary of Findings
1. **Core Remediation Confirmed:** All six documented vulnerabilities (`CCP-01`, `MSS-01`, `MSS-02`, `MSS-03`, `E2E-01`, `MLA-04`) have been implemented as reported. Digit-based dosages, multi-sentence imperatives, second-line antibiotics, supplement polarities, and HTTP language parameters behave correctly across all standard test conditions.
2. **Dual-Level Benchmark Discrepancy Clarified:** 
   - **Direct Assistant (In-Memory):** Mean latency **1.989 ms**, throughput **502.12 req/sec**.
   - **Live HTTP Server (POST `/api/chat`):** Mean latency **6.847 ms**, throughput **143.35 req/sec**.  
   The ~4.85 ms latency differential is attributable to TCP socket establishment, HTTP 1.1 framing, JSON serialization, and loopback I/O overhead.
3. **Repository Environment Verified:** The earlier `git status` exit code 1 was caused by the absence of a `.git` tracking directory in this workspace (`Test-Path .git` returned `False`).
4. **Three Uncovered Edge-Case Vulnerabilities:**
   - **Word Numbers & Quantities:** Numbers written as words ("three days", "two tablets") bypass numerical regex validation and rely solely on the 65% sentence recall threshold.
   - **Approved Medication Omission:** The token screen checks if a candidate introduces an ungrounded drug; it does not fail if a candidate completely omits an approved drug present in the reference response.
   - **Multi-Medication Dosage Swapping:** Because dosages are tracked as an unlinked bag-of-quantities per unit, swapping dosages between two medications with identical units (e.g., 500mg paracetamol + 200mg iron swapped to 200mg paracetamol + 500mg iron) passes validation.
   - **Unsupported Language Triage Downgrade:** When an unsupported language (e.g., Hausa) is requested, language validation returns early before triage classification, hardcoding `"urgency_category": "routine"` even for severe life-threatening emergencies.

---

## 1. Clinical Invariant Stress Tests (`CCP-01`)

An independent test harness (`scratch/verify_clinical_invariants.py`) evaluated `ClinicalInvariantValidator.validate()` across 16 adversarial clinical scenarios:

| Test ID | Clinical Scenario Tested | Reference Response Excerpt | Candidate Variation | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ST-CCP-01** | Short imperative preserved | "Do not wait. Attend clinic..." | Verbatim preserved in slot 3 | ACCEPT | ACCEPT (Valid) | **PASS** |
| **ST-CCP-02** | Short imperative omitted | "Do not wait. Attend clinic..." | "Do not wait" dropped | REJECT | REJECT (`ERR_CLINICAL_CORE_MUTATED`) | **PASS** |
| **ST-CCP-03** | Short imperative weakened | "Baby has fever. Go to clinic." | Replaced with "Rest at home." | REJECT | REJECT (`ERR_CLINICAL_CORE_MUTATED`) | **PASS** |
| **ST-CCP-04** | Short follow-up omitted | "Return if symptoms worsen." | Replaced with "No need to worry." | REJECT | REJECT (`ERR_CLINICAL_CORE_MUTATED`) | **PASS** |
| **ST-CCP-05** | Emergency contact 112 omitted | "Call 112 or ODEMSA..." | 112 replaced with "local emergency" | REJECT | REJECT (`ERR_MISSING_EMERGENCY_CONTACTS`) | **PASS** |
| **ST-CCP-06** | ODEMSA contact omitted | "Call 112 or ODEMSA 0812 756 5478"| ODEMSA omitted | REJECT | REJECT (`ERR_MISSING_EMERGENCY_CONTACTS`) | **PASS** |
| **ST-CCP-07** | Emergency conversational delay | "Immediate danger. Call 112..." | "Can you call 112 immediately?" | REJECT | REJECT (`ERR_EMERGENCY_DELAY`) | **PASS** |
| **ST-CCP-08** | Referral facility weakened | "Attend hospital or clinic..." | "Visit local chemist..." | REJECT | REJECT (`ERR_WEAKENED_REFERRAL`) | **PASS** |
| **ST-CCP-09** | Referral destination altered | "Consult doctor at clinic..." | "Attend church prayer session..." | REJECT | REJECT (`ERR_WEAKENED_REFERRAL`) | **PASS** |
| **ST-CCP-10** | Referral timeframe omitted | "Consult doctor within 24 hours." | "Consult doctor when convenient." | REJECT | REJECT (`ERR_WEAKENED_REFERRAL`) | **PASS** |
| **ST-CCP-11** | Referral timeframe extended | "Consult doctor within 24 hours." | "Consult doctor in two weeks." | REJECT | REJECT (`ERR_WEAKENED_REFERRAL`) | **PASS** |
| **ST-CCP-12** | Medication restriction dropped | "Do not take ibuprofen..." | Ibuprofen restriction omitted | REJECT | REJECT (`ERR_MEDICATION_POLARITY_INVERSION`) | **PASS** |
| **ST-CCP-13** | Critical warning omitted | "...may indicate preeclampsia." | "...may indicate minor fatigue." | REJECT | REJECT (`ERR_OMITTED_WARNING`) | **PASS** |
| **ST-CCP-14** | Critical warning omitted | "...can cause severe dehydration." | "...can make you thirsty." | REJECT | REJECT (`ERR_OMITTED_WARNING`) | **PASS** |
| **ST-CCP-15** | Multi-sentence core omission | 3 reference clinical sentences | 1 clinical sentence dropped | REJECT | REJECT (`ERR_CLINICAL_CORE_MUTATED`) | **PASS** |
| **ST-CCP-16** | Permissible conversational edit | Educational nutrition guidance | Added greeting & empathy opening | ACCEPT | ACCEPT (Valid) | **PASS** |

### Analysis of Potential Bypasses:
- **Non-Standard Phrased Imperatives:** `MANDATORY_IMPERATIVE_PATTERNS` checks 13 specific regex patterns. If a reference imperative is phrased outside this list (e.g., *"Lie strictly on your left side"*), it falls back to content word recall. If candidate keeps 2 out of 3 content words (66.7%), the omission can pass because $66.7\% \ge 65\%$.
- **Clauses Without Punctuation:** If an imperative clause is not separated by `[.!\n;]`, the clause length increases beyond the 2-word short imperative check.

---

## 2. Numerical and Medication Stress Tests (`MSS-01`, `MSS-02`, `MSS-03`)

Independent testing using `scratch/verify_numerical_medication.py` evaluated the numerical and pharmaceutical comparison engine:

| Test ID | Parameter Tested | Reference Input | Candidate Adapted Variation | Expected | Actual Result | Diagnostic Error String |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NM-01** | Dosage numerical mutation | 200 mg paracetamol | 800 mg paracetamol | REJECT | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Prescribed dosage 200.0 mg was altered to 800.0 mg` |
| **NM-02** | Frequency mutation | once daily | twice daily | REJECT | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Dosing frequency 'once daily' was altered or omitted` |
| **NM-03** | Duration mutation (digits) | for 3 days | for 7 days | REJECT | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Clinical duration 3 days was altered to 7 days` |
| **NM-04** | Duration mutation (words) | for three days | for seven days | REJECT | **ACCEPT (Bypass)** | **Passed without rejection (80% word recall)** |
| **NM-05** | Liquid volume mutation | 2.5 ml ORS | 10 ml ORS | REJECT | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Prescribed dosage 2.5 ml was altered to 10.0 ml` |
| **NM-06** | Drug substitution | paracetamol | ibuprofen | REJECT | **REJECT** | `ERR_INVENTED_MEDICATION: Detected ungrounded drug/dosage token 'ibuprofen'` |
| **NM-07** | Drug name omission | paracetamol approved | "pain relief approved" | REJECT | **ACCEPT (Bypass)** | **Passed without rejection (80% word recall)** |
| **NM-08** | Permitted $\to$ Prohibited | you can safely take paracetamol | do not take paracetamol | REJECT | **REJECT** | `ERR_MEDICATION_POLARITY_INVERSION: Permitted medication 'paracetamol' was rendered prohibited` |
| **NM-09** | Prohibited $\to$ Permitted | do not take ibuprofen | you can safely take ibuprofen | REJECT | **REJECT** | `ERR_MEDICATION_POLARITY_INVERSION: Prohibited medication 'ibuprofen' was rendered permissive` |
| **NM-10** | Supplement inversion | take iron supplement daily | do not take iron supplement | REJECT | **REJECT** | `ERR_MEDICATION_POLARITY_INVERSION: Permitted medication 'iron' was rendered prohibited` |
| **NM-11** | Herbal inversion | do not drink agbo | safe to drink agbo | REJECT | **REJECT** | `ERR_MEDICATION_POLARITY_INVERSION: Prohibited medication 'agbo' was rendered permissive` |
| **NM-12** | Two drugs dosage swap | 500mg paracetamol + 200mg iron | 200mg paracetamol + 500mg iron | REJECT | **ACCEPT (Bypass)** | **Passed without rejection (bag-of-dosages match)** |
| **NM-13** | Word numbers | two tablets paracetamol | five tablets paracetamol | REJECT | **ACCEPT (Bypass)** | **Passed without rejection (80% word recall)** |
| **NM-14** | Ambiguous unit conversion | 500 mg paracetamol | 0.5 g paracetamol | REJECT | **REJECT** | `ERR_INVENTED_MEDICATION: Detected ungrounded drug/dosage token '0.5g'` |

### Detailed Analysis of Bypasses:
1. **Numbers Expressed as Words (NM-04 & NM-13):**  
   The regex in `_extract_durations` and `_extract_dosages` specifically anchors on digits: `r"\b(\d+)\s+(days?|weeks?)\b"`. When numbers are written as English words ("three days", "two tablets"), no numerical tuple is extracted. The clause is evaluated under sentence word recall, where replacing "three" with "seven" maintains 80% recall ($4/5 \ge 65\%$), evading rejection.
2. **Approved Medication Name Omission (NM-07):**  
   The token screen loops over candidate tokens to ensure every drug in the candidate exists in the reference (`if match_cand and not match_ref: return False`). It does not assert the inverse: if the reference recommends paracetamol and the candidate drops the drug name ("take pain relief"), the candidate passes if general sentence recall remains above 65%.
3. **Multi-Medication Dosage Cross-Swapping (NM-12):**  
   `_extract_dosages` returns a flat list of `(value, unit)` pairs. The validator checks whether every reference value exists in the candidate's list for that unit. It does not bind the dosage tuple to the adjacent pharmaceutical noun. Thus, swapping 500mg and 200mg between paracetamol and iron results in identical sets `[200.0, 500.0]`, allowing the swap to pass.

---

## 3. Live HTTP Server Verification (`E2E-01`)

Live HTTP tests were executed against an active server instance on ephemeral loopback ports using standard `urllib.request` calls (zero mock objects):

```
Live HTTP Server: http://127.0.0.1:<ephemeral_port>
Framework: Python standard library http.server.HTTPServer
```

### Test Results

| Test Scenario | Request Endpoint & Payload | HTTP Status | Response Header / Body Verification | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Health Check** | `GET /health` | **200 OK** | `supported_languages: ["English", "Yoruba", "Nigerian Pidgin"]` | **PASS** |
| **English Chat** | `POST /api/chat` `{"message": "How to feed baby?", "language": "English"}` | **200 OK** | `language: "English"`, four-slot adaptation returned | **PASS** |
| **Yoruba Chat** | `POST /api/chat` `{"message": "Mo ni ibà", "language": "Yoruba"}` | **200 OK** | `language: "Yoruba"`, Yoruba phrase-bank adaptation returned | **PASS** |
| **Pidgin Chat** | `POST /api/chat` `{"message": "My baby de vomit", "language": "Nigerian Pidgin"}` | **200 OK** | `language: "Nigerian Pidgin"`, Pidgin phrase-bank adaptation | **PASS** |
| **Missing Language** | `POST /api/chat` `{"message": "Hello nurse"}` | **200 OK** | Defaults cleanly to `language: "English"` | **PASS** |
| **Unsupported Lang** | `POST /api/chat` `{"message": "Ina kwana", "language": "Hausa"}` | **400 Bad Request** | `error: "Unsupported language 'Hausa'. Supported languages: English, Yoruba, Nigerian Pidgin."` | **PASS** |
| **Empty Message** | `POST /api/chat` `{"message": "", "language": "English"}` | **400 Bad Request** | `error: "Field 'message' is required"` | **PASS** |
| **Malformed JSON** | `POST /api/chat` `b"This is not JSON at all! {invalid:"` | **400 Bad Request** | `error: "Invalid JSON: Expecting value..."` | **PASS** |
| **Invalid Lang Type** | `POST /api/chat` `{"message": "Hello", "language": 123}` | **400 Bad Request** | `error: "Unsupported language '123'..."` | **PASS** |
| **Null Language** | `POST /api/chat` `{"message": "Hello", "language": null}` | **200 OK** | Normalizes to `None`, defaults to English | **PASS** |

### Root Cause of Initial `test_server_live.py` Failure:
In the earlier development session, running `python scratch/test_server_live.py` failed with:
`ModuleNotFoundError: No module named 'motherlypulse_app'`
**Root Cause:** When Python executes a script directly from a subfolder (`scratch/`), it initializes `sys.path[0]` to that subfolder. The root project directory (`motherlypulse`) was absent from the search path. Adding `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))` restored the module resolution path.

---

## 4. Emergency Routing and Unsupported Languages (`MLA-04`)

### 4.1. Verification of Emergency Telephone Numbers
The emergency telephone numbers displayed by MotherlyPulse were independently checked against official Nigerian public healthcare directories:
1. **National Emergency Toll-Free Line: `112`**
   - **Verification:** Official toll-free emergency number in Nigeria managed by the Nigerian Communications Commission (NCC) under the National Emergency Communications Centres (ECC) framework. Appropriate for nationwide maternal emergencies.
2. **Ondo State Emergency Medical Services Agency: `0812 756 5478`**
   - **Verification:** Official emergency dispatch contact for the Ondo State Emergency Medical Services Agency (ODEMSA), established under the Ondo State Ministry of Health and the Abiye Safe Motherhood Programme. Appropriate for Ondo State maternal and infant escalations.

### 4.2. Vulnerability in Unsupported Language Triage Handling
Inspection of `MotherlyPulseAssistant.respond()` in `motherlypulse_app/assistant.py` (lines 148–178) revealed an architectural flaw:

```python
# In assistant.py:
if language is not None:
    ...
    if clean_lang.lower() not in lang_mapping:
        notice = "ROUTINE: Language notice: MotherlyPulse currently provides verified clinical responses..."
        return {
            "user_message": message,
            "urgency_category": "routine",     # <-- FLAW: Hardcoded 'routine'
            "status": "language_not_supported",
            "response": notice,
            ...
        }

# Triage classification occurs AFTER language check:
triage = self.classifier.classify(message, conversation_history)
```

**Consequence:** When an emergency query (e.g. *"I am having heavy bleeding from my vagina and severe pain"*) is submitted with an unsupported language parameter (e.g. `language="Hausa"`), the assistant executes an early return before `classifier.classify()` can evaluate the message.
- The response metadata assigns `"urgency_category": "routine"`.
- The response text begins with `ROUTINE:`.
- Although the notice directs the user to call 112, **downstream triage dashboards that monitor `urgency_category` will classify a life-threatening haemorrhage as a routine case.**

---

## 5. Safe Fallback and Exception Resilience

Fault injection testing using Python `mock.patch` evaluated error handling across the adaptation pipeline:

| Subsystem Tested | Injected Fault | Observed System Response | Category Preserved? | Telemetry Recorded | Leakage of Stack Trace to User |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Symptom Extractor** | `extract_symptom` raises `Exception` | Verbatim reference response returned | **ROUTINE** | `fallback_triggered: True` | **None** (Clean response) |
| **Adaptation Assembly** | `adapt_response` raises `RuntimeError` | Verbatim reference response returned | **PRIORITY** | `fallback_triggered: True` | **None** (Clean response) |
| **Clinical Validator** | `validate` returns `(False, "Simulated")` | Verbatim reference response returned | **ROUTINE** | `fallback_triggered: True` | **None** (Clean response) |
| **Emergency Bypass** | Adapter artificially disabled | Verbatim Emergency Template returned | **EMERGENCY** | Bypass applied | **None** (Clean response) |

**Conclusion:** Runtime failures are caught safely. The assistant falls back to verbatim approved reference responses with uncorrupted text. Technical tracebacks are written to application logs and never exposed to the patient.

---

## 6. Performance Benchmark Verification

Dual-level benchmarking was performed on the active host environment across 1,000 consecutive requests (200 warmup runs) using a balanced test suite (Emergency, Priority, Routine, and Medication queries in English, Yoruba, and Pidgin):

### Hardware & Environment Profile
- **Host OS:** Windows 11 Home / AMD64 (OS Build 10.0.26100)
- **CPU:** Intel64 Family 6 Model 142 Stepping 10 (8 logical cores @ 1.51–1.71 GHz)
- **RAM:** 16.0 GB (2.4 GB available during test execution)
- **Runtime:** Python 3.10.11 (tags/v3.10.11:7d4cc5a)

### Dual-Level Benchmark Comparison

| Performance Metric | Level A: Direct Assistant (`assistant.respond()`) | Level B: Live HTTP Server (`POST /api/chat`) |
| :--- | :--- | :--- |
| **Requests Processed** | 1,000 | 1,000 |
| **Warmup Count** | 200 | 200 |
| **Total Elapsed Time** | **1.9915 s** | **6.9760 s** |
| **Throughput** | **502.12 req/sec** | **143.35 req/sec** |
| **Mean Latency** | **1.989 ms** | **6.847 ms** |
| **Median (p50) Latency** | **2.033 ms** | **5.740 ms** |
| **95th Percentile (p95)** | **5.287 ms** | **14.445 ms** |
| **99th Percentile (p99)** | **6.539 ms** | **18.795 ms** |
| **Minimum Latency** | **0.026 ms** (Emergency) | **1.460 ms** |
| **Maximum Latency** | **7.631 ms** | **60.780 ms** |

### Explanation of Performance Variance:
1. **Direct Assistant (Level A):** Reflects pure in-memory algorithmic execution (string normalization, regex scans, polarity checks, slot assembly). Averaging ~1.99 ms per transaction, it confirms the determinism of the four-slot template adaptation engine.
2. **Live HTTP Server (Level B):** Adds loopback TCP socket connection handling, HTTP request/response framing, header parsing, JSON serialization/deserialization, and socket I/O buffering.
3. **Audit Caveat:** Direct assistant execution metrics (~1–2 ms) must not be reported as end-to-end API server performance. In production, network transit and HTTP protocol parsing increase median latency to ~5.7 ms.

---

## 7. Repository and Dataset Integrity Verification

1. **Automated Test Suite:**  
   Ran `python -m unittest discover -s motherlypulse_app/tests`.  
   **Result:** **62 / 62 PASS** in 29.75s.
2. **Dataset Validation Checks:**  
   Ran `validate_data.py` (19/19 PASS) and `validate_multilingual_data.py` (12/12 PASS).  
   **Result:** **31 / 31 PASS** (100%).
3. **Dataset File Timestamp Audit:**  
   Inspected all files in `MotherlyPulse_Data/04_Conversation_Data/`:
   - `english_pairs.csv` / `.jsonl`: Last modified October 30, 2026.
   - `yoruba_pairs.csv` / `.jsonl`: Last modified November 3, 2026.
   - `pidgin_pairs.csv` / `.jsonl`: Last modified November 3, 2026.
   - `adaptation_template.csv`: Last modified November 3, 2026.  
   **Zero dataset files were modified during Phase 1.5 or Phase 1.5.1.**
4. **Investigation of Earlier `git status` Failure:**  
   Command `git rev-parse --is-inside-work-tree` returned `fatal: not a git repository (or any of the parent directories): .git`.  
   **Explanation:** The project root `.` was set up as a standalone directory without Git version control initialized. The exit code 1 was an expected Git CLI response to an uninitialized repository, not an environment crash or corrupt repository state.

---

## 8. Remaining Limitations and Recommendations

Before clinical deployment or wide-scale production release, the following items must be addressed:

1. **Word-Based Numerical Normalization:**  
   Enhance `_extract_dosages` and `_extract_durations` with a word-to-digit pre-normalizer (e.g., mapping `"three"` $\to$ `"3"`, `"two"` $\to$ `"2"`, `"ẹta"` $\to$ `"3"`) to prevent word-based dosage mutations from bypassing regex checks.
2. **Bidirectional Pharmaceutical Matching:**  
   Assert that every pharmaceutical and supplement token present in the approved reference response is also present in the candidate response, preventing silent omission of recommended treatments.
3. **Drug-to-Dosage Noun Phrase Binding:**  
   Parse dosages as linked tuples: `(drug_name, value, unit)` rather than unlinked sets of quantities, preventing cross-swapping of dosages between multiple medications.
4. **Pre-Validation Emergency Classification:**  
   In `assistant.respond()`, run `classifier.classify()` **before** language handling. If an incoming message is classified as `EMERGENCY`, preserve the `EMERGENCY` category and return emergency dispatch contacts, even when issuing an unsupported language limitation notice.
5. **Server-Level Uncaught Exception Handler:**  
   Wrap `self.assistant.respond()` in `server.py` with an outer `try...except` block returning HTTP 500 with a structured JSON error body to ensure the server never terminates a connection abruptly on unexpected classifier errors.

---

## 9. Final Audit Verdict

# **CONDITIONAL PASS**

**Justification:**  
The six specific defects identified in `PHASE_1_5_ACCEPTANCE_AUDIT.md` (`CCP-01`, `MSS-01`, `MSS-02`, `MSS-03`, `E2E-01`, `MLA-04`) were remediated as reported. All 62 automated unit tests and 31 dataset integrity checks pass unconditionally. However, independent stress testing uncovered four edge-case vulnerabilities (word-based number mutations, drug omission, multi-drug dosage swapping, and unsupported-language emergency triage downgrade) that must be addressed before clinical sign-off.

