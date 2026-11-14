# Word-Based Numerical Invariance Results

**Target Vulnerability:** VULN-1.5.2-04 (Bypass of Numerical Invariance via Written Number Words)  
**Component:** `motherlypulse_app/template_adapter.py` (`ClinicalInvariantValidator`)  
**Audit Date:** November 5, 2026  
**Status:** FULLY REMEDIATED (Standardized Word-to-Digit Normalization Enforced)

---

## 1. Vulnerability Root Cause Analysis

In the previous Phase 1.5 validator, numerical extraction patterns strictly anchored on ASCII digits:
```python
r"\b(\d+(?:\.\d+)?)\s*(mg|ml|tablets?|capsules?)\b"
r"\b(\d+)\s+(days?|weeks?|months?)\b"
```

When clinical instructions were phrased using English words rather than numeric digits:
- Reference: *"Continue prescribed care for three days."*
- Mutated Candidate: *"Continue prescribed care for seven days."*

The digit extractor found no matches (`ref_durations == []`, `cand_durations == []`). The sentence fell back to word recall where 4 out of 5 content words (`{"continue", "prescribed", "care", "days"}`) matched ($80\% \ge 65\%$). The mutation from 3 days to 7 days passed without triggering rejection.

---

## 2. Corrective Engineering Architecture

In `template_adapter.py`, `ClinicalInvariantValidator` now executes unambiguous word-to-digit pre-normalization via `_normalize_numerical_words()` prior to all numerical, dosage, duration, frequency, and clause evaluations:

### 2.1. Standardized Dictionaries
1. **Word-to-Number Map (`WORD_TO_NUMBER`):**  
   Maps `"zero"` through `"twenty"`, plus `"twenty-four"` and `"forty-eight"`, to their exact ASCII digit representations (`"0"` through `"20"`, `"24"`, `"48"`).
2. **Unit Normalization (`UNIT_NORMALIZATIONS`):**  
   Standardizes spelled-out units:
   - `"millilitres"`, `"milliliters"` $\to$ `"ml"`
   - `"milligrams"` $\to$ `"mg"`
   - `"micrograms"` $\to$ `"mcg"`
   - `"tablets"`, `"capsules"`, `"pills"` $\to$ `"tablet"`
   - `"tablespoons"`, `"tbsp"` $\to$ `"tablespoon"`
   - `"teaspoons"`, `"tsp"` $\to$ `"teaspoon"`
3. **Frequency Standardizations:**  
   Maps phrases like `"one time a day"`, `"once a day"` $\to$ `"once daily"`; `"two times a day"`, `"twice a day"` $\to$ `"twice daily"`.

### 2.2. Targeted Replacement Scope
Replacements are strictly anchored to clinical contexts where a number word is immediately followed by a clinical unit or time measure (`days`, `weeks`, `months`, `hours`, `tablets`, `ml`, `mg`, `dose`, `times`). This prevents corrupting unrelated English prose.

---

## 3. Empirical Test Matrix and Results

All test cases were executed via `motherlypulse_app/tests/test_phase1_5_2_remediation.py`:

| Test ID | Reference Instruction | Candidate Variation Tested | Normalized Comparison | Expected Outcome | Actual Outcome | Validator Diagnostic Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-WNI-01** | "Continue prescribed care for three days." | "Continue prescribed care for seven days." | `3 days` vs `7 days` | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Clinical duration 3 days was altered to 7 days` |
| **TEST-WNI-02** | "Take two tablets of paracetamol." | "Take four tablets of paracetamol." | `2 tablet` vs `4 tablet` | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Dosage for 'paracetamol' was altered from 2.0 tablet to 4.0 tablet` |
| **TEST-WNI-03** | "Take one dose of vitamin A supplement." | "Take two doses of vitamin A supplement." | `1 dose` vs `2 dose` | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Dosage for 'vitamin a' was altered from 1.0 dose to 2.0 dose` |
| **TEST-WNI-04** | "Take iron supplement once daily." | "Take iron supplement twice daily." | `once daily` vs `twice daily` | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Dosing frequency 'once daily' for 'iron' was altered or omitted` |
| **TEST-WNI-05** | "Fetal scan is scheduled in five weeks." | "Fetal scan is scheduled in eight weeks." | `5 weeks` vs `8 weeks` | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Clinical duration 5 weeks was altered to 8 weeks` |
| **TEST-WNI-06** | "Administer two millilitres of liquid medicine." | "Administer five millilitres of liquid medicine." | `2 ml` vs `5 ml` | **REJECT** | **REJECT** | `ERR_NUMERICAL_DOSAGE_MUTATED: Prescribed dosage 2.0 ml was altered to 5.0 ml` |
| **TEST-WNI-07** | "Take 2 tablets of paracetamol for pain." | "Take two tablets of paracetamol for pain." | `2 tablet` vs `2 tablet` (Equivalence) | **ACCEPT** | **ACCEPT** | Validated successfully (Equivalence confirmed) |

---

## 4. Conclusion

The word-based numerical bypass has been resolved. Unambiguous number words and spelled-out units are normalized to standard numeric tuples before validation, ensuring that duration, dosage, and frequency mutations are rejected regardless of whether they are formatted as digits or spelled-out words.

