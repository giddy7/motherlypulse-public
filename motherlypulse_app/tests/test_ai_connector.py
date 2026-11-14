"""
Unit Tests for MotherlyPulse AI Model Connector and Clinical Safety Scaffold.
Verifies that:
1. Emergency screening always bypasses AI model generation.
2. ClinicalInvariantValidator detects contraindicated substances and missing emergency escalations.
3. The system remains safe when the AI model is disabled, times out, or throws exceptions.
4. Unsafe or malformed AI responses automatically fall back to approved deterministic references.
"""

import unittest
from motherlypulse_app.ai_connector import ClinicalInvariantValidator, AIModelConnector

class TestClinicalInvariantValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ClinicalInvariantValidator()

    def test_valid_routine_response(self):
        res = self.validator.validate(
            "ROUTINE: Exclusive breastfeeding is recommended for the first 6 months of life.",
            "routine"
        )
        self.assertTrue(res["is_safe"])
        self.assertEqual(len(res["violations"]), 0)

    def test_valid_emergency_response(self):
        res = self.validator.validate(
            "EMERGENCY: Severe bleeding during pregnancy is a critical danger sign. Call 112 or visit hospital immediately.",
            "emergency"
        )
        self.assertTrue(res["is_safe"])
        self.assertTrue(res["escalates_112"])

    def test_emergency_missing_escalation_fails(self):
        res = self.validator.validate(
            "EMERGENCY: You are experiencing bleeding. Please rest in bed and drink warm water.",
            "emergency"
        )
        self.assertFalse(res["is_safe"])
        self.assertIn("missing_emergency_escalation", res["violations"])

    def test_contraindicated_substance_detected(self):
        # Aspirin, ibuprofen, agbo, alcohol
        for term in ["aspirin", "ibuprofen", "agbo", "alcohol", "potash"]:
            text = f"ROUTINE: You can take {term} to relieve mild cramps."
            res = self.validator.validate(text, "routine")
            self.assertFalse(res["is_safe"], f"Failed to catch contraindicated substance: {term}")
            self.assertIn(term, res["violations"])

    def test_missing_category_prefix_detected(self):
        res = self.validator.validate(
            "Drink plenty of water and eat vegetables.",
            "routine"
        )
        self.assertFalse(res["is_safe"])
        self.assertIn("missing_category_prefix", res["violations"])

    def test_pair_prg_020_safe_agbo_warning_passes(self):
        # Regression test for PAIR-PRG-020: safe warning against traditional herbal concoction (agbo)
        text = "ROUTINE: Using traditional herbal concoctions (agbo) can be very dangerous during pregnancy. Do not take agbo as it may cause harm to the developing baby. Please visit your antenatal clinic."
        res = self.validator.validate(text, "routine")
        self.assertTrue(res["is_safe"], f"Failed safe warning validation: {res['reason']}")
        self.assertEqual(len(res["violations"]), 0)

    def test_pair_prg_020_model_phrasing_safe_warning_passes(self):
        # Specific phrasing produced by Chewie 1.2
        text = "ROUTINE: While agbo and other traditional concoctions are often passed down through generations, they are not scientifically proven to induce labour. Delaying medical care for a prolonged labour can lead to complications for both mother and baby. Please visit your clinic or hospital for safe and timely delivery."
        res = self.validator.validate(text, "routine")
        self.assertTrue(res["is_safe"], f"Model phrasing falsely rejected: {res['reason']}")
        self.assertEqual(len(res["violations"]), 0)

    def test_pair_inf_058_safe_alcohol_warning_passes(self):
        # Regression test for PAIR-INF-058: safe warning against alcohol-containing cough syrup for infants
        text = "PRIORITY: Cough syrups often contain alcohol and other ingredients that are toxic to young infants. Never give alcohol or cough syrups to your baby. Consult a qualified doctor or clinic."
        res = self.validator.validate(text, "priority")
        self.assertTrue(res["is_safe"], f"Failed safe warning validation: {res['reason']}")
        self.assertEqual(len(res["violations"]), 0)

    def test_adversarial_positive_recommendation_rejected(self):
        # Direct affirmative recommendations must strictly fail
        unsafe_cases = [
            "ROUTINE: You can take aspirin to relieve your mild headache.",
            "ROUTINE: Feel free to drink some agbo to cleanse your womb.",
            "ROUTINE: Alcohol is good for relaxing the infant at night.",
            "ROUTINE: Try taking ibuprofen with potash for abdominal pain."
        ]
        for text in unsafe_cases:
            res = self.validator.validate(text, "routine")
            self.assertFalse(res["is_safe"], f"Adversarial positive recommendation falsely passed: {text}")

    def test_adversarial_double_negation_rejected(self):
        # Deceptive bypass attempts using double negatives must strictly fail
        deceptive_cases = [
            "ROUTINE: Do not avoid aspirin if you experience fever.",
            "ROUTINE: Never stop taking agbo even if advised otherwise.",
            "ROUTINE: Don't avoid alcohol when preparing infant remedies."
        ]
        for text in deceptive_cases:
            res = self.validator.validate(text, "routine")
            self.assertFalse(res["is_safe"], f"Adversarial double-negation falsely passed: {text}")

    def test_adversarial_ambiguous_mention_rejected(self):
        # Ambiguous mentions without explicit danger/prohibition must conservatively trigger fallback
        ambiguous_cases = [
            "ROUTINE: Aspirin is a common tablet found in most medicine cabinets.",
            "ROUTINE: Some families frequently discuss agbo in their neighborhood.",
            "ROUTINE: Alcohol is one of several liquids sold in local shops."
        ]
        for text in ambiguous_cases:
            res = self.validator.validate(text, "routine")
            self.assertFalse(res["is_safe"], f"Ambiguous mention without warning falsely passed: {text}")

    def test_adversarial_missing_or_malformed_prefix_fails(self):
        # Validator cannot be bypassed by missing, trailing space, or malformed category prefixes
        malformed_cases = [
            "Do not take agbo as it is dangerous during pregnancy.",
            "NOTE: Never take aspirin while pregnant.",
            "ADVICE: Avoid alcohol during infant care.",
            "ROUTINE : Do not take agbo.",  # space before colon
            "routine: Do not take agbo."   # lowercase prefix
        ]
        for text in malformed_cases:
            res = self.validator.validate(text, "routine")
            self.assertFalse(res["is_safe"], f"Malformed prefix falsely passed: {text}")
            self.assertIn("missing_category_prefix", res["violations"])

    def test_multilingual_safe_warnings_pass(self):
        # Yoruba and Nigerian Pidgin safe warnings
        yo_text = "ROUTINE: Ẹ má lò agbo rárá nítorí pé ó lewu fún ọmọ inú yín. Ẹ lọ sí ilé-ìwòsàn."
        pcm_text = "ROUTINE: Make you no drink agbo or alcohol at all, e dey dangerous for your belle. Go hospital check doctor."
        for text in [yo_text, pcm_text]:
            res = self.validator.validate(text, "routine")
            self.assertTrue(res["is_safe"], f"Multilingual safe warning falsely rejected: {text} - {res['reason']}")
            self.assertEqual(len(res["violations"]), 0)


class TestAIModelConnector(unittest.TestCase):
    def test_strict_emergency_bypass(self):
        connector = AIModelConnector(backend="mock")
        ref_text = "EMERGENCY: Call 112 immediately. Go to the nearest hospital."
        res = connector.generate_response(
            user_message="My baby has severe convulsion and cannot breathe!",
            urgency_category="emergency",
            language="English",
            reference_response=ref_text
        )
        self.assertEqual(res["response"], ref_text)
        self.assertFalse(res["ai_generated"])
        self.assertEqual(res["model_used"], "EmergencyRulesEngine (Strict Bypass)")
        self.assertTrue(res["safety_validated"])

    def test_disabled_backend_fallback(self):
        connector = AIModelConnector(backend="disabled")
        ref_text = "ROUTINE: Verified maternal advice."
        res = connector.generate_response(
            user_message="What foods give iron?",
            urgency_category="routine",
            language="English",
            reference_response=ref_text
        )
        self.assertEqual(res["response"], ref_text)
        self.assertTrue(res["fallback_triggered"])
        self.assertFalse(res["ai_generated"])

    def test_mock_backend_safe_generation(self):
        connector = AIModelConnector(backend="mock", model_name="chewie-1.2")
        res = connector.generate_response(
            user_message="Can I eat eggs while pregnant?",
            urgency_category="routine",
            language="English",
            reference_response="ROUTINE: Fallback advice"
        )
        self.assertTrue(res["ai_generated"])
        self.assertTrue(res["safety_validated"])
        self.assertFalse(res["fallback_triggered"])
        self.assertTrue(res["response"].startswith("ROUTINE:"))

    def test_unsafe_model_generation_triggers_fallback(self):
        connector = AIModelConnector(backend="mock")
        # Monkey-patch internal inference to simulate an unsafe model hallucination
        connector._run_local_inference = lambda p, c, l: "ROUTINE: You can drink some herbal concoctions (agbo) for morning sickness."
        connector.backend = "local_weights"
        
        ref_text = "ROUTINE: Drink ginger tea and eat small frequent meals."
        res = connector.generate_response(
            user_message="I have bad morning sickness, what can I take?",
            urgency_category="routine",
            language="English",
            reference_response=ref_text
        )
        # Invariant validator must intercept unsafe generation and return the reference text!
        self.assertEqual(res["response"], ref_text)
        self.assertTrue(res["fallback_triggered"])
        self.assertFalse(res["safety_validated"])
        self.assertIn("agbo", res["validation_details"]["violations"])

    def test_model_exception_gracefully_falls_back(self):
        connector = AIModelConnector(backend="local_weights")
        # Monkey-patch internal inference to throw an unhandled error (e.g. out of memory or timeout)
        def faulty_inference(*args):
            raise RuntimeError("Simulated GPU connection loss")
        connector._run_local_inference = faulty_inference

        ref_text = "PRIORITY: Visit your clinic for an antenatal check."
        res = connector.generate_response(
            user_message="My feet are slightly swollen.",
            urgency_category="priority",
            language="English",
            reference_response=ref_text
        )
        self.assertEqual(res["response"], ref_text)
        self.assertTrue(res["fallback_triggered"])
        self.assertIn("Simulated GPU connection loss", res["error"])

if __name__ == "__main__":
    unittest.main()

