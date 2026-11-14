# Phase 1.5.2 Regression and Verification Test Results

**Date:** November 5, 2026  
**Scope:** Comprehensive regression test execution covering Phase 1, Phase 1.5, and Phase 1.5.2 safety remediations  
**Status:** 100% PASS (86 / 86 Automated Unit Tests, 31 / 31 Dataset Checks)

---

## 1. Test Suite Composition & Count Summary

| Test Module | Description | Previous Count (Phase 1.5) | New Tests Added | Current Count (Phase 1.5.2) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`test_phase1_5_2_remediation.py`** | Dedicated suite for Phase 1.5.2 critical fixes (Language independence, drug omission, dosage association, word numbers) | 0 | **+24** | **24** | **PASS (100%)** |
| **`test_phase1_5_remediation.py`** | Phase 1.5 core tests (Dosage mutations, imperatives, unlisted drugs, supplement polarities, live HTTP, safe fallback) | 16 | 0 | **16** | **PASS (100%)** |
| **`test_audit_invariants.py`** | Post-implementation clinical invariant audit tests | 14 | 0 | **14** | **PASS (100%)** |
| **`test_template_adaptation.py`** | Core four-slot template adaptation engine unit tests | 16 | 0 | **16** | **PASS (100%)** |
| **`test_hybrid_router_regression.py`**| Dynamic triage classifier and hybrid router regression tests | 14 | 0 | **14** | **PASS (100%)** |
| **`test_stage1_dependencies_and_access.py`** | System environment and dependency access tests | 2 | 0 | **2** | **PASS (100%)** |
| **TOTAL AUTOMATED TESTS** | | **62** | **+24** | **86** | **PASS (100%)** |

---

## 2. Dataset Validation Check Summary

| Validation Suite | Target Assets Verified | Total Checks | Passing Checks | Status |
| :--- | :--- | :--- | :--- | :--- |
| **`validate_data.py`** | Core CSV/JSONL records, sources, passages, LGA facilities (55), immunization centers (43), triage prefixes, emergency precedence | 19 | 19 | **PASS (100%)** |
| **`validate_multilingual_data.py`** | English, Yoruba, and Pidgin 200-pair alignment, domain balance, train/test partition (160/40), prefix format | 12 | 12 | **PASS (100%)** |
| **TOTAL DATASET CHECKS** | | **31** | **31** | **PASS (100%)** |

---

## 3. Dedicated Phase 1.5.2 Test Breakdown (`test_phase1_5_2_remediation.py`)

### Group 1: Emergency Classification Independence (7 Tests)
- `test_english_emergency_with_unsupported_language_parameter`: Confirmed category remains `emergency`.
- `test_yoruba_emergency_with_unsupported_language_parameter`: Confirmed Yoruba bleeding emergency preserves `emergency`.
- `test_pidgin_emergency_with_unsupported_language_parameter`: Confirmed Pidgin haemorrhage emergency preserves `emergency`.
- `test_unsupported_language_ordinary_query_not_classified_as_routine`: Confirmed non-emergency Hausa query reports `unassessed` rather than `routine`.
- `test_empty_input_with_unsupported_language`: Confirmed empty message with unsupported language reports `unassessed`.
- `test_emergency_message_with_missing_language`: Confirmed `language=None` preserves `emergency`.
- `test_emergency_message_with_invalid_language_type`: Confirmed integer language tag (`123`) preserves `emergency`.

### Group 2: Medication Instruction Omission (6 Tests)
- `test_single_medication_omitted_rejected`: Confirmed omission of `paracetamol` fails with `ERR_OMITTED_MEDICATION`.
- `test_one_of_two_medications_omitted_rejected`: Confirmed omission of `iron` from multi-drug reference fails with `ERR_OMITTED_MEDICATION`.
- `test_medication_retained_but_dosage_omitted_rejected`: Confirmed omitting dosage while retaining drug name fails with `ERR_OMITTED_DOSAGE`.
- `test_medication_retained_but_frequency_omitted_rejected`: Confirmed omitting frequency fails with `ERR_OMITTED_FREQUENCY`.
- `test_medication_retained_but_prohibition_removed_rejected`: Confirmed dropping prohibition fails with `ERR_MEDICATION_POLARITY_INVERSION`.
- `test_two_medications_reordered_meaning_preserved_accepted`: Confirmed reordering instructions without changing bindings passes.

### Group 3: Dosage-to-Medication Instruction Association (4 Tests)
- `test_swapped_dosages_between_two_medications_rejected`: Confirmed swapping 500mg and 200mg between two drugs fails with `ERR_NUMERICAL_DOSAGE_MUTATED`.
- `test_swapped_frequencies_between_two_medications_rejected`: Confirmed swapping once daily and twice daily fails with `ERR_NUMERICAL_DOSAGE_MUTATED`.
- `test_swapped_durations_between_two_medications_rejected`: Confirmed swapping 7 days and 3 days fails with `ERR_NUMERICAL_DOSAGE_MUTATED`.
- `test_medication_name_omitted_while_dosage_remains_rejected`: Confirmed dropping drug name while keeping dosage fails with `ERR_OMITTED_MEDICATION`.

### Group 4: Word-Based Numerical Invariance (7 Tests)
- `test_word_number_duration_three_to_seven_days_rejected`: "three days" $\to$ "seven days" rejected.
- `test_word_number_dosage_two_to_four_tablets_rejected`: "two tablets" $\to$ "four tablets" rejected.
- `test_word_number_one_to_two_doses_rejected`: "one dose" $\to$ "two doses" rejected.
- `test_word_number_once_daily_to_twice_daily_rejected`: "once daily" $\to$ "twice daily" rejected.
- `test_word_number_five_to_eight_weeks_rejected`: "five weeks" $\to$ "eight weeks" rejected.
- `test_word_number_two_to_five_millilitres_rejected`: "two millilitres" $\to$ "five millilitres" rejected.
- `test_digit_and_word_unambiguous_equivalence_accepted`: "2 tablets" vs "two tablets" accepted as equivalent.

---

## 4. Execution Trace Evidence

```
............................................................Routine education adaptation error: Simulated memory allocation failure
Traceback (most recent call last):
  File "motherlypulse_app\assistant.py", line 326, in respond
...
Priority adaptation error: Simulated memory allocation failure
Traceback (most recent call last):
  File "motherlypulse_app\assistant.py", line 241, in respond
...
..........................
----------------------------------------------------------------------
Ran 86 tests in 9.825s

OK
```

---

## 5. Conclusion

All 86 automated tests across the 6 test modules pass unconditionally. The 31 dataset validation checks confirm that no dataset corruption or field drift has occurred.

