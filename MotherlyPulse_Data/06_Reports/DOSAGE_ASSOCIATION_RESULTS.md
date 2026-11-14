# Dosage-to-Medication Instruction Association Results

**Target Vulnerability:** VULN-1.5.2-03 (Unlinked Bag-of-Numbers Dosage Cross-Swapping)  
**Component:** `motherlypulse_app/template_adapter.py` (`ClinicalInvariantValidator`)  
**Audit Date:** November 5, 2026  
**Status:** FULLY REMEDIATED (Deterministic Noun-to-Instruction Binding Enforced)

---

## 1. Vulnerability Analysis: The Bag-of-Numbers Flaw

In the Phase 1.5 validator, numerical dosage invariance extracted a flat list of `(value, unit)` tuples across the entire candidate and reference texts:
```python
# Vulnerable logic:
ref_dosages = self._extract_dosages(ref_lower)   # [(500.0, 'mg'), (200.0, 'mg')]
cand_dosages = self._extract_dosages(cand_lower) # [(200.0, 'mg'), (500.0, 'mg')]

for ref_val, ref_unit in ref_dosages:
    matching_cand_vals = [c_val for c_val, c_u in cand_dosages if c_u == ref_unit]
    if not any(abs(c_val - ref_val) < 1e-4 for c_val in matching_cand_vals):
        return False, ERR_NUMERICAL_DOSAGE_MUTATED
```

### The Exploit:
- Reference: *"Take 500mg paracetamol for headache and take 200mg iron supplement daily."*
- Mutated Candidate: *"Take 200mg paracetamol for headache and take 500mg iron supplement daily."*
Because both `500.0 mg` and `200.0 mg` existed in the candidate's bag of dosages, the validator confirmed that `500.0` was present in `matching_cand_vals` and `200.0` was present in `matching_cand_vals`. The cross-swap between paracetamol and iron was accepted without error.

---

## 2. Corrective Engineering Architecture

In `template_adapter.py`, the validator binds every numerical instruction directly to its governing medication entity:

```
Reference Text
  │
  ├─► Clause 1: "Take 500mg paracetamol for headache"
  │     └─► Medication: PARACETAMOL
  │           ├─ Dosage: 500.0 mg
  │           └─ Frequency: None
  │
  └─► Clause 2: "and take 200mg iron supplement daily"
        └─► Medication: IRON
              ├─ Dosage: 200.0 mg
              └─ Frequency: once daily
```

During validation, the candidate's clauses are partitioned identically:
1. The candidate clause governing **PARACETAMOL** must contain `500.0 mg`.
2. The candidate clause governing **IRON** must contain `200.0 mg` and `once daily`.
3. If the candidate attaches `200.0 mg` to paracetamol, the validator compares the candidate's paracetamol dosage (`200.0 mg`) with the reference's paracetamol dosage (`500.0 mg`), immediately failing with:
   $$\texttt{ERR\_NUMERICAL\_DOSAGE\_MUTATED: Dosage for 'paracetamol' was altered from 500.0 mg to 200.0 mg}$$

---

## 3. Empirical Test Matrix and Results

All test scenarios were executed via `motherlypulse_app/tests/test_phase1_5_2_remediation.py`:

| Test ID | Reference Input | Candidate Variation Tested | Defect Simulated | Expected Outcome | Actual Outcome | Validator Diagnostic Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-DMA-01** | 500mg paracetamol + 200mg iron | 200mg paracetamol + 500mg iron | Dosages swapped between medications | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Dosage for 'paracetamol' was altered from 500.0 mg to 200.0 mg` |
| **TEST-DMA-02** | paracetamol once daily + iron twice daily | paracetamol twice daily + iron once daily | Frequencies swapped between medications | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Dosing frequency 'once daily' for 'paracetamol' was altered or omitted` |
| **TEST-DMA-03** | ampicillin for 7 days + paracetamol for 3 days | ampicillin for 3 days + paracetamol for 7 days | Durations swapped between medications | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Duration for 'ampicillin' was altered from 7 days to 3 days` |
| **TEST-DMA-04** | 500mg paracetamol + 200mg iron daily | 200mg iron daily + 500mg paracetamol | Sentences reordered without changing bindings | **ACCEPT** | **ACCEPT** | Validated successfully (Bindings 100% intact) |
| **TEST-DMA-05** | Take 500mg paracetamol if authorized | Take 500mg if authorized | Medication omitted while dosage remains | **REJECT** | **REJECT** | `ERR_OMITTED_MEDICATION: Prescribed medication/supplement 'paracetamol' was omitted from candidate response` |

---

## 4. Conclusion

The unlinked bag-of-numbers comparison has been replaced with strict entity-level instruction binding. Dosage, duration, frequency, and polarity are individually validated per medication, preventing dangerous cross-swapping of instructions in multi-drug clinical responses.

