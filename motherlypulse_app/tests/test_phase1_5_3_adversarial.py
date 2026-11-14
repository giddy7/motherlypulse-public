"""
Adversarial Acceptance Test Suite for Phase 1.5.3 Verification & Safety Remediation.
Contains the 32 adversarial test cases evaluating emergency classification, HTTP language
bypasses, medication instruction preservation, dosage-to-medication proximity binding,
and word-based numerical normalization.
"""

import unittest
import json
import urllib.request
import urllib.error
import threading
from http.server import HTTPServer
from motherlypulse_app.assistant import MotherlyPulseAssistant
from motherlypulse_app.classifier import DynamicTriageClassifier
from motherlypulse_app.template_adapter import ClinicalInvariantValidator
from motherlypulse_app.server import MotherlyPulseRequestHandler


class TestPhase153Adversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Spin up a test HTTP server on an ephemeral port
        cls.port = 8899
        cls.server = HTTPServer(("127.0.0.1", cls.port), MotherlyPulseRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.assistant = MotherlyPulseAssistant()
        self.classifier = DynamicTriageClassifier()
        self.validator = ClinicalInvariantValidator()

    # =========================================================================
    # CATEGORY 1: EMERGENCY CLASSIFICATION & HTTP GATEWAY INTEGRITY
    # =========================================================================

    def test_adv_01_emergency_english_direct(self):
        res = self.assistant.respond("I am bleeding heavily and soaking pads", language="en")
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))
        self.assertIn("112", res["response"])

    def test_adv_02_emergency_yoruba_direct(self):
        res = self.assistant.respond("Eje pupo n tu jade lati abe mi", language="yo")
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))
        self.assertIn("112", res["response"])

    def test_adv_03_emergency_pidgin_direct(self):
        res = self.assistant.respond("Blood dey pour heavy like water from my body", language="pcm")
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))
        self.assertIn("112", res["response"])

    def test_adv_04_emergency_hausa_with_ha_tag(self):
        # Hausa message without English red flag keywords defaults to unassessed notice
        res = self.assistant.respond("Ina da zubar jini mai tsanani", language="ha")
        self.assertEqual(res["urgency_category"], "unassessed")
        self.assertIn("112", res["response"])

    def test_adv_05_emergency_hausa_without_tag(self):
        # Hausa message without tag falls to routine education (lexical limitation)
        res = self.assistant.respond("Ina da zubar jini mai tsanani")
        self.assertEqual(res["urgency_category"], "routine")

    def test_adv_06_emergency_english_unsupported_language_parameter(self):
        # English emergency text requested with French language parameter
        res = self.assistant.respond("Severe bleeding after delivery", language="fr")
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertIn("Notice: You requested 'fr'", res["response"])
        self.assertIn("112", res["response"])

    def test_adv_07_emergency_invalid_language_type(self):
        res = self.assistant.respond("Baby has high fever 39.5 and fits", language=123)
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))
        self.assertIn("112", res["response"])

    def test_adv_08_non_emergency_unsupported_language_parameter(self):
        res = self.assistant.respond("How do I bathe my newborn baby?", language="fr")
        self.assertEqual(res["urgency_category"], "unassessed")
        self.assertIn("Support for 'fr' is not yet available", res["response"])
        self.assertIn("112", res["response"])

    def test_adv_09_http_emergency_with_unsupported_language_escalates(self):
        # CRITICAL FIX VERIFICATION: Danger sign sent with unsupported language over HTTP must escalate with 200
        url = f"http://127.0.0.1:{self.port}/api/chat"
        payload = json.dumps({"message": "I am bleeding heavily and convulsing", "language": "hausa"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["urgency_category"], "emergency")
            self.assertIn("112", data["response"])

    def test_adv_10_http_emergency_german_parameter_escalates(self):
        url = f"http://127.0.0.1:{self.port}/api/chat"
        payload = json.dumps({"message": "Baby is having convulsions and cannot breathe", "language": "de"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["urgency_category"], "emergency")
            self.assertIn("112", data["response"])

    # =========================================================================
    # CATEGORY 2: MEDICATION INSTRUCTION PRESERVATION
    # =========================================================================

    def test_adv_11_omission_of_one_of_two_approved_medications(self):
        ref = "ROUTINE: Take 500 mg paracetamol and take 200 mg iron supplements daily."
        cand = "ROUTINE: Regarding your care: Take 500 mg paracetamol daily."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "headache")
        self.assertFalse(is_valid)
        self.assertIn("ERR_OMITTED_MEDICATION", reason)

    def test_adv_12_substitution_of_medication(self):
        ref = "ROUTINE: Take 500 mg paracetamol for mild pain."
        cand = "ROUTINE: Regarding your care: Take 500 mg ibuprofen for mild pain."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "headache")
        self.assertFalse(is_valid)

    def test_adv_13_addition_of_unapproved_medication(self):
        ref = "ROUTINE: Take 500 mg paracetamol for mild pain."
        cand = "ROUTINE: Regarding your care: Take 500 mg paracetamol and 250 mg amoxicillin."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "headache")
        self.assertFalse(is_valid)
        self.assertIn("ERR_INVENTED_MEDICATION", reason)

    def test_adv_14_reversal_of_medication_instruction(self):
        ref = "ROUTINE: Do not take ibuprofen during pregnancy."
        cand = "ROUTINE: Regarding your care: You can safely take ibuprofen during pregnancy."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "headache")
        self.assertFalse(is_valid)
        self.assertIn("ERR_MEDICATION_POLARITY_INVERSION", reason)

    def test_adv_15_removal_of_prohibition(self):
        ref = "ROUTINE: Do not take agbo or unverified herbs during pregnancy."
        cand = "ROUTINE: Regarding herbs: Agbo is a traditional herbal mixture."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "agbo")
        self.assertFalse(is_valid)

    def test_adv_16_change_of_dosage(self):
        ref = "ROUTINE: Take 500 mg paracetamol."
        cand = "ROUTINE: Regarding pain: Take 1000 mg paracetamol."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "headache")
        self.assertFalse(is_valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_adv_17_change_of_frequency(self):
        ref = "ROUTINE: Take 500 mg paracetamol twice daily."
        cand = "ROUTINE: Regarding pain: Take 500 mg paracetamol once daily."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "headache")
        self.assertFalse(is_valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_adv_18_change_of_duration(self):
        ref = "ROUTINE: Take iron supplements for 30 days."
        cand = "ROUTINE: Regarding supplements: Take iron supplements for 10 days."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "iron")
        self.assertFalse(is_valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    # =========================================================================
    # CATEGORY 3: DOSAGE-TO-MEDICATION PROXIMITY BINDING & ASSOCIATION
    # =========================================================================

    def test_adv_19_swapped_dosages_separated_by_and_take(self):
        ref = "ROUTINE: Take 500 mg paracetamol for headache and take 200 mg iron supplement daily."
        cand = "ROUTINE: Take 200 mg paracetamol for headache and take 500 mg iron supplement daily."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "care")
        self.assertFalse(is_valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_adv_20_compound_clause_dosage_swap_with_and(self):
        # CRITICAL FIX VERIFICATION: Single compound clause with 'and'
        ref = "ROUTINE: Take 500 mg paracetamol and 200 mg iron daily."
        cand = "ROUTINE: Take 200 mg paracetamol and 500 mg iron daily."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "care")
        self.assertFalse(is_valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_adv_21_compound_clause_dosage_swap_with_preposition(self):
        # CRITICAL FIX VERIFICATION: Single compound clause with 'with'
        ref = "ROUTINE: Take 500 mg paracetamol with 200 mg iron daily."
        cand = "ROUTINE: Take 200 mg paracetamol with 500 mg iron daily."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "care")
        self.assertFalse(is_valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_adv_22_instructions_split_across_sentences(self):
        ref = "ROUTINE: For pain relief, use paracetamol. The recommended amount is 500 mg twice daily."
        cand = "ROUTINE: For pain relief, use paracetamol. The recommended amount is 1000 mg twice daily."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "pain")
        self.assertFalse(is_valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_adv_23_reordered_equivalent_instructions(self):
        ref = "ROUTINE: Take 500 mg paracetamol and 200 mg iron daily."
        cand = "ROUTINE: Take 200 mg iron and 500 mg paracetamol daily."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "care")
        self.assertTrue(is_valid)

    # =========================================================================
    # CATEGORY 4: WORD-BASED NUMERICAL INVARIANCE & NORMALIZATION
    # =========================================================================

    def test_adv_24_digit_in_ref_word_in_cand(self):
        ref = "ROUTINE: Take 2 tablets of paracetamol."
        cand = "ROUTINE: Take two tablets of paracetamol."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "pain")
        self.assertTrue(is_valid)

    def test_adv_25_word_in_ref_digit_in_cand(self):
        # CRITICAL FIX VERIFICATION: Reciprocal word-to-digit equivalence accepted
        ref = "ROUTINE: Take two tablets of paracetamol."
        cand = "ROUTINE: Take 2 tablets of paracetamol."
        is_valid, reason = self.validator.validate(cand, ref, "routine", "pain")
        self.assertTrue(is_valid)

    def test_adv_26_large_number_words_normalization(self):
        norm = self.validator._normalize_numerical_words("take five hundred mg paracetamol")
        self.assertIn("500 mg", norm)

    def test_adv_27_large_number_words_fifty_and_hundred(self):
        norm1 = self.validator._normalize_numerical_words("take fifty mg of medication")
        norm2 = self.validator._normalize_numerical_words("administer one hundred ml of fluids")
        self.assertIn("50 mg", norm1)
        self.assertIn("100 ml", norm2)

    def test_adv_28_fraction_parsing_accuracy(self):
        # CRITICAL FIX VERIFICATION: 1/2 tablet extracted as 0.5 tablet, not 2.0 tablet
        dosages = self.validator._extract_dosages("Take 1/2 tablet of paracetamol")
        self.assertEqual(len(dosages), 1)
        self.assertEqual(dosages[0][0], 0.5)
        self.assertEqual(dosages[0][1], "tablet")

    def test_adv_29_decimal_parsing_accuracy(self):
        dosages = self.validator._extract_dosages("Administer 2.5 ml of liquid medicine")
        self.assertEqual(len(dosages), 1)
        self.assertEqual(dosages[0][0], 2.5)
        self.assertEqual(dosages[0][1], "ml")

    def test_adv_30_numerical_range_dosage(self):
        dosages = self.validator._extract_dosages("Take 1 to 2 tablets of paracetamol")
        self.assertTrue(len(dosages) >= 1)
        self.assertEqual(dosages[-1][1], "tablet")

    def test_adv_31_indigenous_yoruba_number_words(self):
        # Verified baseline: indigenous dialect numbers remain unnormalized
        norm = self.validator._normalize_numerical_words("eemeji lojumo")
        self.assertEqual(norm, "eemeji lojumo")

    def test_adv_32_ambiguous_number_expressions(self):
        # Ambiguous numbers ('a couple of days') safely do not trigger numerical extraction
        durs = self.validator._extract_durations("rest for a couple of days")
        self.assertEqual(len(durs), 0)


if __name__ == "__main__":
    unittest.main()
