"""
Day 13 Single-Model End-to-End System Integration Tests
======================================================
Exercises the complete Chewie 1.2 safety architecture across the 6 mandatory scenarios:
1. Emergency in each language (English, Yoruba, Nigerian Pidgin).
2. A routine conversation that turns into an emergency (multi-turn transition).
3. An unsupported language code with a clinical danger sign.
4. A model timeout falling back to the deterministic engine.
5. A generated reply that fails the clinical validator triggering fallback.
6. The holding behaviour when no model is available (pre-AI mode).
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from motherlypulse_app.user_store import UserStore
from motherlypulse_app.assistant import MotherlyPulseAssistant
from motherlypulse_app.ai_connector import AIModelConnector, ClinicalInvariantValidator
from motherlypulse_app.telegram_bot import TelegramBotHandler


class TestSingleModelE2E(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.store = UserStore(self.db_path)

        # Mock AI connector configured for Chewie 1.2
        self.ai_connector = AIModelConnector(backend="mock", model_name="Chewie-1.2-Gemma2B")
        self.assistant = MotherlyPulseAssistant(ai_connector=self.ai_connector)
        self.bot = TelegramBotHandler(
            bot_token="TEST_BOT_TOKEN_E2E",
            assistant=self.assistant,
            user_store=self.store,
            ai_connector=self.ai_connector
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    # -------------------------------------------------------------------------
    # Scenario 1: Emergency in each language (EN, YO, PCM)
    # -------------------------------------------------------------------------
    def test_01_emergency_in_each_language(self):
        languages_and_prompts = [
            ("English", "I am 34 weeks pregnant and bleeding heavily with severe abdominal pain"),
            ("Yoruba", "Ẹ̀jẹ̀ púpọ̀ ń dà jáde láti ojú ara mi pẹ̀lú ìrora abẹ́ ikùn líle"),
            ("Nigerian Pidgin", "Heavy blood dey rush from my private part and my belle dey pain me well well")
        ]

        for lang, query in languages_and_prompts:
            user_id = f"user_emg_{lang[:2].lower()}"
            self.store.register_user(
                user_id=user_id,
                channel="telegram",
                language=lang,
                consent_given=True,
                alias="TestMother",
                user_group="pregnant_woman",
                registration_step="completed"
            )

            res = self.bot.process_update({
                "message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": query}
            })

            self.assertEqual(res["triage_category"], "EMERGENCY", f"Failed emergency escalation for {lang}")
            self.assertIn("112", res["text"], f"National 112 emergency number missing for {lang}")
            self.assertFalse(res.get("ai_generated", False), f"Emergency must bypass generative AI for {lang}")

    # -------------------------------------------------------------------------
    # Scenario 2: Routine conversation that turns into an emergency
    # -------------------------------------------------------------------------
    def test_02_routine_turns_into_emergency(self):
        user_id = "user_routine_to_emg"
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            alias="Grace",
            user_group="pregnant_woman",
            registration_step="completed"
        )

        # Turn 1: Routine query
        res1 = self.bot.process_update({
            "message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "What foods are rich in iron for pregnancy?"}
        })
        self.assertEqual(res1["triage_category"], "ROUTINE")
        self.assertTrue(res1.get("ai_generated", False))
        self.assertIn("Chewie-1.2", res1["text"])

        # Turn 2: Sudden maternal hemorrhage and convulsion
        res2 = self.bot.process_update({
            "message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Help, I started having convulsions and bleeding right now!"}
        })
        self.assertEqual(res2["triage_category"], "EMERGENCY")
        self.assertIn("112", res2["text"])
        self.assertFalse(res2.get("ai_generated", False))

    # -------------------------------------------------------------------------
    # Scenario 3: Unsupported language code with danger sign
    # -------------------------------------------------------------------------
    def test_03_unsupported_language_with_danger_sign(self):
        # Even if an unsupported language code ('fr', 'de', 'es') is passed,
        # emergency danger signs MUST trigger immediate 112 escalation
        user_id = "user_foreign_lang"
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="French",
            consent_given=True,
            alias="Marie",
            user_group="pregnant_woman",
            registration_step="completed"
        )

        res = self.bot.process_update({
            "message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Urgent severe vaginal bleeding and loss of consciousness"}
        })

        self.assertEqual(res["triage_category"], "EMERGENCY")
        self.assertIn("112", res["text"])

    # -------------------------------------------------------------------------
    # Scenario 4: Model timeout falls back to deterministic engine
    # -------------------------------------------------------------------------
    def test_04_model_timeout_triggers_deterministic_fallback(self):
        user_id = "user_timeout_test"
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            alias="Chioma",
            user_group="pregnant_woman",
            registration_step="completed"
        )

        # Switch connector to local_weights and simulate timeout
        self.ai_connector.backend = "local_weights"
        with patch.object(self.ai_connector, "_run_local_inference", side_effect=TimeoutError("Inference timed out after 5.0s")):
            res = self.bot.process_update({
                "message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "I feel slight pelvic heaviness at 32 weeks"}
            })

            self.assertIn(res["triage_category"], ["ROUTINE", "PRIORITY"])
            self.assertFalse(res.get("ai_generated", True))
            self.assertIn("Deterministic Fallback", res["text"])

    # -------------------------------------------------------------------------
    # Scenario 5: Reply failing validator triggers deterministic fallback
    # -------------------------------------------------------------------------
    def test_05_reply_failing_validator_triggers_deterministic_fallback(self):
        user_id = "user_violating_model"
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            alias="Bola",
            user_group="pregnant_woman",
            registration_step="completed"
        )

        # Model hallucinates recommending agbo (herbal mixture)
        self.ai_connector.backend = "local_weights"
        unsafe_reply = "ROUTINE: You can drink some herbal agbo concoction to feel relaxed."
        with patch.object(self.ai_connector, "_run_local_inference", return_value=unsafe_reply):
            res = self.bot.process_update({
                "message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "What herbal tea is good for sleep?"}
            })

            self.assertFalse(res.get("ai_generated", True))
            self.assertIn("Deterministic Fallback", res["text"])
            self.assertNotIn("agbo", res["text"].lower())

    # -------------------------------------------------------------------------
    # Scenario 6: Holding behaviour when no model is available (Pre-AI Mode)
    # -------------------------------------------------------------------------
    def test_06_holding_behaviour_when_no_model_available(self):
        user_id = "user_holding_test"
        # Bot with disabled AI backend
        holding_connector = AIModelConnector(backend="disabled")
        holding_assistant = MotherlyPulseAssistant(ai_connector=holding_connector)
        holding_bot = TelegramBotHandler(
            bot_token="TEST_BOT_TOKEN_HOLDING",
            assistant=holding_assistant,
            user_store=self.store,
            ai_connector=holding_connector
        )

        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            alias="Titi",
            user_group="pregnant_woman",
            registration_step="completed"
        )

        res = holding_bot.process_update({
            "message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Can I take paracetamol for a headache?"}
        })

        self.assertEqual(res["triage_category"], "ROUTINE")
        self.assertFalse(res.get("ai_generated", True))
        self.assertIn("112", res["text"])
        self.assertIn("Deterministic Holding Engine", res["text"])


if __name__ == "__main__":
    unittest.main()
