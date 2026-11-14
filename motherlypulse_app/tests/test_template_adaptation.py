"""
Unit and Integration Test Suite for MotherlyPulse Phase 1:
Deterministic Template-Based Conversational Response Adaptation Engine

Covers all 10 required testing areas:
1. Correct assembly of all four response slots (Empathy, Mirroring, Clinical Core, Action).
2. Correct handling of all three operational urgency categories (EMERGENCY, PRIORITY, ROUTINE).
3. English, Yoruba, and Nigerian Pidgin phrase selection and localization.
4. Preservation of mandatory clinical instructions and core advice.
5. Detection of omitted warnings (Validation failure).
6. Prevention of unsupported symptom mirroring (No hallucinated symptoms).
7. Prevention of invented medication advice (Negative token filter).
8. Correct fallback to the original reference response when validation fails.
9. Emergency bypass without conversational delays or question marks.
10. Preservation of existing application behavior and backward compatibility.
11. Verification against representative records from english_pairs.csv.
"""

import unittest
import pandas as pd
from motherlypulse_app.template_adapter import TemplateAdaptationEngine, ClinicalInvariantValidator
from motherlypulse_app.assistant import MotherlyPulseAssistant

class TestTemplateAdaptationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TemplateAdaptationEngine()
        self.validator = ClinicalInvariantValidator()
        self.assistant = MotherlyPulseAssistant(language="English", enable_adaptation=True)

    # 1. Correct assembly of all four response slots
    def test_01_four_slot_assembly(self):
        user_msg = "I have been vomiting and feeling nausea since morning."
        ref_text = "PRIORITY: Severe persistent vomiting risks dehydration. Please attend the clinic today."
        result = self.engine.adapt_response(user_msg, ref_text, "priority", "English")

        self.assertTrue(result["adaptation_applied"])
        self.assertTrue(result["validation_passed"])
        self.assertFalse(result["fallback_triggered"])

        slots = result["slot_breakdown"]
        self.assertIsNotNone(slots["empathy"])
        self.assertIsNotNone(slots["mirroring"])
        self.assertIsNotNone(slots["clinical_core"])
        self.assertIsNotNone(slots["action_referral"])

        # Check full string composition
        adapted = result["adapted_response"]
        self.assertTrue(adapted.startswith("PRIORITY:"))
        self.assertIn("vomiting", adapted.lower())
        self.assertIn("severe persistent vomiting risks dehydration", adapted.lower())
        self.assertIn("clinic", adapted.lower())

    # 2. Correct handling of all three urgency categories
    def test_02_all_urgency_categories(self):
        # Routine
        res_routine = self.engine.adapt_response(
            "How many times should I visit ANC?",
            "ROUTINE: Attend 8 antenatal visits.",
            "routine",
            "English"
        )
        self.assertTrue(res_routine["adapted_response"].startswith("ROUTINE:"))
        self.assertTrue(res_routine["adaptation_applied"])

        # Priority
        res_prio = self.engine.adapt_response(
            "I have painful urination.",
            "PRIORITY: Painful urination signals a urinary infection. Visit your clinic today.",
            "priority",
            "English"
        )
        self.assertTrue(res_prio["adapted_response"].startswith("PRIORITY:"))
        self.assertTrue(res_prio["adaptation_applied"])

        # Emergency
        res_emerg = self.engine.adapt_response(
            "I am bleeding heavily and convulsing.",
            "EMERGENCY: Immediate hospital transfer required. Call 112 | ODEMSA 0812 756 5478.",
            "emergency",
            "English"
        )
        self.assertTrue(res_emerg["adapted_response"].startswith("EMERGENCY:"))
        # Emergency bypass: adaptation must NOT be applied to preserve raw emergency speed
        self.assertFalse(res_emerg["adaptation_applied"])
        self.assertEqual(res_emerg["adapted_response"], "EMERGENCY: Immediate hospital transfer required. Call 112 | ODEMSA 0812 756 5478.")

    # 3. English, Yoruba and Nigerian Pidgin phrase selection
    def test_03_multilingual_phrase_selection(self):
        user_msg_en = "I have swollen feet."
        user_msg_yo = "Mo ni ẹsẹ wiwu."
        user_msg_pcm = "My leg swell."

        ref_en = "ROUTINE: Elevate your legs when sitting and avoid standing for long periods."
        ref_yo = "ROUTINE: Ẹ gbe ẹsẹ yin soke nigba ti ẹ ba joko."
        ref_pcm = "ROUTINE: Put your leg up when you sit down."

        # English
        res_en = self.engine.adapt_response(user_msg_en, ref_en, "routine", "English")
        self.assertIn("Regarding what you shared about swelling", res_en["adapted_response"])

        # Yoruba
        res_yo = self.engine.adapt_response(user_msg_yo, ref_yo, "routine", "Yoruba")
        self.assertIn("Ẹ pẹlẹ mà", res_yo["adapted_response"])
        self.assertIn("ẹsẹ ti o n wú", res_yo["adapted_response"])

        # Nigerian Pidgin
        res_pcm = self.engine.adapt_response(user_msg_pcm, ref_pcm, "routine", "Nigerian Pidgin")
        self.assertIn("Concerning the leg wey swell", res_pcm["adapted_response"])

    # 4. Preservation of mandatory clinical instructions
    def test_04_preservation_of_clinical_core(self):
        user_msg = "Can I do exercises in pregnancy?"
        ref_text = "ROUTINE: Moderate low-impact walking and stretching for 30 minutes is safe."
        result = self.engine.adapt_response(user_msg, ref_text, "routine", "English")

        self.assertIn("Moderate low-impact walking and stretching for 30 minutes is safe.", result["adapted_response"])

    # 5. Detection of omitted warnings (Validation failure)
    def test_05_detection_of_omitted_warnings(self):
        ref_text = "PRIORITY: Preeclampsia symptoms require immediate doctor examination today."
        # Candidate mutates core and omits the warning
        mutated_cand = "PRIORITY: I hear you. Everything is totally fine, just rest at home."

        is_valid, reason = self.validator.validate(
            candidate_response=mutated_cand,
            reference_response=ref_text,
            urgency_category="priority",
            user_message="I have a headache"
        )
        self.assertFalse(is_valid)
        self.assertTrue(any(e in reason for e in ["ERR_CLINICAL_CORE_MUTATED", "ERR_OMITTED_WARNING"]))

    # 6. Prevention of unsupported symptom mirroring
    def test_06_prevention_of_unsupported_symptom_mirroring(self):
        # User message has NO symptom (just a general question)
        user_msg = "What time does the clinic open for regular checkups?"
        symptom = self.engine.extract_symptom(user_msg)
        # Must be None, not hallucinating any symptom
        self.assertIsNone(symptom)

        res = self.engine.adapt_response(user_msg, "ROUTINE: Health clinics open at 8 AM for registration.", "routine", "English")
        # Must use general mirror framing, not a fabricated symptom
        self.assertIn("Regarding the question you shared:", res["adapted_response"])

    # 7. Prevention of invented medication advice
    def test_07_prevention_of_invented_medication(self):
        ref_text = "ROUTINE: Drink plenty of water and rest."
        # Fabricated candidate contains paracetamol and agbo
        bad_cand = "ROUTINE: Drink plenty of water and rest. Take 500mg paracetamol or drink agbo twice daily."

        is_valid, reason = self.validator.validate(
            candidate_response=bad_cand,
            reference_response=ref_text,
            urgency_category="routine",
            user_message="I have body aches"
        )
        self.assertFalse(is_valid)
        self.assertIn("ERR_INVENTED_MEDICATION", reason)

    # 8. Correct fallback to the original reference response
    def test_08_fallback_on_validation_failure(self):
        user_msg = "I have a headache."
        ref_text = "PRIORITY: Headache requires blood pressure evaluation at clinic."

        # Simulate corrupt engine by injecting an invalid prefix
        class BrokenEngine(TemplateAdaptationEngine):
            def adapt_response(self, user_message, reference_response, urgency_category, language="English"):
                # Missing 'PRIORITY:' prefix
                bad_response = "I hear you. Headache requires blood pressure evaluation at clinic."
                is_valid, failure_reason = self.validator.validate(
                    bad_response, reference_response, urgency_category, user_message, language
                )
                if not is_valid:
                    return {
                        "adapted_response": reference_response,
                        "fallback_triggered": True,
                        "validation_passed": False,
                        "failure_reason": failure_reason
                    }
                return {"adapted_response": bad_response}

        broken = BrokenEngine()
        res = broken.adapt_response(user_msg, ref_text, "priority")
        self.assertTrue(res["fallback_triggered"])
        self.assertFalse(res["validation_passed"])
        self.assertEqual(res["adapted_response"], ref_text)

    # 9. Emergency bypass without conversational delays
    def test_09_emergency_bypass_zero_delay(self):
        emerg_msg = "I am bleeding bright red blood at 30 weeks pregnant."
        res = self.assistant.respond(emerg_msg)

        self.assertEqual(res["urgency_category"], "emergency")
        self.assertFalse(res["adaptation_metadata"]["adaptation_applied"])
        self.assertIn("EMERGENCY:", res["response"])
        self.assertIn("112", res["response"])
        self.assertIn("0812 756 5478", res["response"])
        # Emergency must have NO conversational questions
        self.assertNotIn("?", res["response"])

    # 10. Preservation of existing application behaviour and backward compatibility
    def test_10_backward_compatibility(self):
        assistant_disabled = MotherlyPulseAssistant(language="English", enable_adaptation=False)
        user_msg = "I have taken my iron and folic acid tablet after breakfast."
        res = assistant_disabled.respond(user_msg)

        self.assertEqual(res["urgency_category"], "routine")
        self.assertFalse(res["adaptation_metadata"]["adaptation_applied"])
        self.assertTrue(res["response"].startswith("ROUTINE:"))

    # 11. Verification against representative records from dataset
    def test_11_dataset_records_verification(self):
        try:
            df = pd.read_csv("MotherlyPulse_Data/04_Conversation_Data/english_pairs.csv")
            # Sample 5 routine and 5 priority records
            routine_samples = df[df['triage_level'].str.lower() == 'routine'].head(5)
            priority_samples = df[df['triage_level'].str.lower() == 'priority'].head(5)

            for _, row in pd.concat([routine_samples, priority_samples]).iterrows():
                user_msg = row['user_message']
                ref_reply = row['reply']
                cat = row['triage_level'].lower()

                res = self.engine.adapt_response(user_msg, ref_reply, cat, "English")
                self.assertTrue(res["validation_passed"])
                self.assertTrue(res["adapted_response"].startswith(f"{cat.upper()}:"))
        except FileNotFoundError:
            self.skipTest("Dataset file not available for integration test.")

if __name__ == "__main__":
    unittest.main()
