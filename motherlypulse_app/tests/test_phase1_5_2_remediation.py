"""
Unit, Integration, and Adversarial Regression Tests for MotherlyPulse Phase 1.5.2 Remediation.
Covers:
1. Emergency Classification Independence of Language Support (No downgrade, unassessed state).
2. Medication Instruction Omission Detection (Drug, dosage, frequency, duration, prohibition).
3. Dosage-to-Medication Instruction Association (Anti-cross-swapping invariance).
4. Word-Based Numerical Normalization & Invariance.
"""

import unittest
from motherlypulse_app.assistant import MotherlyPulseAssistant
from motherlypulse_app.template_adapter import ClinicalInvariantValidator, TemplateAdaptationEngine


class TestPhase152Remediation(unittest.TestCase):
    def setUp(self):
        self.assistant = MotherlyPulseAssistant()
        self.validator = ClinicalInvariantValidator()
        self.engine = TemplateAdaptationEngine()

    # =========================================================================
    # 1. EMERGENCY CLASSIFICATION INDEPENDENCE OF LANGUAGE SUPPORT
    # =========================================================================
    def test_english_emergency_with_unsupported_language_parameter(self):
        # Heavy bleeding is critical emergency; requesting Hausa must NOT downgrade to routine
        res = self.assistant.respond("I am having heavy bleeding from my vagina and severe belly pain", language="Hausa")
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))
        self.assertIn("112", res["response"])
        self.assertIn("ODEMSA", res["response"])
        self.assertIn("Hausa", res["response"])

    def test_yoruba_emergency_with_unsupported_language_parameter(self):
        # Yoruba emergency: eje n tu jade (heavy vaginal bleeding)
        res = self.assistant.respond("Eje n tu jade pupo lara mi", language="French")
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))
        self.assertIn("112", res["response"])

    def test_pidgin_emergency_with_unsupported_language_parameter(self):
        # Pidgin emergency: blood de rush well well
        res = self.assistant.respond("Heavy blood de rush from my private part", language="German")
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))
        self.assertIn("112", res["response"])

    def test_unsupported_language_ordinary_query_not_classified_as_routine(self):
        # Non-emergency message with unsupported language MUST NOT report 'routine'
        res = self.assistant.respond("Ina kwana nurse", language="Hausa")
        self.assertEqual(res["urgency_category"], "unassessed")
        self.assertEqual(res["status"], "language_not_supported")
        self.assertFalse(res["response"].startswith("ROUTINE:"))
        self.assertIn("112", res["response"])
        self.assertIn("Support for 'Hausa' is not yet available", res["response"])

    def test_empty_input_with_unsupported_language(self):
        # Empty input with unsupported language reports unassessed limitation notice
        res = self.assistant.respond("", language="Hausa")
        self.assertEqual(res["urgency_category"], "unassessed")
        self.assertEqual(res["status"], "language_not_supported")
        self.assertFalse(res["response"].startswith("ROUTINE:"))

    def test_emergency_message_with_missing_language(self):
        # Missing language parameter defaults to configured language and preserves emergency
        res = self.assistant.respond("My baby is convulsing and rolling eyes", language=None)
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))

    def test_emergency_message_with_invalid_language_type(self):
        # Integer language type (123) handled safely without downgrading emergency
        res = self.assistant.respond("Convulsions and high fever in newborn", language=123)
        self.assertEqual(res["urgency_category"], "emergency")
        self.assertTrue(res["response"].startswith("EMERGENCY:"))

    # =========================================================================
    # 2. MEDICATION INSTRUCTION OMISSION DETECTION
    # =========================================================================
    def test_single_medication_omitted_rejected(self):
        ref = "ROUTINE: You may take paracetamol if authorized by your midwife. Attend clinic as advised."
        cand = "ROUTINE: You may take pain relief if authorized by your midwife. Attend clinic as advised."
        valid, reason = self.validator.validate(cand, ref, "routine", "headache")
        self.assertFalse(valid)
        self.assertIn("ERR_OMITTED_MEDICATION", reason)
        self.assertIn("paracetamol", reason)

    def test_one_of_two_medications_omitted_rejected(self):
        ref = "ROUTINE: Take 500mg paracetamol for headache and take 200mg iron supplement daily."
        cand = "ROUTINE: Take 500mg paracetamol for headache daily. Attend clinic as advised."
        valid, reason = self.validator.validate(cand, ref, "routine", "meds")
        self.assertFalse(valid)
        self.assertIn("ERR_OMITTED_MEDICATION", reason)
        self.assertIn("iron", reason)

    def test_medication_retained_but_dosage_omitted_rejected(self):
        ref = "ROUTINE: Take 500mg paracetamol for fever. Attend clinic as advised."
        cand = "ROUTINE: Take paracetamol for fever. Attend clinic as advised."
        valid, reason = self.validator.validate(cand, ref, "routine", "fever")
        self.assertFalse(valid)
        self.assertIn("ERR_OMITTED_DOSAGE", reason)
        self.assertIn("paracetamol", reason)

    def test_medication_retained_but_frequency_omitted_rejected(self):
        ref = "ROUTINE: Take iron supplement once daily with water. Attend clinic."
        cand = "ROUTINE: Take iron supplement with water. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "vitamins")
        self.assertFalse(valid)
        self.assertIn("ERR_OMITTED_FREQUENCY", reason)
        self.assertIn("iron", reason)

    def test_medication_retained_but_prohibition_removed_rejected(self):
        ref = "ROUTINE: Do not take ibuprofen during pregnancy. Consult your midwife."
        cand = "ROUTINE: Regarding ibuprofen, consult your midwife."
        valid, reason = self.validator.validate(cand, ref, "routine", "pain")
        self.assertFalse(valid)
        self.assertIn("ERR_MEDICATION_POLARITY_INVERSION", reason)

    def test_two_medications_reordered_meaning_preserved_accepted(self):
        ref = "ROUTINE: Take 500mg paracetamol for headache and take 200mg iron supplement daily. Attend clinic."
        cand = "ROUTINE: Take 200mg iron supplement daily and take 500mg paracetamol for headache. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "meds")
        self.assertTrue(valid)

    # =========================================================================
    # 3. DOSAGE-TO-MEDICATION INSTRUCTION ASSOCIATION
    # =========================================================================
    def test_swapped_dosages_between_two_medications_rejected(self):
        # 500mg was for paracetamol, 200mg for iron. Swapping must fail!
        ref = "ROUTINE: Take 500mg paracetamol for headache and take 200mg iron supplement daily. Attend clinic."
        cand = "ROUTINE: Take 200mg paracetamol for headache and take 500mg iron supplement daily. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "meds")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)
        self.assertIn("paracetamol", reason)

    def test_swapped_frequencies_between_two_medications_rejected(self):
        ref = "ROUTINE: Take paracetamol once daily and take iron supplement twice daily. Attend clinic."
        cand = "ROUTINE: Take paracetamol twice daily and take iron supplement once daily. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "meds")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)
        self.assertIn("paracetamol", reason)

    def test_swapped_durations_between_two_medications_rejected(self):
        ref = "ROUTINE: Take ampicillin for 7 days and take paracetamol for 3 days. Attend clinic."
        cand = "ROUTINE: Take ampicillin for 3 days and take paracetamol for 7 days. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "meds")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_medication_name_omitted_while_dosage_remains_rejected(self):
        ref = "ROUTINE: Take 500mg paracetamol if authorized by doctor."
        cand = "ROUTINE: Take 500mg if authorized by doctor."
        valid, reason = self.validator.validate(cand, ref, "routine", "pain")
        self.assertFalse(valid)
        self.assertIn("ERR_OMITTED_MEDICATION", reason)

    # =========================================================================
    # 4. WORD-BASED NUMERICAL INVARIANCE
    # =========================================================================
    def test_word_number_duration_three_to_seven_days_rejected(self):
        ref = "PRIORITY: Continue prescribed care for three days. Consult doctor within 24 hours."
        cand = "PRIORITY: Continue prescribed care for seven days. Consult doctor within 24 hours."
        valid, reason = self.validator.validate(cand, ref, "priority", "care")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_word_number_dosage_two_to_four_tablets_rejected(self):
        ref = "ROUTINE: Take two tablets of paracetamol if advised. Attend clinic."
        cand = "ROUTINE: Take four tablets of paracetamol if advised. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "pain")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_word_number_one_to_two_doses_rejected(self):
        ref = "ROUTINE: Take one dose of vitamin A supplement. Attend clinic."
        cand = "ROUTINE: Take two doses of vitamin A supplement. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "vitamins")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_word_number_once_daily_to_twice_daily_rejected(self):
        ref = "ROUTINE: Take iron supplement once daily with water. Attend clinic."
        cand = "ROUTINE: Take iron supplement twice daily with water. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "vitamins")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_word_number_five_to_eight_weeks_rejected(self):
        ref = "ROUTINE: Fetal scan is scheduled in five weeks. Consult midwife."
        cand = "ROUTINE: Fetal scan is scheduled in eight weeks. Consult midwife."
        valid, reason = self.validator.validate(cand, ref, "routine", "scan")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_word_number_two_to_five_millilitres_rejected(self):
        ref = "ROUTINE: Administer two millilitres of liquid medicine. Attend clinic."
        cand = "ROUTINE: Administer five millilitres of liquid medicine. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "medicine")
        self.assertFalse(valid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_digit_and_word_unambiguous_equivalence_accepted(self):
        ref = "ROUTINE: Take 2 tablets of paracetamol for pain. Attend clinic."
        cand = "ROUTINE: Take two tablets of paracetamol for pain. Attend clinic."
        valid, reason = self.validator.validate(cand, ref, "routine", "pain")
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
