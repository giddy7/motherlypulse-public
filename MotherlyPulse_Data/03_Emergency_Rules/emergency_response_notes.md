# Emergency Response Architecture & Handling Notes

**Project:** MotherlyPulse Maternal Health Assistant  
**Version:** 1.0 (Project Scope)  
**Status:** Provisional Architecture / Pending Clinical Review  
**Date:** October 29, 2026  

---

### Core Golden Principle
> **"A suspected emergency must NEVER be delayed by questioning or conversational probing."**

In maternal and newborn triage, delays in care seeking and facility arrival are the leading contributors to mortality (the "Three Delays" framework). When an incoming message matches an emergency danger sign, the system must immediately trigger an unambiguous, actionable escalation message. It must not engage in multi-turn clarification questions, symptom questionnaires, or open-ended model generation.

---

### Handling Edge Cases & Operational Constraints

#### 1. Incomplete or Vague Information with Red-Flag Keywords
- **Scenario:** A user sends a very short or ambiguous message containing an emergency keyword, such as *"I am bleeding"*, *"baby not moving"*, or *"water break"*, without providing gestational age or additional details.
- **Protocol:** Triage on the side of maximal safety. Treat any mention of an emergency symptom as an active emergency. Do not respond with *"Can you tell me how much you are bleeding?"* or *"When did this start?"*. Immediately output the fixed emergency response instructing them to head to the nearest hospital and call emergency services.

#### 2. Uncertainty / Ambiguous Multi-Symptom Messages
- **Scenario:** A user describes multiple symptoms where one is minor (e.g., morning sickness) but another indicates potential preeclampsia or sepsis (e.g., severe throbbing headache or fever after delivery).
- **Protocol:** Hierarchical triage priority applies: `Emergency > Priority > Routine`. If an emergency symptom is present anywhere in the utterance, the rule engine overrides routine education and fires the urgent escalation protocol.

#### 3. No Shared Location Available
- **Scenario:** The user triggers an emergency rule but has not consented to or shared their GPS location or current LGA.
- **Protocol:**
  1. Immediately output the emergency danger notice emphasizing rapid clinical assessment.
  2. Provide the confirmed national emergency routing number (**112** for Nigeria's toll-free 24/7 National Emergency Communications Centre dispatch line).
  3. Advise them to proceed to their designated antenatal registration clinic or the nearest government primary or secondary hospital without delay.

#### 4. No Verified Facility Nearby or Out-of-Range Location
- **Scenario:** A user's location is resolved to an area outside the verified Akure cluster or in a rural settlement where no immediate verified facility exists in the directory.
- **Protocol:**
  - Never fabricate a placeholder facility name or estimated distance.
  - State clearly: *"We do not have a verified facility mapped in your immediate area. Please go immediately to the nearest primary health centre, general hospital, or private maternity hospital closest to you, or call 112 for urgent ambulance assistance."*

---

### Fixed Emergency Response Template (English)
```text
EMERGENCY ALERT: This is a critical medical warning sign. Please do not wait. 
Go immediately to the nearest hospital or maternity emergency centre. 
If you need urgent assistance, call the national emergency line 112 or Ondo State Emergency Medical Services on 112 / 112.
```
*(Note: Fluent speakers will adapt this exact prompt into Yoruba, Hausa, Igbo, and Nigerian Pidgin for identical fixed execution).*

