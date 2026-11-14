"""
Unit and Integration Tests for MotherlyPulse Phase 2 Capstone Features
Covers:
1. UserStore (Registration, language update, profile groups, right-to-erasure)
2. ReminderEngine (Appointments, medications, NPHCDA infant vaccination schedule)
3. LocationService (Ondo facilities & immunization lookup, distance calculation, transparency caveats)
4. InterfaceStrings (Multilingual strings, allow_unreviewed_translations safety fallback)
5. TelegramBotHandler (Command handling, GPS location parsing, emergency triage precedence)
6. WhatsAppWebhookAdapter (Meta Graph API verification, inbound text/location parsing, emergency triage precedence)
"""

import os
import unittest
import tempfile
from motherlypulse_app.user_store import UserStore
from motherlypulse_app.reminders import ReminderEngine
from motherlypulse_app.location_service import LocationService, haversine_distance_km
from motherlypulse_app.interface_strings import get_interface_string
from motherlypulse_app.telegram_bot import TelegramBotHandler
from motherlypulse_app.whatsapp_adapter import WhatsAppWebhookAdapter


class TestUserStoreAndReminders(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.store = UserStore(self.db_path)
        self.reminders = ReminderEngine(self.store)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_user_lifecycle(self):
        # 1. Register
        self.store.register_user("usr_001", "telegram", "English", consent_given=True, user_group="pregnant_woman")
        user = self.store.get_user("usr_001")
        self.assertIsNotNone(user)
        self.assertEqual(user["channel"], "telegram")
        self.assertEqual(user["user_group"], "pregnant_woman")

        # 2. Update language
        self.store.update_language("usr_001", "Yoruba")
        user = self.store.get_user("usr_001")
        self.assertEqual(user["language"], "Yoruba")

        # 3. Add reminders
        r1 = self.reminders.schedule_appointment_reminder("usr_001", "2026-12-01", "Akure State Specialist Hospital")
        self.assertIsInstance(r1, int)
        
        r2 = self.reminders.schedule_medication_reminder("usr_001", "Take 1 folic acid tablet with breakfast", "2026-12-01T08:00:00")
        self.assertIsInstance(r2, int)

        active = self.store.get_active_reminders("usr_001")
        self.assertEqual(len(active), 2)
        self.assertIn("folic acid", active[1]["reminder_text"])

        # 4. Schedule infant vaccination series
        self.store.update_user_group("usr_001", "mother_infant", baby_birth_date="2026-06-01")
        vax_ids = self.reminders.schedule_infant_vaccination_series("usr_001", "2026-06-01")
        self.assertGreater(len(vax_ids), 0)

        # 5. Right to Erasure (/delete)
        self.store.delete_user("usr_001")
        self.assertIsNone(self.store.get_user("usr_001"))
        self.assertEqual(len(self.store.get_active_reminders("usr_001")), 0)


class TestLocationService(unittest.TestCase):
    def setUp(self):
        self.loc_service = LocationService()

    def test_haversine_distance(self):
        # Distance between Akure (7.2571, 5.2058) and Ondo Town (7.0921, 4.8361) ~ 44 km
        d = haversine_distance_km(7.2571, 5.2058, 7.0921, 4.8361)
        self.assertGreater(d, 35)
        self.assertLess(d, 55)

    def test_find_nearest_facility(self):
        # Query near Akure
        facility = self.loc_service.find_nearest_facility(7.25, 5.20)
        self.assertIsNotNone(facility)
        self.assertIn("Akure", facility["lga"])
        self.assertIn("Approximate town location", facility["disclaimer"])

    def test_find_nearest_immunization_center(self):
        # Query near Akure
        imm = self.loc_service.find_nearest_immunization_center(7.25, 5.20)
        self.assertIsNotNone(imm)
        self.assertIn("Akure", imm["lga"])
        self.assertIn("Session days may have changed", imm["disclaimer"])


class TestInterfaceStrings(unittest.TestCase):
    def test_default_safety_fallback(self):
        # Yoruba status is 'in progress', so by default it must fall back safely to English
        yo_default = get_interface_string("welcome", "Yoruba", allow_unreviewed_translations=False)
        en_default = get_interface_string("welcome", "English")
        self.assertEqual(yo_default, en_default)

    def test_opt_in_translation(self):
        # When explicitly permitted, Yoruba returns the localized string
        yo_optin = get_interface_string("welcome", "Yoruba", allow_unreviewed_translations=True)
        self.assertIn("E kaabo", yo_optin)


class TestTelegramAndWhatsAppIntegrations(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.store = UserStore(self.db_path)
        self.tg_bot = TelegramBotHandler(user_store=self.store)
        self.wa_adapter = WhatsAppWebhookAdapter(user_store=self.store)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_telegram_emergency_precedence(self):
        # Even with /start or regular text, emergency message immediately returns emergency escalation
        emergency_update = {
            "message": {
                "chat": {"id": 12345},
                "from": {"id": 12345},
                "text": "My wife is having convulsions and fits right now"
            }
        }
        res = self.tg_bot.process_update(emergency_update)
        self.assertEqual(res["triage_category"], "EMERGENCY")
        self.assertIn("112", res["text"])

    def test_telegram_commands_and_consent(self):
        # 1. /start
        up1 = {"message": {"chat": {"id": 999}, "from": {"id": 999}, "text": "/start"}}
        res1 = self.tg_bot.process_update(up1)
        self.assertIn("Welcome to MotherlyPulse", res1["text"])
        user = self.store.get_user("999")
        self.assertFalse(bool(user["consent_given"]))

        # 2. /agree
        up2 = {"message": {"chat": {"id": 999}, "from": {"id": 999}, "text": "/agree"}}
        res2 = self.tg_bot.process_update(up2)
        self.assertIn("consent has been recorded", res2["text"])
        user = self.store.get_user("999")
        self.assertTrue(bool(user["consent_given"]))

        # 3. Location pin
        loc_up = {
            "message": {
                "chat": {"id": 999},
                "from": {"id": 999},
                "location": {"latitude": 7.25, "longitude": 5.20}
            }
        }
        res_loc = self.tg_bot.process_update(loc_up)
        self.assertIn("Nearby Health Facilities", res_loc["text"])

    def test_whatsapp_webhook_verification_and_emergency(self):
        # 1. Verification
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "MOTHERLYPULSE_VERIFY_TOKEN",
            "hub.challenge": "test_challenge_code_987"
        }
        valid, challenge, status = self.wa_adapter.verify_webhook(params)
        self.assertTrue(valid)
        self.assertEqual(challenge, "test_challenge_code_987")
        self.assertEqual(status, 200)

        # 2. Emergency Inbound Payload
        inbound = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "2348011223344",
                                        "type": "text",
                                        "text": {"body": "Severe bleeding soaking pads"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        outbound = self.wa_adapter.handle_incoming_payload(inbound)
        self.assertEqual(len(outbound), 1)
        self.assertEqual(outbound[0]["to"], "2348011223344")
        self.assertIn("EMERGENCY", outbound[0]["text"]["body"])
        self.assertIn("112", outbound[0]["text"]["body"])


if __name__ == "__main__":
    unittest.main()

