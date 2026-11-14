# MotherlyPulse — Phase 1.5.2 Critical Safety Remediation Report

**Date:** November 5, 2026  
**Scope:** Corrective engineering addressing the four critical safety vulnerabilities identified in `PHASE_1_5_1_INDEPENDENT_VERIFICATION.md`  
**Status:** COMPLETE (86/86 Automated Tests Passing, 31/31 Dataset Checks Passing)

---

## 1. Executive Summary

Following the Phase 1.5.1 independent verification audit, four critical vulnerabilities were targeted for corrective engineering:
1. **Unsupported-Language Emergency Downgrade:** Requesting an unsupported language (e.g. Hausa) triggered an early return in `assistant.respond()` before dynamic triage classification, forcing an unassessed input into an artificial `routine` category.
2. **Medication Instruction Omission:** Candidates omitting approved medication instructions (drug names, dosages, durations, frequencies) could pass if unrelated sentence words achieved 65% recall.
3. **Dosage-to-Medication Association Failure:** Dosages were verified as an unlinked "bag of numbers" per unit (`mg`), allowing dosages to be swapped between medications (e.g., 500mg paracetamol and 200mg iron swapped to 200mg paracetamol and 500mg iron).
4. **Word-Based Numerical Instruction Bypass:** Numerical extractors only matched ASCII digits (`\d+`), allowing written number words ("three days" $\to$ "seven days", "two tablets" $\to$ "four tablets") to bypass numerical invariance.

All four vulnerabilities have been resolved using deterministic, zero-LLM architecture. The existing three operational categories (`EMERGENCY`, `PRIORITY`, `ROUTINE`) and router policies are strictly preserved.

---

## 2. Remediation Overview Table

| Vulnerability ID | Defect Classification | Affected Subsystem | Remediation Strategy | Status |
| :--- | :--- | :--- | :--- | :--- |
| **VULN-1.5.2-01** | Emergency Downgrade on Language Gating | `assistant.py` (`MotherlyPulseAssistant.respond`) | Executed `classifier.classify()` before language gating. Emergency status is independent of language support; unsupported non-emergency queries report explicit `unassessed` status. | **RESOLVED** |
| **VULN-1.5.2-02** | Medication Instruction Omission | `template_adapter.py` (`ClinicalInvariantValidator`) | Implemented clause-level medication instruction extraction (`_get_medication_clauses`). Rejects any candidate that omits a reference medication name, dosage, frequency, duration, or prohibition. | **RESOLVED** |
| **VULN-1.5.2-03** | Unlinked Dosage-to-Drug Association | `template_adapter.py` (`ClinicalInvariantValidator`) | Bound extracted dosages, frequencies, and durations directly to each specific pharmaceutical/supplement noun. Rejects cross-medication swapping. | **RESOLVED** |
| **VULN-1.5.2-04** | Word-Based Numerical Bypass | `template_adapter.py` (`ClinicalInvariantValidator`) | Implemented `_normalize_numerical_words()` supporting unambiguous written number conversions (`three days` $\to$ `3 days`, `two tablets` $\to$ `2 tablet`, `once daily`, `twice daily`). | **RESOLVED** |

---

## 3. Detailed Engineering Solutions

### 3.1. Emergency Classification Independence (`assistant.py`)
In `motherlypulse_app/assistant.py`:
- Moved dynamic triage classification (`self.classifier.classify(message, conversation_history)`) to execute **before** language gating.
- If an emergency is detected, it returns `urgency_category: "emergency"` with the approved emergency response and emergency dispatch numbers (112 and ODEMSA 0812 756 5478), regardless of whether the requested language is supported.
- If the language is unsupported and emergency status is not established, the assistant returns `urgency_category: "unassessed"` with `status: "language_not_supported"`, completely eliminating the artificial assignment of `routine`.

### 3.2. Clause-Level Medication Instruction Extraction (`template_adapter.py`)
In `motherlypulse_app/template_adapter.py`:
- Implemented `_get_medication_clauses()` which extracts the distinct clause/context surrounding each pharmaceutical or supplement entity.
- If a medication is present in the approved reference response, it MUST appear in the candidate response. Omission triggers `ERR_OMITTED_MEDICATION`.
- If an approved medication has an associated dosage, frequency, duration, or restriction, that specific clause must preserve those exact attributes.

### 3.3. Dosage-to-Medication Binding (`template_adapter.py`)
- Extracted dosages, durations, and frequencies are evaluated **per medication clause**:
  `ref_dosages = self._extract_dosages(ref_clause_for_med)`
  `cand_dosages = self._extract_dosages(cand_clause_for_med)`
- Cross-swapping dosages (e.g. 500mg paracetamol + 200mg iron swapped to 200mg paracetamol + 500mg iron) is detected and rejected with `ERR_NUMERICAL_DOSAGE_MUTATED`.
- Reordering medication sentences without altering their associated instructions remains permissible.

### 3.4. Word-Based Numerical Normalization (`template_adapter.py`)
- Implemented `_normalize_numerical_words()` with unambiguous word-to-number dictionary (`WORD_TO_NUMBER`) and unit normalizations (`UNIT_NORMALIZATIONS`).
- Standardizes unambiguous number words before units ("three days" $\to$ "3 days", "two tablets" $\to$ "2 tablet", "two millilitres" $\to$ "2 ml", "once daily", "twice daily").
- Numerical extractors operate on normalized text, closing the word-based bypass.

---

## 4. Verification and Regression Testing Summary

| Test Category | Baseline Tests | New Tests Added | Total Passing Tests |
| :--- | :--- | :--- | :--- |
| **Unit & Integration Tests** | 62 | **24** | **86 / 86 PASS** (100%) |
| **Core Dataset Integrity** | 19 | 0 (Unmodified) | **19 / 19 PASS** (100%) |
| **Multilingual Dataset Parity** | 12 | 0 (Unmodified) | **12 / 12 PASS** (100%) |

---

## 5. Strict Clinical Boundaries

> [!IMPORTANT]
> **Engineering Invariance vs. Clinical Authorization:**  
> These safeguards ensure that conversational adaptation never drops, alters, or cross-swaps approved medication instructions, and never downgrades emergency triage. Automated tests confirm syntactic determinism and mathematical invariance. They do **NOT** establish clinical efficacy. All 200 conversational dataset records remain marked as `pending_clinical_review`.

