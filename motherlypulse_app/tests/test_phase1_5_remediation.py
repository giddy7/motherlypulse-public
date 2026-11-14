"""
Unit, Integration, and Regression Tests for MotherlyPulse Phase 1.5 Remediation.
Covers:
1. CCP-01: Short clinical sentence & imperative preservation.
2. MSS-01: Numerical dosage, duration, and frequency mutation detection.
3. MSS-02: Expanded pharmaceutical & teratogenic token screening.
4. MSS-03: Supplement & medication polarity preservation.
5. E2E-01: HTTP server language integration & /health verification.
6. MLA-04: Explicit unsupported language handling.
7. Safe fallback on simulated adaptation engine exception.
"""

import unittest
import json
import threading
import urllib.request
import urllib.error
from unittest.mock import patch
from http.server import HTTPServer

from motherlypulse_app.template_adapter import (
    ClinicalInvariantValidator,
    TemplateAdaptationEngine
)
from motherlypulse_app.assistant import MotherlyPulseAssistant
from motherlypulse_app.server import MotherlyPulseRequestHandler


class TestPhase15Remediation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start ephemeral live HTTP server for end-to-end API tests
        cls.server = HTTPServer(('127.0.0.1', 0), MotherlyPulseRequestHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.validator = ClinicalInvariantValidator()
        self.engine = TemplateAdaptationEngine()
        self.assistant = MotherlyPulseAssistant()

    # =========================================================================
    # 1. CCP-01: Short Clinical Sentence & Imperative Preservation
    # =========================================================================
    def test_short_imperative_do_not_wait_preserved(self):
        ref = "PRIORITY: Severe headache can be dangerous. Do not wait. Attend your scheduled clinic visit within 24 hours."
        cand_valid = "PRIORITY: I hear your concern about your headache. Severe headache can be dangerous. Do not wait. Please attend your scheduled clinic visit within 24 hours."
        cand_missing = "PRIORITY: I hear your concern about your headache. Severe headache can be dangerous. Please attend your scheduled clinic visit within 24 hours."
        cand_weakened = "PRIORITY: I hear your concern about your headache. Severe headache can be dangerous. You can wait a bit. Please attend your scheduled clinic visit within 24 hours."

        valid, _ = self.validator.validate(cand_valid, ref, "priority", "Severe headache")
        self.assertTrue(valid)

        invalid_missing, reason_m = self.validator.validate(cand_missing, ref, "priority", "Severe headache")
        self.assertFalse(invalid_missing)
        self.assertIn("ERR_CLINICAL_CORE_MUTATED", reason_m)

        invalid_weak, reason_w = self.validator.validate(cand_weakened, ref, "priority", "Severe headache")
        self.assertFalse(invalid_weak)
        self.assertIn("ERR_CLINICAL_CORE_MUTATED", reason_w)

    def test_short_imperative_go_to_clinic_preserved(self):
        ref = "PRIORITY: Baby has slight fever. Go to clinic. Consult your health worker promptly today."
        cand_valid = "PRIORITY: I hear your concern about fever. Baby has slight fever. Go to clinic. Consult your health worker promptly today."
        cand_omitted = "PRIORITY: I hear your concern about fever. Baby has slight fever. Rest at home. Consult your health worker promptly today."

        valid, _ = self.validator.validate(cand_valid, ref, "priority", "fever")
        self.assertTrue(valid)

        invalid, reason = self.validator.validate(cand_omitted, ref, "priority", "fever")
        self.assertFalse(invalid)
        self.assertIn("ERR_CLINICAL_CORE_MUTATED", reason)

    def test_short_imperative_return_if_symptoms_worsen(self):
        ref = "ROUTINE: Mild nausea is common. Return if symptoms worsen. Attend your clinic visit as advised."
        cand_valid = "ROUTINE: We understand nausea can be uncomfortable. Mild nausea is common. Return if symptoms worsen. Attend your clinic visit as advised."
        cand_omitted = "ROUTINE: We understand nausea can be uncomfortable. Mild nausea is common. No need to come back. Attend your clinic visit as advised."

        valid, _ = self.validator.validate(cand_valid, ref, "routine", "nausea")
        self.assertTrue(valid)

        invalid, reason = self.validator.validate(cand_omitted, ref, "routine", "nausea")
        self.assertFalse(invalid)
        self.assertIn("ERR_CLINICAL_CORE_MUTATED", reason)

    # =========================================================================
    # 2. MSS-01: Numerical Dosage, Duration, and Frequency Invariance
    # =========================================================================
    def test_dosage_numerical_mutation_detected(self):
        ref = "ROUTINE: You can take 200mg paracetamol if authorized by your doctor. Attend clinic as scheduled."
        cand_mutated = "ROUTINE: You can take 800mg paracetamol if authorized by your doctor. Attend clinic as scheduled."
        cand_valid = "ROUTINE: You can take 200mg paracetamol if authorized by your doctor. Attend clinic as scheduled."

        valid, _ = self.validator.validate(cand_valid, ref, "routine", "pain")
        self.assertTrue(valid)

        invalid, reason = self.validator.validate(cand_mutated, ref, "routine", "pain")
        self.assertFalse(invalid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)
        self.assertIn("800.0 mg", reason)

    def test_dosage_ml_mutation_detected(self):
        ref = "ROUTINE: Administer 2.5ml oral rehydration solution. Consult your clinic promptly."
        cand_mutated = "ROUTINE: Administer 10ml oral rehydration solution. Consult your clinic promptly."

        invalid, reason = self.validator.validate(cand_mutated, ref, "routine", "dehydration")
        self.assertFalse(invalid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)

    def test_duration_numerical_mutation_detected(self):
        ref = "PRIORITY: Continue prescribed care for 3 days. Consult doctor at clinic within 24 hours."
        cand_mutated = "PRIORITY: Continue prescribed care for 7 days. Consult doctor at clinic within 24 hours."

        invalid, reason = self.validator.validate(cand_mutated, ref, "priority", "care")
        self.assertFalse(invalid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)
        self.assertIn("7 days", reason)

    def test_dosage_frequency_mutation_detected(self):
        ref = "ROUTINE: Take your prescribed medication once daily with water. Follow midwife guidance."
        cand_mutated = "ROUTINE: Take your prescribed medication twice daily with water. Follow midwife guidance."

        invalid, reason = self.validator.validate(cand_mutated, ref, "routine", "meds")
        self.assertFalse(invalid)
        self.assertIn("ERR_NUMERICAL_DOSAGE_MUTATED", reason)
        self.assertIn("once daily", reason)

    # =========================================================================
    # 3. MSS-02: Expanded Pharmaceutical & Teratogenic Token Screening
    # =========================================================================
    def test_unlisted_antibiotic_cefuroxime_rejected(self):
        ref = "PRIORITY: Please visit the health centre within 24 hours for proper examination."
        cand = "PRIORITY: I understand. You should take cefuroxime before visiting the health centre within 24 hours."

        invalid, reason = self.validator.validate(cand, ref, "priority", "fever")
        self.assertFalse(invalid)
        self.assertIn("ERR_INVENTED_MEDICATION", reason)
        self.assertIn("cefuroxime", reason)

    def test_unlisted_teratogen_warfarin_rejected(self):
        ref = "ROUTINE: Maintain healthy diet and rest. Consult doctor at clinic."
        cand = "ROUTINE: Maintain healthy diet and you can try warfarin. Consult doctor at clinic."

        invalid, reason = self.validator.validate(cand, ref, "routine", "diet")
        self.assertFalse(invalid)
        self.assertIn("ERR_INVENTED_MEDICATION", reason)
        self.assertIn("warfarin", reason)

    # =========================================================================
    # 4. MSS-03: Supplement & Medication Polarity Invariance
    # =========================================================================
    def test_supplement_polarity_permission_to_prohibition_rejected(self):
        ref = "ROUTINE: You can take your prescribed iron supplement daily. Attend your clinic visit as advised."
        cand = "ROUTINE: Do not take iron supplement. Attend your clinic visit as advised."

        invalid, reason = self.validator.validate(cand, ref, "routine", "vitamins")
        self.assertFalse(invalid)
        self.assertIn("ERR_MEDICATION_POLARITY_INVERSION", reason)
        self.assertIn("iron", reason)

    def test_medication_polarity_prohibition_to_permission_rejected(self):
        ref = "ROUTINE: Do not take ibuprofen during pregnancy. Consult your midwife at the clinic."
        cand = "ROUTINE: You can safely take ibuprofen during pregnancy. Consult your midwife at the clinic."

        invalid, reason = self.validator.validate(cand, ref, "routine", "headache")
        self.assertFalse(invalid)
        self.assertIn("ERR_MEDICATION_POLARITY_INVERSION", reason)
        self.assertIn("ibuprofen", reason)

    def test_supplement_folic_acid_polarity_preserved(self):
        ref = "ROUTINE: Folic acid is recommended throughout early pregnancy. Always consult your health centre."
        cand_valid = "ROUTINE: Folic acid is recommended throughout early pregnancy. Always consult your health centre."
        cand_prohibited = "ROUTINE: Avoid folic acid throughout early pregnancy. Always consult your health centre."

        valid, _ = self.validator.validate(cand_valid, ref, "routine", "vitamins")
        self.assertTrue(valid)

        invalid, reason = self.validator.validate(cand_prohibited, ref, "routine", "vitamins")
        self.assertFalse(invalid)
        self.assertIn("ERR_MEDICATION_POLARITY_INVERSION", reason)

    # =========================================================================
    # 5. E2E-01: HTTP Server Language Integration & Health Endpoint
    # =========================================================================
    def test_server_health_supported_languages(self):
        url = f"http://127.0.0.1:{self.port}/health"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "healthy")
            self.assertIn("English", data["supported_languages"])
            self.assertIn("Yoruba", data["supported_languages"])
            self.assertIn("Nigerian Pidgin", data["supported_languages"])

    def test_server_post_chat_language_routing_and_validation(self):
        url = f"http://127.0.0.1:{self.port}/api/chat"

        # 1. Valid Yoruba request
        payload_yo = json.dumps({"message": "E kaaro ma, ara mi n gbona", "language": "Yoruba"}).encode("utf-8")
        req_yo = urllib.request.Request(url, data=payload_yo, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req_yo) as resp:
            self.assertEqual(resp.status, 200)
            res_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res_data["language"], "Yoruba")

        # 2. Valid Nigerian Pidgin request
        payload_pcm = json.dumps({"message": "My baby de vomit", "language": "Nigerian Pidgin"}).encode("utf-8")
        req_pcm = urllib.request.Request(url, data=payload_pcm, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req_pcm) as resp:
            self.assertEqual(resp.status, 200)
            res_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res_data["language"], "Nigerian Pidgin")

        # 3. Unsupported language (Hausa) returns HTTP 400
        payload_hausa = json.dumps({"message": "Ina kwana", "language": "Hausa"}).encode("utf-8")
        req_hausa = urllib.request.Request(url, data=payload_hausa, headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req_hausa)
        self.assertEqual(cm.exception.code, 400)
        err_data = json.loads(cm.exception.read().decode("utf-8"))
        self.assertIn("Unsupported language 'Hausa'", err_data["error"])
        self.assertIn("English, Yoruba, Nigerian Pidgin", err_data["error"])

    # =========================================================================
    # 6. MLA-04: Assistant Unsupported Language Limitation Notice
    # =========================================================================
    def test_assistant_unsupported_language_returns_explicit_notice(self):
        res = self.assistant.respond("I have a question about my pregnancy", language="Hausa")
        
        self.assertEqual(res["status"], "language_not_supported")
        self.assertEqual(res["requested_language"], "Hausa")
        self.assertIn("Support for 'Hausa' is not yet available", res["response"])
        self.assertIn("English, Yoruba, and Nigerian Pidgin", res["response"])
        self.assertIn("112", res["response"])
        self.assertFalse(res["adaptation_metadata"]["adaptation_applied"])

    # =========================================================================
    # 7. Safe Fallback on Simulated Adaptation Engine Exception
    # =========================================================================
    def test_safe_fallback_on_adapter_runtime_exception(self):
        with patch.object(self.assistant.adapter, "adapt_response", side_effect=RuntimeError("Simulated memory allocation failure")):
            # Routine inquiry
            res_routine = self.assistant.respond("What healthy foods should I eat during the first trimester?")
            self.assertEqual(res_routine["urgency_category"], "routine")
            self.assertTrue(res_routine["response"].startswith("ROUTINE:"))
            self.assertTrue(res_routine["adaptation_metadata"]["fallback_triggered"])
            self.assertIn("Simulated memory allocation failure", res_routine["adaptation_metadata"]["error"])

            # Priority inquiry
            res_priority = self.assistant.respond(
                "I missed my tetanus injection at my clinic appointment",
                matched_passage="PRIORITY: Tetanus vaccination is crucial. Attend your scheduled clinic visit within 24 to 48 hours."
            )
            self.assertEqual(res_priority["urgency_category"], "priority")
            self.assertTrue(res_priority["response"].startswith("PRIORITY:"))
            self.assertTrue(res_priority["adaptation_metadata"]["fallback_triggered"])
            self.assertIn("Simulated memory allocation failure", res_priority["adaptation_metadata"]["error"])


if __name__ == "__main__":
    unittest.main()
