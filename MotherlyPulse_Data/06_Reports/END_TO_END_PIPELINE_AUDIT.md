# MotherlyPulse: End-to-End Pipeline Audit
**Phase 1.5 Independent Acceptance Audit: Execution Traces & Entry Point Verification**

**Audit Date:** November 4, 2026  
**Auditor:** Senior Machine Learning Infrastructure Engineer & Python Backend Auditor  
**Modules Audited:** [`assistant.py`](motherlypulse_app/assistant.py), [`cli.py`](motherlypulse_app/cli.py), [`server.py`](motherlypulse_app/server.py), [`template_adapter.py`](motherlypulse_app/template_adapter.py)

---

## 1. End-to-End Response Trace

The diagram below traces an incoming message from the client entry point to the final delivered response:

```
[User Message: CLI or HTTP POST /api/chat]
                 │
                 ▼
[1. Language Determination]
   • Default: "English"
   • Limitation: server.py ignores client JSON "language" field
   • assistant.py has no runtime automatic language detector
                 │
                 ▼
[2. Triage Classification: DynamicTriageClassifier.classify()]
   • Normalizes text (Unicode NFKD decomposed)
   • Evaluates medication safety decline patterns
   • Evaluates Emergency regex patterns (no negation check)
   • Evaluates Priority regex patterns
   • Default: Routine
                 │
                 ├───────────────────────────────┐
                 │ (EMERGENCY)                   │ (PRIORITY / ROUTINE)
                 ▼                               ▼
    [Emergency Bypass]              [3. Reference Selection]
      • Zero adaptation                • Matched passage or fallback template
      • Zero question marks            • Enforces category prefix
      • Direct 112 / ODEMSA                      │
      • Invariant validation bypassed            ▼
      • Guaranteed < 0.05 ms         [4. Symptom Extraction: extract_symptom()]
                 │                     • Language-scoped lexicon (EN, YO, PCM)
                 │                     • Clause-bounded negation check
                 │                     • Denied symptoms return None
                 │                               │
                 │                               ▼
                 │                   [5. Template Adaptation: adapt_response()]
                 │                     • Detects domain (pregnancy vs infant)
                 │                     • Slot 1: Domain-aware empathy
                 │                     • Slot 2: Mirroring (omitted for greetings)
                 │                     • Slot 3: Approved Clinical Core
                 │                     • Slot 4: Action / Referral (deduplicated)
                 │                               │
                 │                               ▼
                 │                   [6. Clinical Invariant Validation]
                 │                     • Prefix check
                 │                     • Drug negative tokens & polarity check
                 │                     • Critical condition markers check
                 │                     • Multi-sentence 60% recall check
                 │                     • Word-boundary referral check
                 │                               │
                 │                       ┌───────┴───────┐
                 │                   [Passed]        [Failed]
                 │                       │               │
                 │                       ▼               ▼
                 │               Adapted 4-Slot    Fallback to Original
                 │                  Candidate        Base Reply
                 │                       │               │
                 └───────────────────────┴───────────────┘
                                         │
                                         ▼
                               [7. Final Structured Response]
```

---

## 2. Production Entry Point Verification

### 2.1 HTTP API Server ([`motherlypulse_app/server.py`](motherlypulse_app/server.py))
- **Active Route:** `POST /api/chat` (lines 37–73).
- **Audit Findings:**
  1. **Ignored Language Parameter (Severity: HIGH):**
     Line 49 parses incoming JSON: `data = json.loads(body)`.
     Lines 57–58 extract: `message = data.get("message")`, `history = data.get("history")`.
     The server **completely fails to extract or set the language parameter** (`data.get("language")`)!
     Because `self.assistant = MotherlyPulseAssistant()` is instantiated with the default `"English"` at the module level (line 16), any HTTP request in Yoruba or Pidgin is processed using English phrase banks and templates unless code is altered.
  2. **Hardcoded Health Metadata (Severity: MEDIUM):**
     Line 27 in `/health` advertises `"supported_languages": ["English"]`, failing to reflect the application's true multilingual capabilities in Yoruba and Nigerian Pidgin.

### 2.2 Interactive Testing CLI ([`motherlypulse_app/cli.py`](motherlypulse_app/cli.py))
- **Execution Flow:**
  Instantiates `assistant = MotherlyPulseAssistant()` (English default) and loops over `assistant.respond(user_input, conversation_history=history)`.
- **Audit Findings:**
  The CLI runs identically through the validated pipeline. However, like `server.py`, it provides no user command (e.g., `/lang yoruba`) to switch languages interactively.

---

## 3. Pipeline Vulnerabilities & Edge Case Behaviors

### Pipeline Finding E2E-01: Uncaught Exceptions During Adaptation Crash Pipeline (HIGH)
- **Affected Code:** [`assistant.py`](motherlypulse_app/assistant.py#L171-L177, L199-L205, L236-L242)
  ```python
  if self.enable_adaptation:
      adapt_res = self.adapter.adapt_response(
          user_message=message,
          reference_response=base_reply,
          urgency_category="priority",
          language=self.language
      )
  ```
- **Mechanism:**
  There is **no `try...except` wrapper** around `self.adapter.adapt_response()`.
  If an unexpected runtime error occurs inside the adaptation engine (e.g., unexpected regex compilation failure, character encoding error, or memory exhaustion), the exception propagates unhandled, terminating the CLI session or returning HTTP 500 in `server.py`.
- **Audit Impact:**
  While it ensures that technical failures *never silently become routine reassurance* (satisfying safety criteria), in production an unhandled exception should be caught and should automatically fall back to `base_reply` with an error log.

### Pipeline Finding E2E-02: Absence of Invariant Validation on Emergency Bypass (LOW - BY DESIGN)
- **Mechanism:**
  Emergency messages immediately return `self.emergency_templates` (lines 133–153 of `assistant.py`) and do **not** invoke `self.validator.validate()`.
- **Audit Assessment:**
  This is an intentional architectural bypass to guarantee sub-millisecond emergency dispatch (< 0.05 ms) and prevent any runtime validation failure from blocking life-critical emergency contacts. Because the emergency templates are static, immutable, pre-approved strings containing official numbers (112, ODEMSA 0812 756 5478), this bypass is clinically safe and operationally justified.

### Pipeline Finding E2E-03: Silent Default on Unsupported / Empty Inputs (MEDIUM)
- **Mechanism:**
  When input is empty (`""`), whitespace (`"   "`), or an unsupported language (e.g. French *"Bonjour, j'ai de la fièvre"*):
  1. `classifier.classify()` matches no emergency/priority patterns and defaults to `ROUTINE`.
  2. `assistant.respond()` delivers standard routine educational advice in English:
     *"ROUTINE: Attending routine checkups and practicing healthy nutrition and care routines support you and your baby..."*
- **Audit Impact:**
  Non-English or malformed queries do not receive an error or clarification prompt; they receive ungrounded routine English prenatal advice.

