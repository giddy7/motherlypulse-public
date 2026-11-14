"""
MotherlyPulse Phase 1 Remediation: Comprehensive Clinical Invariant & Quality Regression Suite
Verifies all 6 documented audit remediations and 2 conversational refinements:
1. Language-scoped symptom lexicons (isolation of English, Yoruba, Nigerian Pidgin; no cross-language overwrites).
2. Negation-aware symptom extraction (denied symptoms are never mirrored affirmatively).
3. Multi-sentence clinical core preservation (all sentences and critical warning markers enforced).
4. Medication polarity verification (reversing prohibition to permission is strictly detected and rejected).
5. Unlisted dangerous obstetric drugs & controlled analgesics detection (misoprostol, tramadol, etc.).
6. Word-boundary anchored referral and timeframe validation (rejects 'clinical evaluation' without facility).
7. Domain-aware phrase selection (pregnancy vs infant care; eliminates improper prenatal greetings).
8. Conversational refinements (referral deduplication and natural greeting handling).
"""

import unittest
from motherlypulse_app.template_adapter import (
    TemplateAdaptationEngine,
    ClinicalInvariantValidator,
    PHRASE_BANKS,
    LANGUAGE_SCOPED_SYMPTOM_LEXICONS
)
from motherlypulse_app.assistant import MotherlyPulseAssistant


class TestAuditClinicalInvariants(unittest.TestCase):
    def setUp(self):
        self.engine = TemplateAdaptationEngine()
        self.validator = ClinicalInvariantValidator()
        self.assistant = MotherlyPulseAssistant(language="English", enable_adaptation=True)

    # -------------------------------------------------------------------------
    # 1. Language-Specific Symptom Lexicons & Key Scoping Isolation
    # -------------------------------------------------------------------------
    def test_lexicon_cross_language_key_isolation(self):
        """
        Verifies that language-specific lexicons are completely isolated.
        Shared words like 'tired' in English must return English descriptions ('feeling tired'),
        while in Nigerian Pidgin they return Pidgin descriptions ('how your body de weak').
        """
        msg_en = "I am very tired today."
        sym_en = self.engine.extract_symptom(msg_en, language="English")
        self.assertEqual(sym_en, "feeling tired")

        msg_pcm = "I de very tired today."
        sym_pcm = self.engine.extract_symptom(msg_pcm, language="Nigerian Pidgin")
        self.assertEqual(sym_pcm, "how your body de weak")

        # Verify English adaptation never contains Pidgin phrasing
        res = self.engine.adapt_response(
            "I am feeling tired.",
            "ROUTINE: Make sure you get at least 8 hours of sleep and rest during the day.",
            "routine",
            language="English"
        )
        self.assertNotIn("de weak", res["adapted_response"])
        self.assertIn("feeling tired", res["adapted_response"])

    def test_symptom_expansion_elimination(self):
        """
        Verifies that symptom extraction does not invent or expand symptoms
        (e.g., 'vomiting' should map to 'vomiting', NOT 'vomiting and nausea').
        """
        msg = "I have vomiting."
        sym = self.engine.extract_symptom(msg, language="English")
        self.assertEqual(sym, "vomiting")
        self.assertNotIn("nausea", sym)

    # -------------------------------------------------------------------------
    # 2. Negation-Aware Symptom Extraction
    # -------------------------------------------------------------------------
    def test_negated_symptom_expressions(self):
        """
        Tests the 6 mandatory negation test expressions:
        - 'I do not have fever.' -> denied
        - 'I am not vomiting.' -> denied
        - 'I haven't experienced fever since yesterday.' -> denied
        - 'I am no longer vomiting.' -> denied
        - 'No headache or dizziness.' -> both denied
        - 'I have fever but no vomiting.' -> fever affirmed, vomiting denied
        """
        # 1. "I do not have fever."
        self.assertIsNone(self.engine.extract_symptom("I do not have fever.", "English"))

        # 2. "I am not vomiting."
        self.assertIsNone(self.engine.extract_symptom("I am not vomiting.", "English"))

        # 3. "I haven't experienced fever since yesterday."
        self.assertIsNone(self.engine.extract_symptom("I haven't experienced fever since yesterday.", "English"))

        # 4. "I am no longer vomiting."
        self.assertIsNone(self.engine.extract_symptom("I am no longer vomiting.", "English"))

        # 5. "No headache or dizziness."
        self.assertIsNone(self.engine.extract_symptom("No headache or dizziness.", "English"))

        # 6. "I have fever but no vomiting."
        sym = self.engine.extract_symptom("I have fever but no vomiting.", "English")
        self.assertEqual(sym, "fever")

    def test_multilingual_negations(self):
        """
        Tests negation recognition in Yoruba and Nigerian Pidgin.
        """
        # Yoruba: "Emi ko ni iba."
        self.assertIsNone(self.engine.extract_symptom("Emi ko ni iba.", "Yoruba"))

        # Yoruba: "Ko si ebi."
        self.assertIsNone(self.engine.extract_symptom("Ko si ebi.", "Yoruba"))

        # Pidgin: "I no get fever."
        self.assertIsNone(self.engine.extract_symptom("I no get fever.", "Nigerian Pidgin"))

        # Pidgin: "I no de vomit."
        self.assertIsNone(self.engine.extract_symptom("I no de vomit.", "Nigerian Pidgin"))

        # Pidgin mixed: "I get belly pain but I no de vomit."
        sym = self.engine.extract_symptom("I get belly pain but I no de vomit.", "Nigerian Pidgin")
        self.assertEqual(sym, "belly pain")

    # -------------------------------------------------------------------------
    # 3. Multi-Sentence Clinical Core Invariance
    # -------------------------------------------------------------------------
    def test_multi_sentence_warning_preservation(self):
        """
        Verifies that dropping sentences or warning clauses from multi-sentence reference
        responses is detected and rejected.
        """
        ref_text = (
            "PRIORITY: Swelling in the feet is common during late pregnancy. "
            "However, sudden severe swelling accompanied by high blood pressure or headache is a dangerous sign of preeclampsia. "
            "You must visit your primary health centre immediately."
        )
        # Candidate keeps sentence 1, but drops sentence 2 and 3
        mutated_cand = (
            "PRIORITY: I hear your concern. Regarding what you shared about swelling: "
            "Swelling in the feet is common during late pregnancy. "
            "Please consult your healthcare provider or visit your primary health centre within 24 to 48 hours for proper clinical assessment."
        )
        is_valid, reason = self.validator.validate(
            candidate_response=mutated_cand,
            reference_response=ref_text,
            urgency_category="priority",
            user_message="My feet are swollen"
        )
        self.assertFalse(is_valid)
        self.assertTrue(
            "ERR_OMITTED_WARNING" in reason or "ERR_CLINICAL_CORE_MUTATED" in reason,
            f"Expected warning or core mutation error, got: {reason}"
        )

    # -------------------------------------------------------------------------
    # 4. Medication Polarity Inversion
    # -------------------------------------------------------------------------
    def test_medication_negation_inversion_rejection(self):
        """
        Verifies that inverting a reference prohibition (e.g., 'Do not take ibuprofen')
        into permission (e.g., 'You can safely take ibuprofen') is detected and rejected.
        """
        ref_text = (
            "ROUTINE: Taking unverified medicines can harm both you and your baby. "
            "Do not take ibuprofen under any circumstance."
        )
        cand_inverted = (
            "ROUTINE: Taking unverified medicines can harm both you and your baby. "
            "You can safely take ibuprofen under any circumstance."
        )
        is_valid, reason = self.validator.validate(
            candidate_response=cand_inverted,
            reference_response=ref_text,
            urgency_category="routine",
            user_message="Can I take medicine for headache?"
        )
        self.assertFalse(is_valid)
        self.assertIn("ERR_MEDICATION_POLARITY_INVERSION", reason)

    # -------------------------------------------------------------------------
    # 5. Unlisted Dangerous Drugs Screening
    # -------------------------------------------------------------------------
    def test_unlisted_high_risk_drug_screening(self):
        """
        Verifies detection and rejection of dangerous obstetric/controlled drugs
        (misoprostol, tramadol, codeine) added to candidate responses.
        """
        ref_text = "ROUTINE: Ensure you drink warm water, rest adequately, and eat small frequent meals."
        cand_dangerous = (
            "ROUTINE: Ensure you drink warm water, rest adequately, and eat small frequent meals. "
            "Take misoprostol and tramadol to relieve pain."
        )
        is_valid, reason = self.validator.validate(
            candidate_response=cand_dangerous,
            reference_response=ref_text,
            urgency_category="routine",
            user_message="I have abdominal pain"
        )
        self.assertFalse(is_valid)
        self.assertIn("ERR_INVENTED_MEDICATION", reason)

    # -------------------------------------------------------------------------
    # 6. Referral Word-Boundary & Timeframe Validation
    # -------------------------------------------------------------------------
    def test_referral_substring_leak_prevention(self):
        """
        Verifies that 'clinical evaluation' does NOT falsely satisfy physical facility referral.
        """
        ref_text = "PRIORITY: Painful urination is a serious sign of urinary tract infection."
        cand_with_clinical_only = (
            "PRIORITY: Painful urination is a serious sign of urinary tract infection. "
            "This requires clinical evaluation at home within 24 hours."
        )
        is_valid, reason = self.validator.validate(
            candidate_response=cand_with_clinical_only,
            reference_response=ref_text,
            urgency_category="priority",
            user_message="I have burning urination"
        )
        self.assertFalse(is_valid)
        self.assertIn("ERR_WEAKENED_REFERRAL", reason)

    def test_referral_timeframe_enforcement(self):
        """
        Verifies that priority responses omitting referral timeframes are rejected.
        """
        ref_text = "PRIORITY: Painful urination is a serious sign of infection. Visit your primary health centre."
        cand_no_timeframe = (
            "PRIORITY: Painful urination is a serious sign of infection. "
            "Visit your primary health centre whenever convenient."
        )
        is_valid, reason = self.validator.validate(
            candidate_response=cand_no_timeframe,
            reference_response=ref_text,
            urgency_category="priority",
            user_message="I have burning urination"
        )
        self.assertFalse(is_valid)
        self.assertIn("ERR_WEAKENED_REFERRAL", reason)

    # -------------------------------------------------------------------------
    # 7. Domain-Aware Phrase Selection (Pregnancy vs Infant Care)
    # -------------------------------------------------------------------------
    def test_domain_aware_yoruba_greetings(self):
        """
        Verifies that Yoruba prenatal greeting 'Ẹ ku oju lona ọmọ mà' is NEVER
        delivered to infant-care inquiries.
        """
        # Infant care inquiry
        infant_msg = "Mo fẹ mọ nipa abẹrẹ ajesara ọmọ mi ti o jẹ ọsẹ mẹfa."
        infant_ref = "ROUTINE: Abẹrẹ ajesara ọsẹ mẹfa ṣe pataki pupọ fun aabo ọmọ yin lodi si aisan."
        res_infant = self.engine.adapt_response(infant_msg, infant_ref, "routine", language="Yoruba")

        self.assertNotIn("Ẹ ku oju lona ọmọ", res_infant["adapted_response"])
        self.assertTrue(
            "ẹ ku itọju ọmọ" in res_infant["adapted_response"] or
            "ibeere pataki lẹ bi yii" in res_infant["adapted_response"] or
            "ọrọ to wọpọ" in res_infant["adapted_response"]
        )

    def test_pidgin_honorific_correction(self):
        """
        Verifies that the Nigerian Pidgin priority phrase bank uses 'Pele my sister'
        instead of Yoruba 'Epele'.
        """
        pbank = PHRASE_BANKS["Nigerian Pidgin"]
        self.assertNotIn("Epele", pbank["empathy_priority"][2])
        self.assertIn("Pele my sister", pbank["empathy_priority"][2])

    # -------------------------------------------------------------------------
    # 8. Conversational Refinements: Deduplication & Generic Greetings
    # -------------------------------------------------------------------------
    def test_referral_deduplication_in_priority(self):
        """
        Verifies that when a reference response already contains a facility referral,
        Slot 4 does not duplicate the referral sentence verbatim.
        """
        prio_ref = (
            "PRIORITY: A fasting blood sugar level of 105 mg/dL is elevated. "
            "Please visit your antenatal care provider within 24 to 48 hours for clinical evaluation."
        )
        user_msg = "My fasting blood sugar was 105 mg/dL."
        res = self.engine.adapt_response(user_msg, prio_ref, "priority", language="English")

        adapted = res["adapted_response"]
        # Must not repeat 'within 24 to 48 hours' twice
        self.assertEqual(adapted.count("within 24 to 48 hours"), 1)
        self.assertIn("follow through with this clinical visit promptly", adapted)

    def test_generic_greeting_handling(self):
        """
        Verifies that general greetings ('Hello nurse') do not produce awkward
        Slot 2 framing ('Regarding the question you shared: Hello!').
        """
        user_msg = "Hello nurse, I have a question about my pregnancy."
        ref_text = "ROUTINE: Hello! I am here to assist you with guidance on pregnancy and baby care. How can I help you today?"
        res = self.engine.adapt_response(user_msg, ref_text, "routine", language="English")

        self.assertNotIn("Regarding the question you shared:", res["adapted_response"])
        self.assertTrue(res["adapted_response"].startswith("ROUTINE:"))
        self.assertIn("Hello! I am here to assist you", res["adapted_response"])

    # -------------------------------------------------------------------------
    # 9. Emergency Bypass Directness
    # -------------------------------------------------------------------------
    def test_emergency_bypass_guarantees(self):
        """
        Verifies that emergency responses strictly bypass conversational scaffolding,
        preserve contacts, and contain zero question marks.
        """
        emerg_msg = "I am bleeding heavily and feeling dizzy."
        res = self.assistant.respond(emerg_msg)

        self.assertEqual(res["urgency_category"], "emergency")
        self.assertFalse(res["adaptation_metadata"]["adaptation_applied"])
        self.assertIn("EMERGENCY:", res["response"])
        self.assertIn("112", res["response"])
        self.assertIn("0812 756 5478", res["response"])
        self.assertNotIn("?", res["response"])


if __name__ == "__main__":
    unittest.main()
