"""
Integration Tests for AI-Enabled Telegram Bot Flow & Assistant
==============================================================
Verifies that when an AI backend (Chewie 1.2 / MamaBot-Llama) is connected,
the Telegram bot and Assistant correctly generate, validate, and escalate
clinical responses while preserving strict emergency preemption and
deterministic fallbacks.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from motherlypulse_app.user_store import UserStore
from motherlypulse_app.assistant import MotherlyPulseAssistant
from motherlypulse_app.ai_connector import AIModelConnector
from motherlypulse_app.telegram_bot import TelegramBotHandler


class TestAITelegramIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.store = UserStore(self.db_path)
        
        # Initialize mock AI connector for Chewie 1.2
        self.ai_connector = AIModelConnector(backend="mock", model_name="chewie-1.2")
        self.assistant = MotherlyPulseAssistant(ai_connector=self.ai_connector)
        self.bot = TelegramBotHandler(
            bot_token="TEST_BOT_TOKEN_AI",
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

    def test_registered_user_receives_ai_generated_routine_response(self):
        user_id = "user_ai_routine_1"
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            alias="Folake",
            user_group="pregnant_woman",
            registration_step="completed"
        )

        update = {
            "message": {
                "chat": {"id": user_id},
                "from": {"id": user_id},
                "text": "What foods should I eat to prevent anemia?"
            }
        }
        res = self.bot.process_update(update)
        self.assertEqual(res["triage_category"], "ROUTINE")
        self.assertTrue(res.get("ai_generated", False))
        self.assertIn("chewie-1.2", res.get("model_used", ""))
        self.assertIn("ROUTINE:", res["text"])

    def test_multilingual_ai_responses(self):
        user_yo = "user_ai_yo_2"
        self.store.register_user(
            user_id=user_yo,
            channel="telegram",
            language="Yoruba",
            consent_given=True,
            alias="Ade",
            user_group="pregnant_woman",
            registration_step="completed"
        )
        up_yo = {
            "message": {
                "chat": {"id": user_yo},
                "from": {"id": user_yo},
                "text": "Bawo ni mo se le toju ara mi lasiko oyun?"
            }
        }
        res_yo = self.bot.process_update(up_yo)
        self.assertTrue(res_yo.get("ai_generated", False))
        self.assertIn("Yoruba", res_yo["text"])

        user_pcm = "user_ai_pcm_3"
        self.store.register_user(
            user_id=user_pcm,
            channel="telegram",
            language="Nigerian Pidgin",
            consent_given=True,
            alias="Blessing",
            user_group="mother_infant",
            registration_step="completed"
        )
        up_pcm = {
            "message": {
                "chat": {"id": user_pcm},
                "from": {"id": user_pcm},
                "text": "Which food good for my baby wey reach six months?"
            }
        }
        res_pcm = self.bot.process_update(up_pcm)
        self.assertTrue(res_pcm.get("ai_generated", False))
        self.assertIn("Nigerian Pidgin", res_pcm["text"])

    def test_emergency_query_bypasses_ai_completely(self):
        user_id = "user_ai_emerg_4"
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            alias="Chidinma",
            registration_step="completed"
        )

        update = {
            "message": {
                "chat": {"id": user_id},
                "from": {"id": user_id},
                "text": "I am convulsing and have severe chest pain"
            }
        }
        res = self.bot.process_update(update)
        self.assertEqual(res["triage_category"], "EMERGENCY")
        self.assertIn("112", res["text"])
        self.assertFalse(res.get("ai_generated", False))

    def test_unsafe_ai_generation_triggers_clinical_invariant_fallback(self):
        user_id = "user_ai_fallback_5"
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            alias="Ngozi",
            registration_step="completed"
        )

        # Invalidate generation by simulating unsafe model output recommending agbo
        with patch.object(self.ai_connector, "_run_local_inference", return_value="ROUTINE: You should drink agbo concoction twice daily."):
            self.ai_connector.backend = "local"
            res = self.bot.process_update({
                "message": {
                    "chat": {"id": user_id},
                    "from": {"id": user_id},
                    "text": "What can I take for stomach ache?"
                }
            })
            # Validator must reject agbo recommendation and fallback safely
            self.assertFalse(res.get("ai_generated", False))
            self.assertNotIn("drink agbo", res["text"])
            self.assertIn("ROUTINE:", res["text"])

    def test_unregistered_user_cannot_access_ai_without_registration(self):
        unreg_id = "user_unreg_999"
        update = {
            "message": {
                "chat": {"id": unreg_id},
                "from": {"id": unreg_id},
                "text": "Can I take paracetamol?"
            }
        }
        res = self.bot.process_update(update)
        self.assertIn("please complete your registration first", res["text"])
        self.assertIn("/start", res["text"])
