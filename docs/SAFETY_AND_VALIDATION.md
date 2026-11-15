# Safety & Clinical Validation Architecture

## 1. Deterministic Emergency Preemption

Before any AI model is invoked, `DynamicTriageClassifier` (`motherlypulse_app/classifier.py`) scans incoming messages using curated multilingual keywords and fuzzy regex rules across English, Yoruba, and Nigerian Pidgin:
- **Emergency triggers** (e.g., severe vaginal bleeding, convulsions/eclampsia, unconsciousness, neonatal fever/difficulty breathing) immediately return an approved deterministic emergency template instructing the user to call **Nigeria National Emergency Number `112`** and go to the nearest hospital.
- `AIModelConnector.generate_response()` and `compare_models()` also enforce an internal `if cat_clean == "emergency"` bypass (`motherlypulse_app/ai_connector.py`), ensuring generative models are never relied upon for acute emergencies.

## 2. `ClinicalInvariantValidator`

All non-emergency (`PRIORITY` / `ROUTINE`) neural outputs are screened locally by `ClinicalInvariantValidator` before reaching the user:
1. **Strict Category Prefix:** Output must begin with `EMERGENCY:`, `PRIORITY:`, or `ROUTINE:`.
2. **Contraindicated Substance Gate:** Screens for dangerous recommendations in pregnancy/infancy (`aspirin`, `ibuprofen`, `advil`, `motrin`, `gin`, `alcohol`, `ogogoro`, `concoction`, `kaun`, `potash`, `agbo`, `herbal mixture`, `tetracycline`).
3. **Negation & Bypass Awareness (`_is_safe_clause`):** Distinguishes explicit warnings (*"do not take aspirin"*, *"ẹ má lo agbo"*, *"no drink agbo"*) from affirmative recommendations or double-negation bypasses (*"do not avoid..."*). Ambiguous mentions are conservatively rejected.
4. **Emergency Escalation Check:** For `Emergency`-labeled validations, verifies presence of `112` / hospital / urgent escalation terms in the response body (stripping the `EMERGENCY:` prefix first).

## 3. Graceful Deterministic Fallback

If `AI_MODEL_BACKEND=disabled`, `AI_MODEL_ENDPOINT` is unreachable/times out, or `ClinicalInvariantValidator` rejects a model output, `AIModelConnector` automatically returns the approved `DeterministicReference` passage from `MotherlyPulse_Data`.

## 4. Known Safety Limitations

- In held-out testing, Yoruba (`yo`) Emergency `112` escalation without the deterministic bypass scored `68.89%` (`11` missed escalations in both baseline and fine-tuned, plus `3` regressions), reinforcing why the deterministic `EmergencyRulesEngine` bypass must remain mandatory.
- Automated invariant checks do not substitute for formal clinical board review and native-speaker Yoruba/Pidgin evaluation.

