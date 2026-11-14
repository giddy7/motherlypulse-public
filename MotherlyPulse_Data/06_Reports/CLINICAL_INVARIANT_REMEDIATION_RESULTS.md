# Clinical Invariant Remediation Results
**Vulnerability Focus:** CCP-01 (Clinical Core Preservation & Short Imperative Filtering Bypass)  
**Component:** `motherlypulse_app/template_adapter.py` (`ClinicalInvariantValidator`)  
**Audit Date:** November 4, 2026  
**Status:** FULLY REMEDIATED (Zero Imperative Bypasses Detected)

---

## 1. Vulnerability Analysis (`CCP-01`)

In the Phase 1.5 Acceptance Audit (`PHASE_1_5_ACCEPTANCE_AUDIT.md`), the validator was found to drop or ignore short reference sentences:
```python
# Vulnerable code prior to remediation:
ref_sentences = [s.strip() for s in re.split(r'[\.\n]', ref_core) if len(s.strip()) > 8]
for s in ref_sentences:
    s_words = set(re.findall(r"\b\w{4,}\b", s.lower()))
    if len(s_words) >= 3:   # <-- VULNERABILITY: Skipped sentences with < 3 content words
        overlap = s_words.intersection(cand_words)
        recall = len(overlap) / len(s_words)
        if recall < 0.60:
            ...
```

Under this vulnerable implementation:
- Life-saving imperatives such as **"Do not wait."**, **"Go to clinic."**, **"Do not take this medicine."**, and **"Return if symptoms worsen."** have fewer than 3 words with $\ge 4$ characters.
- As a result, an adapted candidate response could completely omit or mutate these critical sentences without failing validation.

---

## 2. Corrective Engineering Architecture

The remediated validator in `template_adapter.py` enforces a dual-tier preservation protocol:

```
Reference Response Clinical Core
           │
           ├─► 1. Sentence Clause Extraction (split on [.!\n;], min length >= 3 chars)
           │
           ├─► 2. Mandatory Imperative Pattern Screen (MANDATORY_IMPERATIVE_PATTERNS)
           │       └─► Matched imperative MUST appear in candidate response (regex match)
           │           If missing: Fail with ERR_CLINICAL_CORE_MUTATED
           │
           └─► 3. Content Word Recall Screen
                   ├─► Short clauses (1–2 content words): 100% recall mandatory
                   └─► Multi-word clauses (>= 3 content words): >= 65% recall mandatory
                       If recall fails: Fail with ERR_CLINICAL_CORE_MUTATED
```

### 2.1. Mandatory Imperative Pattern Inventory
The following clinical imperative regex patterns are now actively enforced:
- `r"\bdo\s+not\s+wait\b"`
- `r"\bgo\s+to\s+(the\s+)?(clinic|hospital|health\s+centre|health\s+center|doctor)\b"`
- `r"\bseek\s+(immediate|prompt|emergency)?\s*(medical\s+)?(help|care|attention)\b"`
- `r"\bdo\s+not\s+(take|use|drink|ingest|administer)\b"`
- `r"\bcall\s+(emergency|112|hospital|health\s+centre)\b"`
- `r"\breturn\s+if\s+(symptoms?\s+)?worsen\b"`
- `r"\battend\s+(your\s+)?(scheduled\s+)?(clinic\s+visit|health\s+centre)\b"`
- `r"\bconsult\s+(your\s+)?(doctor|midwife|health\s+worker|healthcare\s+provider)\b"`
- `r"\be\s+lo\s+si\b"`, `r"\be\s+ma\s+se\b"`, `r"\bko\s+gbodo\b"` (Yoruba)
- `r"\bgo\s+hospital\b"`, `r"\bmake\s+you\s+no\b"` (Nigerian Pidgin)

---

## 3. Test Suite Verification & Results

Dedicated test cases in `motherlypulse_app/tests/test_phase1_5_remediation.py` verified all short imperative scenarios against the remediated validator:

| Test Case | Reference Imperative Clause | Candidate Variation | Expected Outcome | Actual Outcome | Validator Diagnostic |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-CCP-01A** | "Do not wait." | Verbatim preserved | **PASS** | **PASS** | Validated successfully |
| **TEST-CCP-01B** | "Do not wait." | Clause omitted entirely | **FAIL (Caught)** | **FAIL** | `ERR_CLINICAL_CORE_MUTATED: Mandatory clinical imperative omitted or weakened: 'Do not wait'` |
| **TEST-CCP-01C** | "Do not wait." | Weakened: "You can wait a bit." | **FAIL (Caught)** | **FAIL** | `ERR_CLINICAL_CORE_MUTATED: Mandatory clinical imperative omitted or weakened: 'Do not wait'` |
| **TEST-CCP-02A** | "Go to clinic." | Verbatim preserved | **PASS** | **PASS** | Validated successfully |
| **TEST-CCP-02B** | "Go to clinic." | Replaced with "Rest at home." | **FAIL (Caught)** | **FAIL** | `ERR_CLINICAL_CORE_MUTATED: Mandatory clinical imperative omitted or weakened: 'Go to clinic'` |
| **TEST-CCP-03A** | "Return if symptoms worsen." | Verbatim preserved | **PASS** | **PASS** | Validated successfully |
| **TEST-CCP-03B** | "Return if symptoms worsen." | Replaced with "No need to return." | **FAIL (Caught)** | **FAIL** | `ERR_CLINICAL_CORE_MUTATED: Mandatory clinical imperative omitted or weakened: 'Return if symptoms worsen'` |
| **TEST-CCP-04** | "Do not take this medicine." | Omitted | **FAIL (Caught)** | **FAIL** | `ERR_CLINICAL_CORE_MUTATED: Mandatory clinical imperative omitted or weakened` |

---

## 4. Conclusion

The short clinical sentence filtering bypass (`CCP-01`) is completely eliminated. All short clinical imperatives, regardless of character length or word count, are strictly enforced during response validation. Any candidate response omitting or weakening a mandatory imperative is deterministically rejected, prompting an immediate fallback to the original approved reference response.

