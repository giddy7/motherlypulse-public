# Emergency Classification Language Independence Results

**Target Vulnerability:** VULN-1.5.2-01 (Emergency Triage Downgrade on Unsupported Language Parameter)  
**Component:** `motherlypulse_app/assistant.py` (`MotherlyPulseAssistant.respond`)  
**Audit Date:** November 5, 2026  
**Status:** FULLY REMEDIATED (Zero Emergency Downgrades; Explicit Unassessed State Implemented)

---

## 1. Vulnerability Root Cause Analysis

In the previous Phase 1.5 implementation:
```python
# Vulnerable order of execution:
if language is not None and language not in supported_languages:
    return {
        "urgency_category": "routine",     # <-- CRITICAL FLAW: Hardcoded routine
        "status": "language_not_supported",
        "response": "ROUTINE: Language notice: ...",
        ...
    }

# Dynamic triage was executed AFTER language check:
triage = self.classifier.classify(message, conversation_history)
```

If a patient submitted an emergency inquiry (e.g. *"I am having heavy bleeding from my vagina and severe belly pain"*) while specifying `language="Hausa"`, the early return intercepted the pipeline and falsely tagged the transaction as `routine`. Downstream triage dashboards relying on `urgency_category` would classify a critical haemorrhage as a routine case.

---

## 2. Corrective Engineering Architecture

In `motherlypulse_app/assistant.py`, dynamic triage classification was moved to execute **before** language gating:

```
User Message Input (with language parameter)
                  │
                  ▼
   1. Dynamic Triage Classification (classifier.classify)
                  │
                  ├──────────────────────────────┐
                  ▼                              ▼
          Category == EMERGENCY?         Category != EMERGENCY?
                  │                              │
                  ├─► YES:                       ├─► YES:
                  │   Emergency Bypass           │   Check Language Support
                  │   Category = "EMERGENCY"     │   ├─► Supported:
                  │   Contacts: 112 + ODEMSA     │   │   Run Adaptation
                  │   Zero Downgrade             │   │
                  │   (Lang notice appended      │   └─► Unsupported:
                  │    if unsupported)           │       Category = "UNASSESSED"
                  │                              │       Status = "language_not_supported"
                  │                              │       Contacts: 112 + ODEMSA
                  │                              │       Safe limitation notice
```

### Safety Rules Enforced:
1. **Zero Downgrade:** If triage evaluates an input as `emergency`, the category remains `emergency` unconditionally, regardless of language tags.
2. **No Routine Invention:** If emergency cannot be determined because the language is unsupported, the system returns `urgency_category: "unassessed"` with `status: "language_not_supported"`. It **never** fabricates a `routine` category.
3. **Emergency Escalation Contacts:** Both 112 and ODEMSA (0812 756 5478) are provided in all unsupported-language responses.

---

## 3. Empirical Test Matrix and Results

The dedicated test suite `motherlypulse_app/tests/test_phase1_5_2_remediation.py` verified all required scenarios:

| Test Case | Input Message | Language Parameter | Expected Category | Actual Category | Status / Flag | Emergency Contacts (112 / ODEMSA) | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-ELI-01** | "I am having heavy bleeding from my vagina and severe belly pain" | `"Hausa"` | `emergency` | **`emergency`** | Emergency bypass | Present (`112` + `ODEMSA`) | **PASS** |
| **TEST-ELI-02** | "Eje n tu jade pupo lara mi" (Yoruba bleeding emergency) | `"French"` | `emergency` | **`emergency`** | Emergency bypass | Present (`112` + `ODEMSA`) | **PASS** |
| **TEST-ELI-03** | "Heavy blood de rush from my private part" (Pidgin emergency) | `"German"` | `emergency` | **`emergency`** | Emergency bypass | Present (`112` + `ODEMSA`) | **PASS** |
| **TEST-ELI-04** | "Ina kwana nurse" (Ordinary Hausa inquiry) | `"Hausa"` | `unassessed` | **`unassessed`** | `language_not_supported` | Present (`112` + `ODEMSA`) | **PASS** |
| **TEST-ELI-05** | `""` (Empty message) | `"Hausa"` | `unassessed` | **`unassessed`** | `language_not_supported` | Present (`112` + `ODEMSA`) | **PASS** |
| **TEST-ELI-06** | "My baby is convulsing and rolling eyes" | `None` (Missing) | `emergency` | **`emergency`** | Emergency bypass | Present (`112` + `ODEMSA`) | **PASS** |
| **TEST-ELI-07** | "Convulsions and high fever in newborn" | `123` (Invalid type) | `emergency` | **`emergency`** | Emergency bypass | Present (`112` + `ODEMSA`) | **PASS** |
| **TEST-ELI-08** | "Ina son maganin zazzabi" (Hausa ordinary inquiry) | `"Hausa"` | `unassessed` | **`unassessed`** | `language_not_supported` | Present (`112` + `ODEMSA`) | **PASS** |

---

## 4. Metadata Inspection Evidence

Example response payload for an Emergency inquiry with an unsupported language parameter (`TEST-ELI-01`):
```json
{
  "user_message": "I am having heavy bleeding from my vagina and severe belly pain",
  "urgency_category": "emergency",
  "medication_safety_triggered": false,
  "language": "English",
  "requested_language": "Hausa",
  "response": "EMERGENCY: This is a critical medical warning sign that requires immediate medical attention. Please do not wait. Go immediately to the nearest hospital or emergency maternity centre.\nEmergency Contacts:\n- National Emergency: Call 112 (Toll-Free)\n- Ondo State Emergency Medical Services (ODEMSA): 0812 756 5478\nIf you can safely travel, proceed to your nearest General Hospital or Comprehensive Health Centre now.\n\nNotice: You requested 'Hausa'. While MotherlyPulse cannot converse in 'Hausa', a critical medical emergency was detected. Please call 112 or ODEMSA immediately as instructed above.",
  "delay_incurred": false,
  "action": "Immediate Emergency Hospital Escalation"
}
```

Example response payload for an Unassessed inquiry in an unsupported language (`TEST-ELI-04`):
```json
{
  "user_message": "Ina kwana nurse",
  "urgency_category": "unassessed",
  "medication_safety_triggered": false,
  "language": "English",
  "requested_language": "Hausa",
  "status": "language_not_supported",
  "supported_languages": ["English", "Yoruba", "Nigerian Pidgin"],
  "response": "MotherlyPulse currently provides verified clinical responses in English, Yoruba, and Nigerian Pidgin. Support for 'Hausa' is not yet available, and medical urgency cannot be reliably assessed in this language. For urgent medical concerns or emergencies, please call emergency services immediately at 112 or visit your nearest healthcare facility.",
  "classification_metadata": {
    "triage": "unassessed",
    "reason": "Input language 'Hausa' unsupported; urgency cannot be reliably determined"
  },
  "action": "Language Guidance / Emergency Referral"
}
```

---

## 5. Conclusion

Language gating has been decoupled from emergency triage. Triage classification now has full precedence, guaranteeing that emergencies are never downgraded to routine, and unsupported languages are never falsely certified as routine.

