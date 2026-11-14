"""
Comprehensive Automated Unit and Integration Tests for MotherlyPulse
Telegram Bot Features (Non-AI Implementation, Day 9).

Covers:
1. Registration in English, Yoruba, and Nigerian Pidgin.
2. Consent acceptance and rejection.
3. Alias and user-group selection.
4. Expected Delivery Date (EDD) and Baby's Date of Birth (DOB) validation.
5. Language changes via /language.
6. Reminder creation, editing, and cancellation.
7. Scheduled reminder delivery and duplicate prevention across restarts.
8. SQLite database persistence after restart.
9. Health facility & immunization lookup with approximate-coordinate warnings.
10. Account deletion with explicit confirmation safeguard (right to erasure).
11. Emergency danger sign detection precedence before holding response.
12. Pre-AI holding response for non-emergency conversational queries.
13. Isolation of different Telegram users' data.
"""

import os
import unittest
import tempfile
import datetime
from unittest.mock import patch, MagicMock

from motherlypulse_app.user_store import UserStore, parse_and_validate_date
from motherlypulse_app.reminders import ReminderEngine
from motherlypulse_app.location_service import LocationService
from motherlypulse_app.telegram_bot import TelegramBotHandler


class TestTelegramBotNonAIFeatures(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.store = UserStore(self.db_path)
        self.location_service = LocationService()
        self.reminder_engine = ReminderEngine(self.store)
        self.bot = TelegramBotHandler(
            bot_token="TEST_BOT_TOKEN_12345",
            user_store=self.store,
            location_service=self.location_service,
            reminder_engine=self.reminder_engine
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    # =========================================================================
    # 1. REGISTRATION IN ENGLISH, YORUBA, AND NIGERIAN PIDGIN
    # =========================================================================
    def test_registration_flow_english(self):
        user_id = "user_en_101"
        # Step 1: /start
        up1 = {"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}}
        res1 = self.bot.process_update(up1)
        self.assertIn("Welcome to MotherlyPulse", res1["text"])
        self.assertIn("Please select your preferred language", res1["text"])

        # Step 2: Select English
        up2 = {"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}}
        res2 = self.bot.process_update(up2)
        self.assertIn("MOTHERLYPULSE CONSENT NOTICE", res2["text"])

        # Step 3: Accept consent
        up3 = {"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "agree"}}
        res3 = self.bot.process_update(up3)
        self.assertIn("What name or alias", res3["text"])
        user = self.store.get_user(user_id)
        self.assertTrue(bool(user["consent_given"]))
        self.assertIsNotNone(user["consent_date"])

        # Step 4: Enter alias
        up4 = {"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Mama Tolu"}}
        res4 = self.bot.process_update(up4)
        self.assertIn("Please select your user group", res4["text"])

        # Step 5: Select group (Pregnant woman)
        up5 = {"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}}
        res5 = self.bot.process_update(up5)
        self.assertIn("Expected Delivery Date", res5["text"])

        # Step 6: Enter valid EDD
        future_edd = (datetime.date.today() + datetime.timedelta(days=90)).isoformat()
        up6 = {"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": future_edd}}
        res6 = self.bot.process_update(up6)
        self.assertIn("Registration Complete", res6["text"])
        self.assertIn("Mama Tolu", res6["text"])
        self.assertIn("Pregnant Woman", res6["text"])

        # Verify DB state
        profile = self.store.get_user(user_id)
        self.assertEqual(profile["alias"], "Mama Tolu")
        self.assertEqual(profile["user_group"], "pregnant_woman")
        self.assertEqual(profile["expected_delivery_date"], future_edd)
        self.assertEqual(profile["language"], "English")
        self.assertTrue(self.store.is_user_registered(user_id))

    def test_registration_flow_yoruba(self):
        user_id = "user_yo_202"
        # Step 1: /start
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        # Step 2: Select Yoruba (code 'yo' or '2')
        res2 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "2"}})
        self.assertIn("IKEDE IFOHUNSOKAN", res2["text"])

        # Step 3: Accept consent in Yoruba
        res3 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "agree"}})
        self.assertIn("Orukọ inagijẹ", res3["text"])

        # Step 4: Enter alias
        res4 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Iya Funke"}})
        self.assertIn("yan ẹka", res4["text"])

        # Step 5: Select group (Mother/Caregiver of infant)
        res5 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "2"}})
        self.assertIn("bi ọmọ", res5["text"])

        # Step 6: Enter baby DOB (past date within 6 months)
        past_dob = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        res6 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": past_dob}})
        self.assertIn("Iforukọsilẹ Pari", res6["text"])
        self.assertIn("Iya Funke", res6["text"])

        # Verify DB & routine vaccines scheduled
        profile = self.store.get_user(user_id)
        self.assertEqual(profile["language"], "Yoruba")
        self.assertEqual(profile["user_group"], "mother_infant")
        self.assertEqual(profile["baby_birth_date"], past_dob)
        reminders = self.store.get_active_reminders(user_id)
        self.assertGreater(len(reminders), 0) # Routine vaccines auto-scheduled

    def test_registration_flow_pidgin(self):
        user_id = "user_pcm_303"
        # Step 1: /start
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        # Step 2: Select Pidgin ('3')
        res2 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "3"}})
        self.assertIn("MOTHERLYPULSE AGREE NOTICE", res2["text"])

        # Step 3: Accept consent
        res3 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "agree"}})
        self.assertIn("Which name or alias", res3["text"])

        # Step 4: Alias
        res4 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Sister Chioma"}})
        self.assertIn("choose which group", res4["text"])

        # Step 5: Select group (Pregnant)
        res5 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}})
        self.assertIn("Expected Delivery Date", res5["text"])

        # Step 6: Enter EDD using DD/MM/YYYY format
        future_dt = datetime.date.today() + datetime.timedelta(days=120)
        formatted_edd = future_dt.strftime("%d/%m/%Y")
        res6 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": formatted_edd}})
        self.assertIn("Registration Don Complete", res6["text"])
        self.assertIn("Sister Chioma", res6["text"])

        profile = self.store.get_user(user_id)
        self.assertEqual(profile["language"], "Nigerian Pidgin")
        self.assertEqual(profile["expected_delivery_date"], future_dt.isoformat())

    # =========================================================================
    # 2. CONSENT REJECTION
    # =========================================================================
    def test_consent_rejection_halts_registration(self):
        user_id = "user_decline_404"
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}}) # English
        
        # User explicitly declines consent
        res_decline = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "decline"}})
        self.assertIn("declined consent", res_decline["text"].lower())
        self.assertIn("112", res_decline["text"])

        # Verify user is not registered and personal data not stored
        user = self.store.get_user(user_id)
        self.assertFalse(bool(user["consent_given"]))
        self.assertFalse(self.store.is_user_registered(user_id))

        # Sending another text still blocks personal tracking
        res_after = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "My name is Amina"}})
        self.assertIn("complete your registration first", res_after["text"])

    # =========================================================================
    # 3. INTERRUPTED REGISTRATION RESUMPTION
    # =========================================================================
    def test_interrupted_registration_resumes_saved_step(self):
        user_id = "user_interrupted_505"
        # Starts and picks language
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "agree"}})

        # User closes Telegram at alias prompt. Hours later sends text:
        res_resume = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Mama Bisi"}})
        self.assertIn("select your user group", res_resume["text"].lower())

        user = self.store.get_user(user_id)
        self.assertEqual(user["alias"], "Mama Bisi")

    # =========================================================================
    # 4. DUPLICATE REGISTRATION PREVENTION
    # =========================================================================
    def test_prevent_duplicate_registration(self):
        user_id = "user_dup_606"
        # Register user completely
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            alias="Blessing",
            user_group="pregnant_woman",
            expected_delivery_date="2026-12-25",
            registration_step="completed"
        )
        
        # User types /start again
        res = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        self.assertIn("Welcome back, Blessing", res["text"])
        self.assertIn("Main Menu", res["text"])
        # Ensure profile was not erased
        profile = self.store.get_user(user_id)
        self.assertEqual(profile["alias"], "Blessing")

    # =========================================================================
    # 5. DATE VALIDATION & OVERDUE EDD TESTS
    # =========================================================================
    def test_edd_date_validation(self):
        ref = datetime.date(2026, 11, 7)
        # Valid EDD in future
        ok, iso, _ = parse_and_validate_date("2026-12-20", "pregnant_woman", ref)
        self.assertTrue(ok)
        self.assertEqual(iso, "2026-12-20")

        # Valid DD/MM/YYYY
        ok, iso, _ = parse_and_validate_date("20/12/2026", "pregnant_woman", ref)
        self.assertTrue(ok)
        self.assertEqual(iso, "2026-12-20")

        # Invalid format
        ok, _, code = parse_and_validate_date("tomorrow morning", "pregnant_woman", ref)
        self.assertFalse(ok)
        self.assertEqual(code, "invalid_format")

        # In distant past (> 14 days past): returns iso_str with edd_in_past code
        ok, iso_str, code = parse_and_validate_date("2026-09-01", "pregnant_woman", ref)
        self.assertFalse(ok)
        self.assertEqual(iso_str, "2026-09-01")
        self.assertEqual(code, "edd_in_past")

        # Too far in future (> 42 weeks)
        ok, _, code = parse_and_validate_date("2028-01-01", "pregnant_woman", ref)
        self.assertFalse(ok)
        self.assertEqual(code, "edd_too_far_future")

    def test_overdue_edd_flow_baby_born_yes(self):
        """When EDD is >14 days past and user confirms baby is born, switches to mother_infant."""
        user_id = "user_overdue_yes_801"
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}})  # English
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "agree"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Sister Ngozi"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}})  # Pregnant woman

        # Enter EDD 30 days in the past
        past_edd = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        res_edd = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": past_edd}})
        self.assertIn("Has your baby already been born?", res_edd["text"])
        self.assertIn("reply_markup", res_edd)

        # User replies "yes" (baby has arrived)
        res_confirm = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "yes"}})
        self.assertIn("Date of Birth", res_confirm["text"])
        self.assertIn("Congratulations", res_confirm["text"])

        # Enter valid baby DOB
        baby_dob = (datetime.date.today() - datetime.timedelta(days=25)).isoformat()
        res_dob = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": baby_dob}})
        self.assertIn("Registration Complete", res_dob["text"])
        self.assertIn("Mother / Caregiver of Infant", res_dob["text"])

        # Verify DB: profile is mother_infant, DOB is set, routine vaccines scheduled
        profile = self.store.get_user(user_id)
        self.assertEqual(profile["user_group"], "mother_infant")
        self.assertEqual(profile["baby_birth_date"], baby_dob)
        reminders = self.store.get_active_reminders(user_id)
        self.assertGreater(len(reminders), 0)

    def test_overdue_edd_flow_still_pregnant_no(self):
        """When EDD is >14 days past and user says still pregnant, retains pregnancy profile and provides clinical recommendation."""
        user_id = "user_overdue_no_802"
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}})  # English
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "agree"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Mama Halima"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}})  # Pregnant woman

        # Enter EDD 20 days in the past
        past_edd = (datetime.date.today() - datetime.timedelta(days=20)).isoformat()
        res_edd = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": past_edd}})
        self.assertIn("Has your baby already been born?", res_edd["text"])

        # User replies "no" (still expecting)
        res_no = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "no"}})
        self.assertIn("Registration Complete", res_no["text"])
        self.assertIn("Important Clinical Recommendation", res_no["text"])
        self.assertIn("112", res_no["text"])
        self.assertIn("antenatal clinic, doctor, or midwife", res_no["text"])

        # Verify DB: profile retained as pregnant_woman with past_edd saved
        profile = self.store.get_user(user_id)
        self.assertEqual(profile["user_group"], "pregnant_woman")
        self.assertEqual(profile["expected_delivery_date"], past_edd)
        self.assertTrue(self.store.is_user_registered(user_id))

    @patch.object(TelegramBotHandler, "answer_callback_query", return_value=True)
    def test_overdue_edd_callback_query(self, mock_ack):
        """Test inline keyboard callbacks for overdue EDD confirmation."""
        user_id = "user_overdue_cb_803"
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "agree"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Mama Sade"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "1"}})

        past_edd = (datetime.date.today() - datetime.timedelta(days=25)).isoformat()
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": past_edd}})

        # Callback born_no
        cb_update = {
            "callback_query": {
                "id": "cb_no_1",
                "from": {"id": user_id},
                "message": {"chat": {"id": user_id}},
                "data": "edd_check:born_no"
            }
        }
        res_cb = self.bot.process_update(cb_update)
        self.assertIn("Registration Complete", res_cb["text"])
        self.assertIn("Important Clinical Recommendation", res_cb["text"])

        profile = self.store.get_user(user_id)
        self.assertEqual(profile["user_group"], "pregnant_woman")
        self.assertEqual(profile["expected_delivery_date"], past_edd)

    def test_dob_date_validation(self):
        ref = datetime.date(2026, 11, 7)
        # Valid DOB in past (4 months old)
        ok, iso, _ = parse_and_validate_date("2026-07-01", "mother_infant", ref)
        self.assertTrue(ok)
        self.assertEqual(iso, "2026-07-01")

        # Valid DOB within 1 year (10 months old)
        ok, iso, _ = parse_and_validate_date("2026-01-01", "mother_infant", ref)
        self.assertTrue(ok)
        self.assertEqual(iso, "2026-01-01")

        # In future (impossible birth date)
        ok, _, code = parse_and_validate_date("2027-01-01", "mother_infant", ref)
        self.assertFalse(ok)
        self.assertEqual(code, "dob_in_future")

        # Older than 1 year (14 months old) -> rejected per 1-year infant scope
        ok, _, code = parse_and_validate_date("2025-09-01", "mother_infant", ref)
        self.assertFalse(ok)
        self.assertEqual(code, "dob_too_old")

        # Distant past (> 5 years)
        ok, _, code = parse_and_validate_date("2015-01-01", "mother_infant", ref)
        self.assertFalse(ok)
        self.assertEqual(code, "dob_too_old")

    # =========================================================================
    # 6. LANGUAGE CHANGING VIA /language
    # =========================================================================
    def test_language_switch_command(self):
        user_id = "user_lang_707"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")

        # Switch to Yoruba
        res_yo = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/language yoruba"}})
        self.assertIn("A ti yipada si Ede Yoruba", res_yo["text"])
        self.assertEqual(self.store.get_user(user_id)["language"], "Yoruba")

        # Switch to Pidgin
        res_pcm = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/language pidgin"}})
        self.assertIn("Language don change to Nigerian Pidgin", res_pcm["text"])
        self.assertEqual(self.store.get_user(user_id)["language"], "Nigerian Pidgin")

    # =========================================================================
    # 7. REMINDER FUNCTIONALITY (APPOINTMENT, MEDICATION, VACCINATION)
    # =========================================================================
    def test_appointment_reminder_creation(self):
        user_id = "user_rem_808"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")

        # Schedule clinic appointment
        res = self.bot.process_update({
            "message": {
                "chat": {"id": user_id}, "from": {"id": user_id},
                "text": "/remind_apt 2026-12-10 State Specialist Hospital Akure"
            }
        })
        self.assertIn("reminder scheduled", res["text"].lower())
        self.assertIn("2026-12-10", res["text"])

        active = self.store.get_active_reminders(user_id)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["reminder_type"], "appointment")
        self.assertIn("State Specialist Hospital", active[0]["reminder_text"])

    def test_medication_reminder_strictly_non_prescriptive(self):
        user_id = "user_med_909"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")

        # User schedules their own stated routine
        res = self.bot.process_update({
            "message": {
                "chat": {"id": user_id}, "from": {"id": user_id},
                "text": "/remind_med 08:30 Take 1 iron tablet with orange juice"
            }
        })
        self.assertIn("reminder scheduled", res["text"].lower())
        self.assertIn("08:30", res["text"])

        active = self.store.get_active_reminders(user_id)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["reminder_type"], "medication")
        self.assertEqual(active[0]["frequency"], "daily")
        self.assertIn("iron tablet", active[0]["reminder_text"])

    def test_vaccination_reminder_nphcda_schedule(self):
        user_id = "user_vax_1010"
        self.store.register_user(
            user_id=user_id,
            channel="telegram",
            language="English",
            consent_given=True,
            user_group="mother_infant",
            baby_birth_date="2026-08-01",
            registration_step="completed"
        )

        res = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/remind_vax"}})
        self.assertIn("Vaccination Schedule Activated", res["text"])
        self.assertIn("NPHCDA", res["text"])

        active = self.store.get_active_reminders(user_id)
        # NPHCDA schedule defines 7 primary milestones
        self.assertGreaterEqual(len(active), 7)
        self.assertTrue(any("BCG" in r["reminder_text"] for r in active))
        self.assertTrue(any("Pentavalent" in r["reminder_text"] for r in active))

    def test_reminder_cancellation(self):
        user_id = "user_cancel_1111"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")
        r_id = self.reminder_engine.schedule_appointment_reminder(user_id, "2026-12-05")

        # Cancel reminder
        res = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": f"/cancel_reminder {r_id}"}})
        self.assertIn("cancelled", res["text"].lower())

        # Verify it no longer appears in active list
        active = self.store.get_active_reminders(user_id)
        self.assertEqual(len(active), 0)

    # =========================================================================
    # 8. SCHEDULED REMINDER DELIVERY AND DUPLICATE PREVENTION ACROSS RESTARTS
    # =========================================================================
    def test_reminder_dispatch_and_restart_duplicate_prevention(self):
        user_id = "user_dispatch_1212"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")
        
        # Schedule reminder due right now
        past_iso = (datetime.datetime.utcnow() - datetime.timedelta(minutes=10)).isoformat()
        r_id = self.store.add_reminder(user_id, "appointment", "Clinic checkup today", past_iso)

        # Mock send_telegram_message
        with patch.object(self.bot, 'send_telegram_message', return_value=True) as mock_send:
            dispatched = self.bot.check_and_dispatch_due_reminders()
            self.assertEqual(len(dispatched), 1)
            self.assertEqual(dispatched[0]["reminder_id"], r_id)
            mock_send.assert_called_once()
            call_text = mock_send.call_args[0][1]
            self.assertIn("Clinic checkup today", call_text)

        # Verify delivered flag in DB
        rem_in_db = self.store.get_reminder(r_id)
        self.assertEqual(rem_in_db["delivered"], 1)

        # SIMULATE SERVER REBOOT: create a new bot instance on the same SQLite DB
        new_store = UserStore(self.db_path)
        new_bot = TelegramBotHandler(user_store=new_store)

        with patch.object(new_bot, 'send_telegram_message', return_value=True) as mock_send2:
            reboot_dispatched = new_bot.check_and_dispatch_due_reminders()
            # MUST NOT re-send already delivered reminder!
            self.assertEqual(len(reboot_dispatched), 0)
            mock_send2.assert_not_called()

    # =========================================================================
    # 9. FACILITY LOOKUP & HONESTY CAVEATS
    # =========================================================================
    def test_facility_lookup_via_gps_pin(self):
        user_id = "user_gps_1313"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")

        # Send GPS location near Akure (7.25, 5.20)
        loc_up = {
            "message": {
                "chat": {"id": user_id}, "from": {"id": user_id},
                "location": {"latitude": 7.25, "longitude": 5.20}
            }
        }
        res = self.bot.process_update(loc_up)
        self.assertIn("Nearby Health Facilities", res["text"])
        self.assertIn("Akure", res["text"])
        # Crucial transparency requirement: approximate town caveat
        self.assertIn("Approximate town location; ask locally for the exact entrance", res["text"])
        self.assertIn("Session days may have changed", res["text"])
        self.assertIn("112", res["text"])

    def test_facility_lookup_via_text_query(self):
        user_id = "user_query_1414"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")

        res = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/clinic Ondo"}})
        self.assertIn("Verified Facilities", res["text"])
        self.assertIn("Ondo", res["text"])

    # =========================================================================
    # 10. ACCOUNT DELETION WITH CONFIRMATION SAFEGUARD
    # =========================================================================
    def test_account_deletion_flow(self):
        user_id = "user_del_1515"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")
        self.reminder_engine.schedule_appointment_reminder(user_id, "2026-12-15")

        # Step 1: /delete requires confirmation
        res1 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/delete"}})
        self.assertIn("ACCOUNT DELETION CONFIRMATION", res1["text"])
        self.assertIn("cannot be undone", res1["text"])
        # User not yet deleted
        self.assertIsNotNone(self.store.get_user(user_id))

        # Step 2: Cancel
        res_cancel = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "cancel"}})
        self.assertIn("cancelled", res_cancel["text"].lower())
        self.assertIsNotNone(self.store.get_user(user_id))

        # Step 3: Trigger /delete and confirm
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/delete"}})
        res_confirm = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "confirm"}})
        self.assertIn("permanently deleted", res_confirm["text"].lower())

        # Verify complete erasure
        self.assertIsNone(self.store.get_user(user_id))
        self.assertEqual(len(self.store.get_active_reminders(user_id)), 0)

    # =========================================================================
    # 11. EMERGENCY DETECTION PRECEDENCE BEFORE HOLDING RESPONSE
    # =========================================================================
    def test_emergency_overrides_holding_and_commands(self):
        user_id = "user_emerg_1616"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")

        # Severe bleeding emergency
        emerg_msg = "Help me nurse I am bleeding heavily and feeling dizzy"
        res = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": emerg_msg}})
        self.assertEqual(res["triage_category"], "EMERGENCY")
        self.assertIn("112", res["text"])
        self.assertIn("EMERGENCY ALERT", res["text"])
        # Must NOT return holding message
        self.assertNotIn("conversational health assistant is currently in preparation", res["text"])

    def test_pre_ai_holding_response_for_routine_inquiries(self):
        user_id = "user_routine_1717"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")

        # Routine non-emergency inquiry
        routine_msg = "Can I eat eggs while pregnant?"
        res = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": routine_msg}})
        self.assertEqual(res["triage_category"], "ROUTINE")
        self.assertIn("in preparation (awaiting AI model integration)", res["text"])
        self.assertIn("112", res["text"])
        self.assertIn("Main Menu", res["text"])

    # =========================================================================
    # 12. MULTI-USER DATA ISOLATION
    # =========================================================================
    def test_multi_user_isolation(self):
        user_a = "user_alpha_1818"
        user_b = "user_beta_1919"

        self.store.register_user(user_id=user_a, channel="telegram", language="English", consent_given=True, alias="Alpha", registration_step="completed")
        self.store.register_user(user_id=user_b, channel="telegram", language="Yoruba", consent_given=True, alias="Beta", registration_step="completed")

        r_a = self.reminder_engine.schedule_appointment_reminder(user_a, "2026-12-01", "Akure Clinic")
        r_b = self.reminder_engine.schedule_appointment_reminder(user_b, "2026-12-20", "Ondo Clinic")

        rem_a = self.store.get_active_reminders(user_a)
        rem_b = self.store.get_active_reminders(user_b)

        self.assertEqual(len(rem_a), 1)
        self.assertEqual(len(rem_b), 1)
        self.assertEqual(rem_a[0]["reminder_id"], r_a)
        self.assertEqual(rem_b[0]["reminder_id"], r_b)

        # Deleting User A does not affect User B
        self.store.delete_user(user_a)
        self.assertIsNone(self.store.get_user(user_a))
        self.assertIsNotNone(self.store.get_user(user_b))
        self.assertEqual(len(self.store.get_active_reminders(user_b)), 1)

    # =========================================================================
    # 13. COMPREHENSIVE EMERGENCY PRECEDENCE ACROSS ALL 3 LANGUAGES
    # =========================================================================
    def test_comprehensive_emergency_precedence_across_languages(self):
        user_id = "user_prec_2020"
        self.store.register_user(user_id=user_id, channel="telegram", language="English", consent_given=True, registration_step="completed")

        # English maternal emergency
        res_en = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "I am having severe bleeding and convulsions"}})
        self.assertEqual(res_en["triage_category"], "EMERGENCY")
        self.assertIn("112", res_en["text"])

        # Yoruba infant emergency
        self.store.update_language(user_id, "Yoruba")
        res_yo = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Ọmọ mi n ja ipa pẹlu iba gbigbona"}})
        self.assertEqual(res_yo["triage_category"], "EMERGENCY")
        self.assertIn("112", res_yo["text"])

        # Nigerian Pidgin emergency
        self.store.update_language(user_id, "Nigerian Pidgin")
        res_pcm = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Heavy blood de rush from my private part"}})
        self.assertEqual(res_pcm["triage_category"], "EMERGENCY")
        self.assertIn("112", res_pcm["text"])


    # =========================================================================
    # 14. YORUBA NATURAL LANGUAGE REGISTRATION, CONSENT & DELETION COMMANDS
    # =========================================================================
    def test_yoruba_natural_language_registration_flow(self):
        """Validates that Yoruba mothers typing colloquial numbers ('eeji', 'okan')
        and Yoruba consent responses ('mo gba') complete registration flawlessly."""
        user_id = "user_yo_colloquial_999"
        # 1. Start using /beere (Yoruba alias for /start)
        res1 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/beere"}})
        self.assertIn("Welcome to MotherlyPulse", res1["text"])

        # 2. Select Yoruba using dialect word 'eeji'
        res2 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "eeji"}})
        self.assertIn("IKEDE IFOHUNSOKAN", res2["text"])

        # 3. Give consent using 'mo gba'
        res3 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "mo gba"}})
        self.assertIn("Orukọ inagijẹ", res3["text"])

        # 4. Set alias
        res4 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "Iya Simi"}})
        self.assertIn("yan ẹka", res4["text"])

        # 5. Select Pregnant group using 'okan'
        res5 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "okan"}})
        self.assertIn("reti ibimọ ọmọ yin", res5["text"])

        # 6. Set valid future EDD
        future_edd = (datetime.date.today() + datetime.timedelta(days=120)).isoformat()
        res6 = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": future_edd}})
        self.assertIn("Iforukọsilẹ Pari", res6["text"])
        self.assertIn("Iya Simi", res6["text"])
        self.assertIn("Alaboyun", res6["text"])

        # Verify database record
        profile = self.store.get_user(user_id)
        self.assertEqual(profile["language"], "Yoruba")
        self.assertEqual(profile["user_group"], "pregnant_woman")
        self.assertEqual(profile["alias"], "Iya Simi")
        self.assertTrue(self.store.is_user_registered(user_id))

    def test_yoruba_consent_decline_and_commands(self):
        """Validates 'mi o gba' refusal and /mogba, /duro direct command shortcuts."""
        user_id = "user_yo_decline_cmd_888"
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/start"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "2"}})

        # Decline via 'mi o gba'
        res_dec = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "mi o gba"}})
        self.assertIn("kọ ifọhunsọkan", res_dec["text"].lower())
        self.assertFalse(self.store.is_user_registered(user_id))

        # Restart via /beere and fast-track consent via /mogba
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/beere"}})
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "2"}})
        res_mogba = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/mogba"}})
        self.assertIn("Orukọ inagijẹ", res_mogba["text"])

    def test_yoruba_account_deletion_commands(self):
        """Validates 'fagile' cancellation and 'fowosi' confirmation for deletion."""
        user_id = "user_yo_delete_777"
        self.store.register_user(user_id=user_id, channel="telegram", language="Yoruba", consent_given=True, registration_step="completed")

        # Initiate /delete
        res_del = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/delete"}})
        self.assertIn("IPARẸ AKAUNTI", res_del["text"])

        # Cancel with 'fagile'
        res_can = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "fagile"}})
        self.assertIn("fagilee", res_can["text"].lower())
        self.assertTrue(self.store.is_user_registered(user_id))

        # Re-trigger /delete and confirm with 'fowosi'
        self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "/delete"}})
        res_conf = self.bot.process_update({"message": {"chat": {"id": user_id}, "from": {"id": user_id}, "text": "fowosi"}})
        self.assertIn("pa gbogbo alaye", res_conf["text"].lower())
        self.assertFalse(self.store.is_user_registered(user_id))


if __name__ == "__main__":
    unittest.main()