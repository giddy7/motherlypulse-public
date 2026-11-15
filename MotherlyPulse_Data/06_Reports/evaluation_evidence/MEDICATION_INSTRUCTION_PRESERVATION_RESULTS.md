# Medication Instruction Preservation Results

**Target Vulnerability:** VULN-1.5.2-02 (Medication Instruction Omission via General Sentence Recall Bypass)  
**Component:** `motherlypulse_app/template_adapter.py` (`ClinicalInvariantValidator`)  
**Audit Date:** November 5, 2026  
**Status:** FULLY REMEDIATED (100% Invariant Enforcement on Medication Entities & Instructions)

---

## 1. Vulnerability Root Cause Analysis

In the previous Phase 1.5 validator, medication checks relied primarily on a negative token screen that only checked whether the candidate introduced ungrounded drugs not present in the reference:
```python
for pattern in FORBIDDEN_MEDICATION_TOKENS:
    match_cand = re.search(pattern, cand_lower)
    if match_cand:
        match_ref = re.search(pattern, ref_lower)
        if not match_ref: # Candidate introduced drug not in reference
            return False, ERR_INVENTED_MEDICATION
```

This unidirectional check failed to detect when an approved medication in the reference was **omitted** from the candidate:
- Reference: *"You may take paracetamol if authorized by your midwife. Attend clinic as advised."*
- Candidate: *"You may take pain relief if authorized by your midwife. Attend clinic as advised."*
Because 4 out of 5 content words (`{"may", "take", "authorized", "midwife"}`) were preserved ($80\% \ge 65\%$), the omission of `paracetamol` was accepted.

---

## 2. Corrective Engineering Architecture

The remediated validator in `template_adapter.py` introduces dedicated clause-level medication instruction extraction via `_get_medication_clauses()`:

1. **Bidirectional Medication Name Verification:**  
   The validator inventories all pharmaceutical and supplement entities in the reference (`ref_meds`). Every reference medication MUST be present in the candidate (`cand_meds`).  
   If any reference medication is missing:
   $$\text{Reject with: } \texttt{ERR\_OMITTED\_MEDICATION}$$
2. **Clause-Level Instruction Extraction:**  
   The validator extracts the specific clause or sentence window surrounding each medication mention:
   - Prescribed dosage (`extract_dosages`)
   - Dosing frequency (`extract_frequencies`)
   - Administration duration (`extract_durations`)
   - Clinical polarity (prohibition vs permission markers)
3. **Instruction Preservation Guarantee:**  
   If an approved medication instruction contains a dosage, duration, frequency, or restriction in the reference, that exact instruction must be preserved in the candidate's corresponding medication clause.

---

## 3. Empirical Test Matrix and Results

All test cases were executed via `motherlypulse_app/tests/test_phase1_5_2_remediation.py`:

| Test ID | Reference Instruction | Candidate Variation Tested | Defect Simulated | Expected Outcome | Actual Outcome | Validator Diagnostic Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-MIP-01** | "You may take paracetamol if authorized..." | "You may take pain relief if authorized..." | Drug name omitted | **REJECT** | **REJECT** | `ERR_OMITTED_MEDICATION: Prescribed medication/supplement 'paracetamol' was omitted from candidate response` |
| **TEST-MIP-02** | "Take 500mg paracetamol and 200mg iron daily." | "Take 500mg paracetamol daily." | 1 of 2 medications omitted (iron dropped) | **REJECT** | **REJECT** | `ERR_OMITTED_MEDICATION: Prescribed medication/supplement 'iron' was omitted from candidate response` |
| **TEST-MIP-03** | "Take 500mg paracetamol for fever." | "Take paracetamol for fever." | Medication retained, dosage omitted | **REJECT** | **REJECT** | `ERR_OMITTED_DOSAGE: Dosage for 'paracetamol' was omitted from candidate` |
| **TEST-MIP-04** | "Take iron supplement once daily with water." | "Take iron supplement with water." | Medication retained, frequency omitted | **REJECT** | **REJECT** | `ERR_OMITTED_FREQUENCY: Frequency for 'iron' was omitted from candidate` |
| **TEST-MIP-05** | "Do not take ibuprofen during pregnancy." | "Regarding ibuprofen, consult midwife." | Medication retained, prohibition removed | **REJECT** | **REJECT** | `ERR_MEDICATION_POLARITY_INVERSION: Prohibited medication 'ibuprofen' was rendered permissive or stripped of prohibition` |
| **TEST-MIP-06** | "Take 500mg paracetamol and take 200mg iron daily." | "Take 200mg iron daily and take 500mg paracetamol." | Reordered without changing meaning | **ACCEPT** | **ACCEPT** | Validated successfully (100% preservation) |

---

## 4. Conclusion

General sentence recall ($\ge 65\%$) is no longer used to evaluate medication instructions. All approved medication names and their associated clinical parameters (dosage, frequency, duration, polarity) are deterministically bound and protected against omission.

