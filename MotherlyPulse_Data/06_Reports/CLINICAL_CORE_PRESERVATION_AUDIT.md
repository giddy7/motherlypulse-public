# MotherlyPulse: Clinical Core Preservation Audit
**Phase 1.5 Independent Acceptance Audit: Recall Thresholds & Clinical Invariants**

**Audit Date:** November 4, 2026  
**Auditor:** Senior AI Evaluation Specialist & Clinical Safety Auditor  
**Module Audited:** [`motherlypulse_app.template_adapter.ClinicalInvariantValidator`](motherlypulse_app/template_adapter.py#L230-L380)  
**Audit Scope:** Multi-sentence recall logic, short sentence filtering, mandatory vs. explanatory element preservation.

---

## 1. Executive Summary

This independent acceptance audit investigated whether the 60% lexical recall threshold implemented during Phase 1 remediation provides sufficient guarantees that mandatory clinical instructions, escalation directives, and emergency warnings cannot be dropped during conversational adaptation.

### Key Audit Findings

| Finding ID | Finding Description | Severity | Validator Status |
|---|---|---|---|
| **CCP-01** | **Short Sentence Filtering Blind Spot:** Reference sentences with fewer than 3 words of length $\ge 4$ (e.g., *"Do not wait."*, *"Go to clinic."*) are completely bypassed by the sentence invariance check. | **HIGH** | **VULNERABILITY** |
| **CCP-02** | **Partial Content Deletion Within 60% Floor:** Long sentences allowing up to 40% word omission can drop specific clinical directives (e.g., specific prohibited traditional substances) while still passing validation. | **MEDIUM** | **PARTIAL LEAK** |
| **CCP-03** | **Critical Condition Warning Enforcement:** Dedicated condition marker filter (`preeclampsia`, `eclampsia`, `dehydration`, etc.) operates with 100% precision, preventing dropped clinical conditions. | **LOW** | **VERIFIED SAFE** |
| **CCP-04** | **Substantial Sentence Omission Catch:** Multi-sentence reference responses containing secondary diagnostic sentences (e.g., OGTT instructions) are cleanly rejected if omitted. | **LOW** | **VERIFIED SAFE** |

---

## 2. Detailed Technical Investigation of the 60% Recall Threshold

### 2.1 The Short Sentence Filtering Bypass (CCP-01)
- **Affected Code:** [`template_adapter.py`](motherlypulse_app/template_adapter.py#L320-L335)
  ```python
  ref_sentences = [s.strip() for s in re.split(r'[\.\n]', ref_core) if len(s.strip()) > 8]
  cand_words = set(re.findall(r"\b\w{4,}\b", cand_lower))
  for s in ref_sentences:
      s_words = set(re.findall(r"\b\w{4,}\b", s.lower()))
      if len(s_words) >= 3:
          overlap = s_words.intersection(cand_words)
          recall = len(overlap) / len(s_words)
          if recall < 0.60:
              return False, f"ERR_CLINICAL_CORE_MUTATED: ..."
  ```
- **Mechanism of Failure:**
  Lines 324–326 filter reference sentences by `if len(s_words) >= 3:`.
  If a clinical instruction sentence in the approved reference contains fewer than three words with 4 or more letters:
  - *"Do not wait."* ──► `s_words = {'wait'}` (count = 1). **Bypassed.**
  - *"Go to clinic."* ──► `s_words = {'clinic'}` (count = 1). **Bypassed.**
  - *"Call 112 now."* ──► `s_words = {'call'}` (count = 1). **Bypassed.**
  - *"Stay calm."* ──► `s_words = {'stay', 'calm'}` (count = 2). **Bypassed.**
- **Empirical Reproduction:**
  ```python
  ref = "PRIORITY: Severe abdominal pain can occur. Do not wait. Go to clinic."
  cand = (
      "PRIORITY: I hear your concern. Regarding what you shared about pain: "
      "Severe abdominal pain can occur. Please consult your healthcare provider "
      "within 24 to 48 hours for proper clinical assessment."
  )
  is_valid, reason = validator.validate(cand, ref, "priority", "I have severe pain")
  ```
  - **Validator Outcome:** **Passed (`is_valid = True`, `reason = None`)**.
  - **Clinical Safety Impact:**
    The urgent escalation commands *"Do not wait"* and *"Go to clinic"* were completely omitted from the candidate response. The candidate replaced them with a 24–48h timeframe, yet passed validation because both short sentences were ignored by the `len(s_words) >= 3` guard.
- **Recommended Remediation:**
  Remove the `len(s_words) >= 3` guard or replace it with a total character check (`len(s) >= 4`). Every non-empty sentence in the approved clinical core must be accounted for in the candidate text.

---

### 2.2 Partial Content Deletion Within the 60% Recall Floor (CCP-02)
- **Mechanism of Vulnerability:**
  Because the threshold is set to $\ge 0.60$ (60% word overlap), an adapted candidate can drop up to 40% of the significant words in any sentence.
- **Empirical Reproduction:**
  ```python
  ref = "ROUTINE: Never insert herbs, roots, or substances into your vagina."
  # Candidate drops 'herbs' and 'roots', keeping 'never', 'substances', 'into', 'vagina'
  cand = "ROUTINE: I understand your question. Never insert other substances into your vagina. Feel free to check in."
  is_valid, reason = validator.validate(cand, ref, "routine", "can I use vaginal herbs?")
  ```
  - **Word Analysis:**
    `s_words` = `{'never', 'insert', 'herbs', 'roots', 'substances', 'into', 'vagina'}` (7 content words).
    Candidate contains `{'never', 'insert', 'substances', 'into', 'vagina'}` (5 content words).
    Recall = $5 / 7 = 71.4\% \ge 60\%$.
  - **Validator Outcome:** **Passed (`is_valid = True`)**.
  - **Clinical Safety Impact:**
    Specific cultural prohibitions (e.g., vaginal herbs/roots) can be diluted to general phrasing without triggering a validator failure.
- **Recommended Remediation:**
  Introduce an explicit extraction check for cultural risk tokens (e.g., herbs, concoctions, cow dung, hot water compression) when present in reference responses.

---

### 2.3 Critical Condition Marker Enforcement (CCP-03 - Verified Safe)
The dedicated marker filter in lines 309–318 enforces that if any of the following clinical warning conditions appear in the approved reference text, they **must** appear in the candidate response:
`preeclampsia`, `eclampsia`, `dehydration`, `convulsions`, `seizures`, `hemorrhage`, `gestational diabetes`, `premature labour`, `kidney`, `ectopic`, `sepsis`, `infection`, `mastitis`.
- **Empirical Test:**
  When a candidate kept sentence 1 of a preeclampsia reference but dropped sentence 2, the validator correctly rejected the response with:
  `ERR_OMITTED_WARNING: Mandatory clinical warning 'preeclampsia' was omitted from candidate`.

---

## 3. Mandatory vs. Optional Clinical Elements Classification

To eliminate ambiguity in future validator iterations, clinical reference content across the 200 conversational scenarios is classified into two distinct operational tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CLINICAL REFERENCE RESPONSE                          │
├───────────────────────────────────┬────────────────────────────────────┤
│     TIER 1: MANDATORY INVARIANTS   │     TIER 2: EXPLANATORY CORE       │
│     (100% Exact Preservation Req.) │     (Flexible Conversational Slot) │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Urgent warning signs & red flags│ • General background biology       │
│ • Referral destination (facility) │ • Normal physiological changes     │
│ • Referral timeframe (e.g. 24-48h)│ • Supportive conversational context │
│ • Explicit medication prohibitions│ • Routine wellness hygiene advice  │
│ • Specific lab follow-up tests    │                                    │
│ • Emergency contact numbers       │                                    │
└───────────────────────────────────┴────────────────────────────────────┘
```

### Recommendation for Tiered Invariant Validation
Rather than applying an undifferentiated 60% lexical recall threshold to all sentences:
1. **Tier 1 (Mandatory Elements):** Require **100% exact presence** of mandatory directives, escalation timeframes, and condition names.
2. **Tier 2 (Explanatory Sentences):** Maintain the 60% recall floor to permit empathetic conversational phrasing while ensuring semantic preservation.

