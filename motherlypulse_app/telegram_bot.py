"""
MotherlyPulse Telegram Bot Client (Non-AI Maternal & Infant Health Assistant)
Provides an interactive maternal and infant health channel for Telegram.

Key Features (Non-AI Implementation):
- Reads `TELEGRAM_BOT_TOKEN` from the environment or .env file.
- Supported languages: English, Yoruba, Nigerian Pidgin.
- Complete multi-turn registration flow with saved progress and resumption:
    1. /start -> Select language (English, Yoruba, Pidgin)
    2. Consent notice in selected language -> Accept or Decline
    3. Alias / preferred name
    4. User group (Pregnant woman vs Mother/caregiver of infant)
    5. Milestone date (Expected delivery date or Baby's date of birth) with clinical validation
- Duplicate registration prevention (returning users see profile and Main Menu).
- Supported commands:
    * /start: Begin registration or open Main Menu
    * /language: Change preferred language
    * /profile: View registered maternal/infant profile
    * /remind: View active reminders
    * /remind_apt: Schedule clinic appointment reminder
    * /remind_med: Schedule personal medication reminder (strictly non-prescriptive)
    * /remind_vax: Schedule infant vaccination schedule based on official NPHCDA schedule
    * /cancel_reminder: Cancel a scheduled reminder
    * /clinic: Locates nearest verified primary health centre or immunization post in Ondo State
    * /delete: Request account and data erasure (with confirmation)
    * /help: Interactive usage instructions
    * /menu: Display Main Menu
- Location lookup: handles GPS location pins, text coordinates, or Ondo town/LGA queries with honesty caveats.
- CRITICAL CLINICAL SAFETY INVARIANT:
    Every incoming text message is triaged for emergency danger signs FIRST.
    If classified as EMERGENCY, immediately returns approved emergency response with 112 line,
    overriding any routine conversational, registration, or command processing.
- PRE-AI HOLDING MODE:
    Free-text health inquiries receive an approved holding notice explaining that conversational
    AI models are in preparation, advising menu features and the 112 emergency line.
"""

import os
import sys
import json
import logging
import datetime
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple, List

from .assistant import MotherlyPulseAssistant
from .classifier import DynamicTriageClassifier
from .user_store import UserStore, parse_and_validate_date, get_wat_timezone
from .location_service import LocationService
from .reminders import ReminderEngine
from .interface_strings import get_localized_string
from .ai_connector import AIModelConnector

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


class TelegramBotHandler:
    def __init__(
        self,
        bot_token: Optional[str] = None,
        assistant: Optional[MotherlyPulseAssistant] = None,
        user_store: Optional[UserStore] = None,
        location_service: Optional[LocationService] = None,
        reminder_engine: Optional[ReminderEngine] = None,
        ai_connector: Optional[AIModelConnector] = None
    ):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.ai_connector = ai_connector or (assistant.ai_connector if assistant and hasattr(assistant, "ai_connector") else AIModelConnector())
        self.assistant = assistant or MotherlyPulseAssistant(ai_connector=self.ai_connector)
        self.user_store = user_store or UserStore()
        self.location_service = location_service or LocationService()
        self.reminder_engine = reminder_engine or ReminderEngine(self.user_store)
        self.classifier = DynamicTriageClassifier()
        self.tz = get_wat_timezone()

    def process_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a raw Telegram Update object and produces an outgoing response.
        Enforces emergency triage prioritization before any command or dialog parsing.
        """
        # 1. Handle Callback Query (Inline button clicks)
        if "callback_query" in update:
            return self._handle_callback_query(update["callback_query"])

        message = update.get("message") or update.get("edited_message")
        if not message:
            return {"status": "ignored", "reason": "no_message"}

        chat_id = str(message.get("chat", {}).get("id", ""))
        user_id = str(message.get("from", {}).get("id", chat_id))
        user_profile = self.user_store.get_user(user_id)
        current_lang = user_profile["language"] if user_profile else "English"

        # 2. Check for GPS Location Message
        if "location" in message:
            lat = message["location"].get("latitude")
            lon = message["location"].get("longitude")
            reply = self._handle_location(user_id, lat, lon, current_lang)
            return {"chat_id": chat_id, "text": reply, "triage_category": "ROUTINE"}

        text = message.get("text", "").strip()
        if not text:
            return {"status": "ignored", "reason": "empty_text"}

        # 3. SAFETY FIRST: Triaging emergency danger signs before ANY command or conversational processing
        triage_res = self.classifier.classify(text)
        if triage_res.get("urgency_category") == "emergency":
            emergency_reply = self._get_emergency_reply(current_lang)
            return {
                "chat_id": chat_id,
                "text": emergency_reply,
                "triage_category": "EMERGENCY",
                "matched_rules": triage_res.get("reason", "")
            }

        # 4. Handle Direct Commands (e.g. /start, /language, /delete, /help, /remind, /clinic, /profile)
        if text.startswith("/"):
            return self._handle_command(user_id, chat_id, text, current_lang, user_profile)

        # 5. Check if user is in an active multi-turn state (Registration, Deletion confirmation, Reminders)
        step, partial_data = self.user_store.get_registration_state(user_id)
        if step and step != "completed":
            return self._handle_registration_state(user_id, chat_id, text, step, partial_data, current_lang)

        # 6. Check if user is in account deletion confirmation
        if partial_data.get("awaiting_delete_confirm"):
            return self._handle_delete_confirmation(user_id, chat_id, text, current_lang)

        # 7. Check if user is in reminder scheduling flow
        if partial_data.get("awaiting_reminder_type"):
            return self._handle_reminder_flow(user_id, chat_id, text, partial_data, current_lang)

        # 8. Check if user is registered
        if not self.user_store.is_user_registered(user_id):
            # Prompt unregistered user to complete registration
            prompt_msg = (
                f"Welcome to MotherlyPulse! To access health reminders, clinic lookups, and maternal guidance, "
                f"please complete your registration first.\n\n"
                f"Type /start to begin."
            )
            return {"chat_id": chat_id, "text": prompt_msg, "triage_category": "ROUTINE"}

        # 9. Registered User Health Inquiries — Pre-AI Holding Response
        # The AI models (Chewie 1.2 / MamaBot-Llama) are not connected yet.
        # Free-text queries return the approved holding response with the 112 emergency line and menu navigation.
        # 9. Registered User Health Inquiries
        if self.ai_connector and self.ai_connector.backend != "disabled":
            assistant_res = self.assistant.respond(
                message=text,
                language=current_lang,
                user_group=user_profile.get("user_group")
            )
            raw_reply = assistant_res.get("response") or assistant_res.get("reply", "")
            urgency = assistant_res.get("urgency_category", "ROUTINE").upper()
            ai_gen = assistant_res.get("ai_generated", False)
            model_used = assistant_res.get("model_used", "")

            # Show which mode is running (model live or fallback) for non-emergency responses
            # (emergency responses remain strictly unpolluted with 112 escalation only)
            if urgency != "EMERGENCY":
                if ai_gen:
                    mode_indicator = f"\n\n🤖 *[Mode: Live Model ({model_used})]*"
                else:
                    mode_indicator = f"\n\n🛡️ *[Mode: Deterministic Fallback ({model_used})]*"
                reply_text = f"{raw_reply}{mode_indicator}"
            else:
                reply_text = raw_reply

            menu_text, menu_markup = self._build_main_menu(current_lang)
            return {
                "chat_id": chat_id,
                "text": reply_text,
                "reply_markup": menu_markup,
                "triage_category": urgency,
                "ai_generated": ai_gen,
                "model_used": model_used
            }

        # Pre-AI Holding Response
        holding_text = get_localized_string("holding_message", current_lang)
        mode_indicator = "\n\n🛡️ *[Mode: Deterministic Holding Engine (Pre-AI)]*"
        menu_text, menu_markup = self._build_main_menu(current_lang)
        combined_text = f"{holding_text}{mode_indicator}\n\n{menu_text}"
        return {
            "chat_id": chat_id,
            "text": combined_text,
            "reply_markup": menu_markup,
            "triage_category": "ROUTINE",
            "ai_generated": False,
            "model_used": "DeterministicHolding"
        }

    # =========================================================================
    # Emergency Response Formatter
    # =========================================================================
    def _get_emergency_reply(self, language: str) -> str:
        """Returns approved emergency escalation response with national 112 line."""
        if language == "Yoruba":
            return (
                "EMERGENCY ALERT: Ọrọ rẹ fihan ami eewu ilera to le koko.\n\n"
                "Ẹ jọwọ ẹ pe nọmba pajawiri 112 lẹsẹkẹsẹ tabi ki ẹ lọ si ile-iwosan pajawiri to sunmọ julọ.\n\n"
                "Ẹ ma ṣe duro ni ile. Ti ẹ ba nilo ọkọ pajawiri, ẹ pe 112 lẹsẹkẹsẹ."
            )
        elif language == "Nigerian Pidgin":
            return (
                "EMERGENCY ALERT: Your message show say na serious danger sign.\n\n"
                "Abeg call national emergency on 112 quick-quick or carry body go the nearest emergency hospital.\n\n"
                "Make you no wait for house at all. If you need ambulance, call 112 now-now."
            )
        else:
            return (
                "EMERGENCY ALERT: Your message indicates a critical medical danger sign.\n\n"
                "Please call 112 immediately or proceed to the nearest emergency maternal/pediatric facility.\n\n"
                "Do not wait at home. If transport is needed, call national emergency services on 112."
            )

    # =========================================================================
    # Multi-Turn Registration State Machine
    # =========================================================================
    def _start_registration(self, user_id: str, chat_id: str) -> Dict[str, Any]:
        """Begins or restarts the registration sequence at Step 1: Language Selection."""
        self.user_store.set_registration_step(user_id, "awaiting_language", {})
        welcome_header = "Welcome to MotherlyPulse! I am your maternal and infant health support assistant for Ondo State.\n\n"
        prompt = welcome_header + get_localized_string("language_select_prompt", "English")
        markup = {
            "inline_keyboard": [
                [{"text": "1. English", "callback_data": "lang:en"}],
                [{"text": "2. Èdè Yorùbá", "callback_data": "lang:yo"}],
                [{"text": "3. Naijá Pidgin", "callback_data": "lang:pcm"}]
            ]
        }
        return {"chat_id": chat_id, "text": prompt, "reply_markup": markup, "triage_category": "ROUTINE"}

    def _handle_registration_state(
        self,
        user_id: str,
        chat_id: str,
        text: str,
        step: str,
        partial_data: Dict[str, Any],
        current_lang: str
    ) -> Dict[str, Any]:
        """Executes the next step in the multi-turn registration flow."""
        clean_text = text.strip()

        # Step 1: Language selection
        if step == "awaiting_language":
            lang_map = {
                "1": "English", "english": "English", "en": "English", "okan": "English", "ọkan": "English",
                "2": "Yoruba", "yoruba": "Yoruba", "yo": "Yoruba", "eeji": "Yoruba", "eji": "Yoruba", "èjì": "Yoruba",
                "3": "Nigerian Pidgin", "pidgin": "Nigerian Pidgin", "pcm": "Nigerian Pidgin", "meta": "Nigerian Pidgin", "mẹta": "Nigerian Pidgin"
            }
            selected_lang = lang_map.get(clean_text.lower())
            if not selected_lang:
                msg = (
                    "Please choose a valid language:\n"
                    "1. English\n"
                    "2. Yoruba\n"
                    "3. Nigerian Pidgin\n\n"
                    "Reply with 1, 2, or 3."
                )
                return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}

            self.user_store.update_language(user_id, selected_lang)
            partial_data["language"] = selected_lang
            self.user_store.set_registration_step(user_id, "awaiting_consent", partial_data)

            consent_notice = get_localized_string("consent_notice_text", selected_lang)
            markup = {
                "inline_keyboard": [
                    [{"text": "✅ Agree / Accept", "callback_data": "consent:agree"}],
                    [{"text": "❌ Decline", "callback_data": "consent:decline"}]
                ]
            }
            return {"chat_id": chat_id, "text": consent_notice, "reply_markup": markup, "triage_category": "ROUTINE"}

        # Step 2: Consent Notice
        elif step == "awaiting_consent":
            norm = clean_text.lower()
            if norm in ("agree", "/agree", "yes", "accept", "1", "gba", "mo gba", "mogba", "/mogba"):
                self.user_store.record_consent(user_id, True)
                self.user_store.set_registration_step(user_id, "awaiting_alias", partial_data)
                alias_msg = get_localized_string("alias_request", current_lang)
                return {"chat_id": chat_id, "text": f"✅ {get_localized_string('consent_confirmed', current_lang)}\n\n{alias_msg}", "triage_category": "ROUTINE"}
            elif norm in ("decline", "/stop", "no", "reject", "2", "kọ", "ko", "mi o gba", "mi o gba mo", "duro", "/duro"):
                self.user_store.record_consent(user_id, False)
                self.user_store.set_registration_step(user_id, "consent_declined", {})
                decline_msg = get_localized_string("consent_declined", current_lang)
                return {"chat_id": chat_id, "text": decline_msg, "triage_category": "ROUTINE"}
            else:
                retry_msg = (
                    "Please reply with 'agree' to give consent, or 'decline' to stop."
                    if current_lang == "English" else
                    "Ẹ jọwọ dahun 'mo gba' (tabi /agree) lati gba, tabi 'mi o gba' (tabi /stop) lati da duro."
                )
                return {"chat_id": chat_id, "text": retry_msg, "triage_category": "ROUTINE"}

        # Step 3: Alias
        elif step == "awaiting_alias":
            alias = clean_text
            if len(alias) > 50:
                alias = alias[:50]
            self.user_store.update_alias(user_id, alias)
            partial_data["alias"] = alias
            self.user_store.set_registration_step(user_id, "awaiting_group", partial_data)

            group_msg = get_localized_string("group_request", current_lang)
            markup = {
                "inline_keyboard": [
                    [{"text": "🤰 Expecting a Baby (Pregnant woman)", "callback_data": "group:pregnant"}],
                    [{"text": "👶 Mother / Caregiver of Infant", "callback_data": "group:mother"}]
                ]
            }
            return {"chat_id": chat_id, "text": group_msg, "reply_markup": markup, "triage_category": "ROUTINE"}

        # Step 4: User Group
        elif step == "awaiting_group":
            norm = clean_text.lower()
            if "preg" in norm or norm in ("1", "okan", "ọkan") or "alaboyun" in norm or "belle" in norm:
                group = "pregnant_woman"
            elif "moth" in norm or "infant" in norm or "baby" in norm or norm in ("2", "eeji", "eji", "èjì") or "iya" in norm or "pikin" in norm:
                group = "mother_infant"
            else:
                msg = (
                    "Please select your user group:\n"
                    "1. Pregnant woman\n"
                    "2. Mother or caregiver of an infant\n\n"
                    "Reply with 1 or 2."
                )
                return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}

            self.user_store.update_user_group(user_id, group)
            partial_data["user_group"] = group
            self.user_store.set_registration_step(user_id, "awaiting_date", partial_data)

            if group == "pregnant_woman":
                date_prompt = get_localized_string("edd_request", current_lang)
            else:
                date_prompt = get_localized_string("dob_request", current_lang)

            return {"chat_id": chat_id, "text": date_prompt, "triage_category": "ROUTINE"}

        # Step 5: Milestone Date Validation & Completion
        elif step == "awaiting_date":
            group = partial_data.get("user_group")
            if not group:
                user = self.user_store.get_user(user_id)
                group = user.get("user_group", "pregnant_woman") if user else "pregnant_woman"

            valid, iso_date, error_code = parse_and_validate_date(clean_text, group)
            if not valid:
                if error_code == "edd_in_past" and group == "pregnant_woman" and iso_date:
                    partial_data["pending_past_edd"] = iso_date
                    self.user_store.set_registration_step(user_id, "awaiting_edd_baby_born_check", partial_data)
                    prompt = get_localized_string("edd_past_check_prompt", current_lang)
                    markup = {
                        "inline_keyboard": [
                            [{"text": "👶 Yes, Baby is Born", "callback_data": "edd_check:born_yes"}],
                            [{"text": "🤰 No, Still Pregnant", "callback_data": "edd_check:born_no"}]
                        ]
                    }
                    return {"chat_id": chat_id, "text": prompt, "reply_markup": markup, "triage_category": "ROUTINE"}

                err_key = f"date_error_{error_code}" if error_code else "date_error_format"
                err_msg = get_localized_string(err_key, current_lang)
                return {"chat_id": chat_id, "text": f"❌ {err_msg}", "triage_category": "ROUTINE"}

            # Save normalized milestone date and complete registration
            edd = iso_date if group == "pregnant_woman" else None
            dob = iso_date if group == "mother_infant" else None
            self.user_store.update_user_group(user_id, group, expected_delivery_date=edd, baby_birth_date=dob)
            self.user_store.set_registration_step(user_id, "completed", {})

            alias = partial_data.get("alias") or (self.user_store.get_user(user_id) or {}).get("alias") or "Friend"
            group_desc = "Pregnant Woman" if group == "pregnant_woman" else "Mother / Caregiver of Infant"
            if current_lang == "Yoruba":
                group_desc = "Alaboyun" if group == "pregnant_woman" else "Iya tabi Alabojuto Ọmọ"
            elif current_lang == "Nigerian Pidgin":
                group_desc = "Belle Woman" if group == "pregnant_woman" else "Mama / Caregiver of Pikin"

            success_tmpl = get_localized_string("registration_complete", current_lang)
            success_text = success_tmpl.format(
                alias=alias,
                group_desc=group_desc,
                milestone_date=iso_date,
                language=current_lang
            )

            # Also auto-schedule routine infant vaccinations if infant caregiver
            if group == "mother_infant" and dob:
                self.reminder_engine.schedule_infant_vaccination_series(user_id, dob)

            menu_text, menu_markup = self._build_main_menu(current_lang)
            return {
                "chat_id": chat_id,
                "text": f"{success_text}\n\n{menu_text}",
                "reply_markup": menu_markup,
                "triage_category": "ROUTINE"
            }

        elif step == "awaiting_edd_baby_born_check":
            norm = clean_text.lower()
            pending_edd = partial_data.get("pending_past_edd")
            if norm in ("yes", "y", "1", "beeni", "bẹẹni", "born", "baby born"):
                # Baby is born: offer infant registration flow
                self.user_store.update_user_group(user_id, "mother_infant")
                partial_data["user_group"] = "mother_infant"
                self.user_store.set_registration_step(user_id, "awaiting_date", partial_data)
                date_prompt = get_localized_string("dob_request", current_lang)
                intro = (
                    "Congratulations on your baby's arrival! 👶\n\n"
                    if current_lang == "English" else
                    "Ẹ ku ewu ọmọ! 👶\n\n"
                    if current_lang == "Yoruba" else
                    "Congrats on your new baby! 👶\n\n"
                )
                return {"chat_id": chat_id, "text": f"{intro}{date_prompt}", "triage_category": "ROUTINE"}
            elif norm in ("no", "n", "2", "rara", "ko tii", "still pregnant", "not yet"):
                # Baby not born yet: retain pregnancy profile and provide appropriate clinical recommendation
                self.user_store.update_user_group(user_id, "pregnant_woman", expected_delivery_date=pending_edd)
                self.user_store.set_registration_step(user_id, "completed", {})
                alias = partial_data.get("alias") or (self.user_store.get_user(user_id) or {}).get("alias") or "Friend"
                tmpl = get_localized_string("edd_post_term_retained_notice", current_lang)
                notice_text = tmpl.format(alias=alias, milestone_date=pending_edd)
                menu_text, menu_markup = self._build_main_menu(current_lang)
                return {
                    "chat_id": chat_id,
                    "text": f"{notice_text}\n\n{menu_text}",
                    "reply_markup": menu_markup,
                    "triage_category": "ROUTINE"
                }
            else:
                retry_msg = (
                    "Please reply 'yes' if baby has been born, or 'no' if you are still expecting."
                    if current_lang == "English" else
                    "Ẹ jọwọ dahun 'beeni' ti a ba ti bi ọmọ, tabi 'rara' ti ẹ ba ṣi wa ninu oyun."
                )
                return {"chat_id": chat_id, "text": retry_msg, "triage_category": "ROUTINE"}

        elif step == "consent_declined":
            msg = (
                "You previously declined consent. To access MotherlyPulse services, "
                "please type /start to review the consent notice and complete your registration first."
                if current_lang == "English" else
                "Ẹ ti kọ ifọhunsọkan tẹlẹ. Lati lo MotherlyPulse, ẹ tẹ /start tabi /beere lati tun bẹrẹ."
            )
            return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}

        return {"chat_id": chat_id, "text": "Please complete your registration first by typing /start.", "triage_category": "ROUTINE"}

    # =========================================================================
    # Callback Query Handling (Inline Buttons)
    # =========================================================================
    def _handle_callback_query(self, cb: Dict[str, Any]) -> Dict[str, Any]:
        cb_id = str(cb.get("id", ""))
        from_user = cb.get("from", {})
        user_id = str(from_user.get("id", ""))
        chat_id = str(cb.get("message", {}).get("chat", {}).get("id", user_id))
        data = cb.get("data", "").strip()

        user_profile = self.user_store.get_user(user_id)
        current_lang = user_profile["language"] if user_profile else "English"

        # Acknowledge callback query
        self.answer_callback_query(cb_id)

        # 1. Language callbacks
        if data.startswith("lang:"):
            code = data.split(":", 1)[1]
            lang_map = {"en": "English", "yo": "Yoruba", "pcm": "Nigerian Pidgin"}
            new_lang = lang_map.get(code, "English")
            self.user_store.update_language(user_id, new_lang)
            step, partial_data = self.user_store.get_registration_state(user_id)

            if step == "awaiting_language" or not self.user_store.is_user_registered(user_id):
                partial_data["language"] = new_lang
                self.user_store.set_registration_step(user_id, "awaiting_consent", partial_data)
                notice = get_localized_string("consent_notice_text", new_lang)
                markup = {
                    "inline_keyboard": [
                        [{"text": "✅ Agree / Accept", "callback_data": "consent:agree"}],
                        [{"text": "❌ Decline", "callback_data": "consent:decline"}]
                    ]
                }
                return {"chat_id": chat_id, "text": notice, "reply_markup": markup, "triage_category": "ROUTINE"}
            else:
                ack = get_localized_string("language_updated", new_lang)
                menu_text, menu_markup = self._build_main_menu(new_lang)
                return {"chat_id": chat_id, "text": f"{ack}\n\n{menu_text}", "reply_markup": menu_markup, "triage_category": "ROUTINE"}

        # 2. Consent callbacks
        elif data.startswith("consent:"):
            action = data.split(":", 1)[1]
            step, partial_data = self.user_store.get_registration_state(user_id)
            if action == "agree":
                self.user_store.record_consent(user_id, True)
                self.user_store.set_registration_step(user_id, "awaiting_alias", partial_data)
                alias_msg = get_localized_string("alias_request", current_lang)
                return {"chat_id": chat_id, "text": f"✅ {get_localized_string('consent_confirmed', current_lang)}\n\n{alias_msg}", "triage_category": "ROUTINE"}
            else:
                self.user_store.record_consent(user_id, False)
                self.user_store.set_registration_step(user_id, "consent_declined", {})
                decline_msg = get_localized_string("consent_declined", current_lang)
                return {"chat_id": chat_id, "text": decline_msg, "triage_category": "ROUTINE"}

        # 3. User Group callbacks
        elif data.startswith("group:"):
            grp_code = data.split(":", 1)[1]
            group = "pregnant_woman" if grp_code == "pregnant" else "mother_infant"
            step, partial_data = self.user_store.get_registration_state(user_id)
            self.user_store.update_user_group(user_id, group)
            partial_data["user_group"] = group
            self.user_store.set_registration_step(user_id, "awaiting_date", partial_data)
            date_prompt = get_localized_string("edd_request" if group == "pregnant_woman" else "dob_request", current_lang)
            return {"chat_id": chat_id, "text": date_prompt, "triage_category": "ROUTINE"}

        # 3b. Overdue EDD baby born check callbacks
        elif data.startswith("edd_check:"):
            action = data.split(":", 1)[1]
            step, partial_data = self.user_store.get_registration_state(user_id)
            pending_edd = partial_data.get("pending_past_edd")
            if action == "born_yes":
                self.user_store.update_user_group(user_id, "mother_infant")
                partial_data["user_group"] = "mother_infant"
                self.user_store.set_registration_step(user_id, "awaiting_date", partial_data)
                date_prompt = get_localized_string("dob_request", current_lang)
                intro = (
                    "Congratulations on your baby's arrival! 👶\n\n"
                    if current_lang == "English" else
                    "Ẹ ku ewu ọmọ! 👶\n\n"
                    if current_lang == "Yoruba" else
                    "Congrats on your new baby! 👶\n\n"
                )
                return {"chat_id": chat_id, "text": f"{intro}{date_prompt}", "triage_category": "ROUTINE"}
            else:
                self.user_store.update_user_group(user_id, "pregnant_woman", expected_delivery_date=pending_edd)
                self.user_store.set_registration_step(user_id, "completed", {})
                alias = partial_data.get("alias") or (self.user_store.get_user(user_id) or {}).get("alias") or "Friend"
                tmpl = get_localized_string("edd_post_term_retained_notice", current_lang)
                notice_text = tmpl.format(alias=alias, milestone_date=pending_edd)
                menu_text, menu_markup = self._build_main_menu(current_lang)
                return {
                    "chat_id": chat_id,
                    "text": f"{notice_text}\n\n{menu_text}",
                    "reply_markup": menu_markup,
                    "triage_category": "ROUTINE"
                }

        # 4. Main Menu callbacks
        elif data.startswith("menu:"):
            action = data.split(":", 1)[1]
            if action == "profile":
                return {"chat_id": chat_id, "text": self._format_profile(user_id, current_lang), "triage_category": "ROUTINE"}
            elif action == "language":
                prompt = get_localized_string("language_select_prompt", current_lang)
                markup = {
                    "inline_keyboard": [
                        [{"text": "English", "callback_data": "lang:en"}],
                        [{"text": "Èdè Yorùbá", "callback_data": "lang:yo"}],
                        [{"text": "Naijá Pidgin", "callback_data": "lang:pcm"}]
                    ]
                }
                return {"chat_id": chat_id, "text": prompt, "reply_markup": markup, "triage_category": "ROUTINE"}
            elif action == "apt":
                msg = (
                    "📅 **Antenatal / Clinic Appointment Reminders**\n\n"
                    "To schedule a clinic visit reminder, use:\n"
                    "`/remind_apt YYYY-MM-DD [Clinic Name]`\n\n"
                    "Example:\n"
                    "`/remind_apt 2026-12-05 State Specialist Hospital Akure`"
                )
                return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}
            elif action == "med":
                msg = (
                    "💊 **Medication Reminders**\n\n"
                    "To schedule your personal medication reminder, use:\n"
                    "`/remind_med HH:MM Medication details`\n\n"
                    "Example:\n"
                    "`/remind_med 08:00 Take 1 folic acid tablet with food`\n\n"
                    "⚠️ *Note: The bot faithfully repeats your scheduled routine. It does not prescribe or alter doses.*"
                )
                return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}
            elif action == "vax":
                return self._handle_vax_command(user_id, chat_id, current_lang)
            elif action == "clinic":
                instructions = self.location_service.get_location_instructions(current_lang)
                return {"chat_id": chat_id, "text": instructions, "triage_category": "ROUTINE"}
            elif action == "help":
                return {"chat_id": chat_id, "text": get_localized_string("help_text", current_lang), "triage_category": "ROUTINE"}
            elif action == "delete":
                return self._start_delete_confirmation(user_id, chat_id, current_lang)

        return {"chat_id": chat_id, "text": "Command processed.", "triage_category": "ROUTINE"}

    # =========================================================================
    # Direct Telegram Commands
    # =========================================================================
    def _handle_command(
        self,
        user_id: str,
        chat_id: str,
        cmd_text: str,
        current_lang: str,
        user_profile: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        parts = cmd_text.split()
        cmd = parts[0].lower()

        # /start: Begin registration or show Main Menu if registered
        if cmd in ("/start", "/beere", "/bẹrẹ"):
            if self.user_store.is_user_registered(user_id):
                alias = user_profile.get("alias") or "Friend"
                welcome_back = (
                    f"Welcome back, {alias}! Here is your MotherlyPulse menu."
                    if current_lang == "English" else
                    f"Ẹ kaabọ pada, {alias}! Eyi ni akojọ aṣayan MotherlyPulse yin."
                    if current_lang == "Yoruba" else
                    f"Welcome back, {alias}! See your MotherlyPulse menu here."
                )
                menu_text, menu_markup = self._build_main_menu(current_lang)
                return {
                    "chat_id": chat_id,
                    "text": f"{welcome_back}\n\n{menu_text}",
                    "reply_markup": menu_markup,
                    "triage_category": "ROUTINE"
                }
            else:
                return self._start_registration(user_id, chat_id)

        # /agree: Fast-track consent if prompted
        elif cmd in ("/agree", "/mogba", "/mo_gba"):
            step, partial_data = self.user_store.get_registration_state(user_id)
            self.user_store.record_consent(user_id, True)
            self.user_store.set_registration_step(user_id, "awaiting_alias", partial_data)
            alias_msg = get_localized_string("alias_request", current_lang)
            return {"chat_id": chat_id, "text": f"✅ {get_localized_string('consent_confirmed', current_lang)}\n\n{alias_msg}", "triage_category": "ROUTINE"}

        # /stop or /duro: Fast-track decline or pause
        elif cmd in ("/stop", "/duro"):
            step, partial_data = self.user_store.get_registration_state(user_id)
            if step == "awaiting_consent":
                self.user_store.record_consent(user_id, False)
                self.user_store.set_registration_step(user_id, "consent_declined", {})
                decline_msg = get_localized_string("consent_declined", current_lang)
                return {"chat_id": chat_id, "text": decline_msg, "triage_category": "ROUTINE"}
            else:
                return {"chat_id": chat_id, "text": "MotherlyPulse paused. Type /start or /beere to resume.", "triage_category": "ROUTINE"}

        # /language: Change language
        elif cmd == "/language":
            if len(parts) > 1:
                arg = parts[1].strip().lower()
                lang_map = {
                    "english": "English", "en": "English", "1": "English", "okan": "English", "ọkan": "English",
                    "yoruba": "Yoruba", "yo": "Yoruba", "2": "Yoruba", "eeji": "Yoruba", "eji": "Yoruba",
                    "pidgin": "Nigerian Pidgin", "pcm": "Nigerian Pidgin", "3": "Nigerian Pidgin", "meta": "Nigerian Pidgin", "mẹta": "Nigerian Pidgin"
                }
                new_lang = lang_map.get(arg)
                if new_lang:
                    self.user_store.update_language(user_id, new_lang)
                    ack = get_localized_string("language_updated", new_lang)
                    menu_text, menu_markup = self._build_main_menu(new_lang)
                    return {"chat_id": chat_id, "text": f"{ack}\n\n{menu_text}", "reply_markup": menu_markup, "triage_category": "ROUTINE"}
                return {"chat_id": chat_id, "text": "Supported languages: English, Yoruba, Nigerian Pidgin.\nExample: /language yoruba", "triage_category": "ROUTINE"}
            else:
                prompt = get_localized_string("language_select_prompt", current_lang)
                markup = {
                    "inline_keyboard": [
                        [{"text": "English", "callback_data": "lang:en"}],
                        [{"text": "Èdè Yorùbá", "callback_data": "lang:yo"}],
                        [{"text": "Naijá Pidgin", "callback_data": "lang:pcm"}]
                    ]
                }
                return {"chat_id": chat_id, "text": prompt, "reply_markup": markup, "triage_category": "ROUTINE"}

        # /profile: View profile
        elif cmd == "/profile":
            return {"chat_id": chat_id, "text": self._format_profile(user_id, current_lang), "triage_category": "ROUTINE"}

        # /delete: Request account erasure with confirmation
        elif cmd == "/delete":
            return self._start_delete_confirmation(user_id, chat_id, current_lang)

        # /confirm_delete: Execute deletion
        elif cmd in ("/confirm_delete", "/fowosi", "/fọwọsi"):
            self.user_store.delete_user(user_id)
            ack = get_localized_string("data_deleted", current_lang)
            return {"chat_id": chat_id, "text": f"🗑️ {ack}", "triage_category": "ROUTINE"}

        # /cancel: Cancel active action
        elif cmd in ("/cancel", "/fagile"):
            self.user_store.set_registration_step(user_id, "completed", {})
            ack = get_localized_string("delete_cancelled", current_lang)
            menu_text, menu_markup = self._build_main_menu(current_lang)
            return {"chat_id": chat_id, "text": f"{ack}\n\n{menu_text}", "reply_markup": menu_markup, "triage_category": "ROUTINE"}

        # /help: Interactive usage instructions
        elif cmd == "/help":
            return {"chat_id": chat_id, "text": get_localized_string("help_text", current_lang), "triage_category": "ROUTINE"}

        # /menu: Show main menu
        elif cmd == "/menu":
            menu_text, menu_markup = self._build_main_menu(current_lang)
            return {"chat_id": chat_id, "text": menu_text, "reply_markup": menu_markup, "triage_category": "ROUTINE"}

        # /remind: List active reminders
        elif cmd == "/remind":
            reminders = self.user_store.get_active_reminders(user_id)
            if not reminders:
                msg = (
                    "You have no active reminders scheduled.\n\n"
                    "Schedule reminders using:\n"
                    "• `/remind_apt YYYY-MM-DD [Clinic]` - Antenatal / Clinic appointment\n"
                    "• `/remind_med HH:MM [Medicine]` - Daily medication\n"
                    "• `/remind_vax` - Infant routine vaccinations"
                )
                return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}

            lines = ["📋 **Your Active Reminders:**\n"]
            for r in reminders:
                freq = f" ({r['frequency']})" if r.get("frequency") and r["frequency"] != "once" else ""
                lines.append(f"• [ID: {r['reminder_id']}] **{r['reminder_type'].title()}**{freq}: {r['reminder_text']} (Scheduled: {r['scheduled_time']})")
            lines.append("\nTo cancel a reminder, type: `/cancel_reminder <ID>`")
            return {"chat_id": chat_id, "text": "\n".join(lines), "triage_category": "ROUTINE"}

        # /remind_apt: Schedule clinic appointment reminder
        elif cmd == "/remind_apt":
            if len(parts) < 2:
                msg = "Please provide appointment date: `/remind_apt YYYY-MM-DD [Clinic Name]`\nExample: `/remind_apt 2026-12-01 State Specialist Hospital`"
                return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}
            apt_date = parts[1]
            clinic = " ".join(parts[2:]) if len(parts) > 2 else "your primary health clinic"
            try:
                r_id = self.reminder_engine.schedule_appointment_reminder(user_id, apt_date, clinic)
                return {"chat_id": chat_id, "text": f"✅ Appointment reminder scheduled (ID: {r_id}) for {apt_date} at {clinic}.", "triage_category": "ROUTINE"}
            except Exception as e:
                return {"chat_id": chat_id, "text": f"❌ Error scheduling appointment: {str(e)}", "triage_category": "ROUTINE"}

        # /remind_med: Schedule medication reminder
        elif cmd == "/remind_med":
            if len(parts) < 3:
                msg = (
                    "Please provide reminder time and medication details:\n"
                    "`/remind_med HH:MM [Medication details]`\n"
                    "Example: `/remind_med 08:00 Take 1 folic acid tablet with breakfast`\n\n"
                    "⚠️ *Note: MotherlyPulse faithfully records your routine; it does not prescribe medications.*"
                )
                return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}
            time_part = parts[1]
            med_text = " ".join(parts[2:])
            # Calculate next occurrence of HH:MM
            now = datetime.datetime.now(self.tz)
            scheduled_iso = f"{now.date().isoformat()}T{time_part}:00"
            r_id = self.reminder_engine.schedule_medication_reminder(user_id, med_text, scheduled_iso, frequency="daily")
            return {"chat_id": chat_id, "text": f"✅ Medication reminder scheduled (ID: {r_id}) for {time_part} daily: {med_text}.", "triage_category": "ROUTINE"}

        # /remind_vax: Schedule infant vaccination schedule
        elif cmd == "/remind_vax":
            return self._handle_vax_command(user_id, chat_id, current_lang)

        # /cancel_reminder: Cancel a reminder
        elif cmd == "/cancel_reminder":
            if len(parts) < 2:
                return {"chat_id": chat_id, "text": "Usage: `/cancel_reminder <ID>`", "triage_category": "ROUTINE"}
            try:
                r_id = int(parts[1])
                success = self.reminder_engine.cancel_reminder(user_id, r_id)
                if success:
                    return {"chat_id": chat_id, "text": f"✅ Reminder #{r_id} cancelled.", "triage_category": "ROUTINE"}
                return {"chat_id": chat_id, "text": f"❌ Reminder #{r_id} not found or already cancelled.", "triage_category": "ROUTINE"}
            except ValueError:
                return {"chat_id": chat_id, "text": "Please provide a valid numeric reminder ID.", "triage_category": "ROUTINE"}

        # /clinic: Location lookup
        elif cmd in ("/clinic", "/hospital", "/find"):
            if len(parts) > 1:
                query = " ".join(parts[1:])
                # Check if coordinates were passed: /clinic 7.25, 5.20
                coords = self.location_service.parse_coordinates_from_text(query)
                if coords:
                    lat, lon = coords
                    reply = self._handle_location(user_id, lat, lon, current_lang)
                    return {"chat_id": chat_id, "text": reply, "triage_category": "ROUTINE"}

                # Search by town/LGA query
                matches = self.location_service.find_facilities_by_query(query)
                if matches:
                    lines = [f"🏥 Verified Facilities in Ondo State matching '{query}':\n"]
                    for m in matches:
                        lines.append(
                            f"• **{m['facility_name']}** ({m.get('local_government_area', '')} LGA)\n"
                            f"  Address: {m.get('street_address', m.get('town_or_community', ''))}\n"
                            f"  ⚠️ {m.get('disclaimer', '')}\n"
                        )
                    return {"chat_id": chat_id, "text": "\n".join(lines), "triage_category": "ROUTINE"}
                else:
                    return {"chat_id": chat_id, "text": f"No verified facility found matching '{query}' in Ondo State. In emergency, call 112.", "triage_category": "ROUTINE"}

            instructions = self.location_service.get_location_instructions(current_lang)
            return {"chat_id": chat_id, "text": instructions, "triage_category": "ROUTINE"}

        # /compare <question>: Side-by-side A/B demo (Baseline vs. Fine-Tuned Chewie 1.2)
        elif cmd == "/compare":
            query = cmd_text[len(parts[0]):].strip()
            if not query:
                usage_msg = (
                    "🔬 **A/B Model Comparison Demo (`/compare`)**\n\n"
                    "Compare **Baseline (`google/gemma-2-2b-it`)** vs. **Fine-Tuned (`Chewie 1.2 QLoRA`)** "
                    "side-by-side with live `ClinicalInvariantValidator` checks.\n\n"
                    "Usage: `/compare <your health question>`\n"
                    "Example: `/compare Can I take aspirin for a headache during pregnancy?`"
                )
                return {"chat_id": chat_id, "text": usage_msg, "triage_category": "ROUTINE"}

            triage_res = self.classifier.classify(query)
            urgency = triage_res.get("urgency_category", "routine")
            if urgency == "emergency":
                return {
                    "chat_id": chat_id,
                    "text": self._get_emergency_reply(current_lang),
                    "triage_category": "EMERGENCY",
                    "matched_rules": triage_res.get("reason", ""),
                }

            cmp_res = self.ai_connector.compare_models(query, urgency, current_lang)
            if not cmp_res.get("available"):
                offline_msg = (
                    f"⚠️ **Live A/B Comparison Unavailable**\n"
                    f"Reason: {cmp_res.get('reason', 'Remote AI endpoint is offline.')}\n\n"
                    "You can still send your question normally in chat for verified deterministic guidance."
                )
                return {
                    "chat_id": chat_id,
                    "text": offline_msg,
                    "triage_category": urgency.upper(),
                    "compare_available": False,
                }

            def _fmt_side(label: str, side: Dict[str, Any]) -> str:
                val = side.get("validation", {})
                is_safe = val.get("is_safe", False)
                verdict = "✅ Passed" if is_safe else f"❌ Rejected ({val.get('reason', 'Safety violation')})"
                raw = (side.get("response") or "").strip()
                if len(raw) > 1200:
                    raw = raw[:1197] + "..."
                latency = side.get("latency_ms", 0.0)
                return (
                    f"**{label}** (`{latency:.0f} ms`)\n"
                    f"Validator: {verdict}\n"
                    f"{raw}"
                )

            reply = (
                f"🔬 **A/B Demo — Triage: {urgency.upper()} ({current_lang})**\n"
                f"Query: _{query}_\n\n"
                f"{_fmt_side('Model A: Baseline (google/gemma-2-2b-it)', cmp_res['base'])}\n\n"
                f"---\n\n"
                f"{_fmt_side('Model B: Fine-Tuned (Chewie 1.2 QLoRA)', cmp_res['finetuned'])}"
            )
            return {
                "chat_id": chat_id,
                "text": reply,
                "triage_category": urgency.upper(),
                "compare_available": True,
                "compare_result": cmp_res,
            }

        else:
            return {"chat_id": chat_id, "text": f"Unknown command '{cmd}'. Type /help to see all available features.", "triage_category": "ROUTINE"}

    # =========================================================================
    # Account Deletion Confirmation Flow
    # =========================================================================
    def _start_delete_confirmation(self, user_id: str, chat_id: str, current_lang: str) -> Dict[str, Any]:
        """Prompts user for explicit confirmation before erasing personal account data."""
        self.user_store.set_registration_step(user_id, "completed", {"awaiting_delete_confirm": True})
        prompt = get_localized_string("delete_confirm_prompt", current_lang)
        markup = {
            "inline_keyboard": [
                [{"text": "⚠️ Confirm Deletion", "callback_data": "menu:delete_confirm"}],
                [{"text": "❌ Cancel", "callback_data": "menu:delete_cancel"}]
            ]
        }
        return {"chat_id": chat_id, "text": prompt, "reply_markup": markup, "triage_category": "ROUTINE"}

    def _handle_delete_confirmation(self, user_id: str, chat_id: str, text: str, current_lang: str) -> Dict[str, Any]:
        norm = text.strip().lower()
        if norm in ("confirm", "/confirm_delete", "yes", "delete", "fowosi", "fọwọsi", "/fowosi", "/fọwọsi"):
            self.user_store.delete_user(user_id)
            ack = get_localized_string("data_deleted", current_lang)
            return {"chat_id": chat_id, "text": f"🗑️ {ack}", "triage_category": "ROUTINE"}
        else:
            self.user_store.set_registration_step(user_id, "completed", {"awaiting_delete_confirm": False})
            ack = get_localized_string("delete_cancelled", current_lang)
            menu_text, menu_markup = self._build_main_menu(current_lang)
            return {"chat_id": chat_id, "text": f"{ack}\n\n{menu_text}", "reply_markup": menu_markup, "triage_category": "ROUTINE"}

    # =========================================================================
    # Reminder Helpers
    # =========================================================================
    def _handle_vax_command(self, user_id: str, chat_id: str, current_lang: str) -> Dict[str, Any]:
        """Schedules routine infant vaccination schedule based on infant birth date."""
        user = self.user_store.get_user(user_id)
        dob = user.get("baby_birth_date") if user else None
        if not dob:
            msg = (
                "To schedule your baby's vaccination reminders, we need baby's date of birth.\n"
                "Please update your profile using `/profile` or provide baby's birth date."
            )
            return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}

        scheduled_ids = self.reminder_engine.schedule_infant_vaccination_series(user_id, dob)
        msg = (
            f"💉 **Infant Routine Vaccination Schedule Activated!**\n\n"
            f"Scheduled {len(scheduled_ids)} milestones according to Nigeria's National Primary Health Care "
            f"Development Agency (NPHCDA) immunization schedule for birth date {dob}.\n\n"
            f"You will receive reminders 2 days prior to each immunization session. Use /remind to view them."
        )
        return {"chat_id": chat_id, "text": msg, "triage_category": "ROUTINE"}

    # =========================================================================
    # Location Services
    # =========================================================================
    def _handle_location(self, user_id: str, lat: float, lon: float, lang: str) -> str:
        if lat is None or lon is None:
            return "Could not retrieve GPS coordinates. Please try sharing your location again."
        return self.location_service.format_location_response(lat, lon, lang)

    # =========================================================================
    # Profile & Main Menu Formatters
    # =========================================================================
    def _format_profile(self, user_id: str, lang: str) -> str:
        user = self.user_store.get_user(user_id)
        if not user:
            return "No profile found. Type /start to register."

        alias = user.get("alias") or "Not set"
        group = user.get("user_group")
        group_str = "Pregnant Woman" if group == "pregnant_woman" else "Mother / Caregiver of Infant" if group == "mother_infant" else "Not set"
        edd = user.get("expected_delivery_date") or "N/A"
        dob = user.get("baby_birth_date") or "N/A"
        consent = "Granted" if user.get("consent_given") else "Not granted"
        consent_dt = user.get("consent_date") or "N/A"

        return (
            f"👤 **MotherlyPulse Profile:**\n\n"
            f"• **Telegram User ID:** `{user_id}`\n"
            f"• **Preferred Alias:** {alias}\n"
            f"• **User Category:** {group_str}\n"
            f"• **Expected Delivery Date:** {edd}\n"
            f"• **Baby's Date of Birth:** {dob}\n"
            f"• **Language:** {user.get('language', 'English')}\n"
            f"• **Timezone:** {user.get('timezone', 'Africa/Lagos')} (WAT)\n"
            f"• **Consent Status:** {consent} (Recorded: {consent_dt})\n\n"
            f"Type `/language` to switch language, `/remind` for reminders, or `/delete` to erase data."
        )

    def _build_main_menu(self, language: str) -> Tuple[str, Dict[str, Any]]:
        """Generates the Main Menu text and native Telegram inline keyboard."""
        menu_title = (
            "📱 **MotherlyPulse Main Menu:**\n"
            "Select an option below or type a command:"
            if language == "English" else
            "📱 **Akojọ Aṣayan MotherlyPulse:**\n"
            "Yan aṣayan kan lati isalẹ tabi tẹ ilana rẹ:"
            if language == "Yoruba" else
            "📱 **MotherlyPulse Main Menu:**\n"
            "Pick wetin you wan do below or type command:"
        )

        markup = {
            "inline_keyboard": [
                [
                    {"text": "👤 My Profile", "callback_data": "menu:profile"},
                    {"text": "🌐 Language", "callback_data": "menu:language"}
                ],
                [
                    {"text": "📅 Clinic Visit", "callback_data": "menu:apt"},
                    {"text": "💊 Medicine Reminder", "callback_data": "menu:med"}
                ],
                [
                    {"text": "💉 Vaccine Schedule", "callback_data": "menu:vax"},
                    {"text": "🏥 Find Clinic", "callback_data": "menu:clinic"}
                ],
                [
                    {"text": "ℹ️ Help & Guide", "callback_data": "menu:help"},
                    {"text": "🗑️ Delete Account", "callback_data": "menu:delete"}
                ]
            ]
        }
        return menu_title, markup

    # =========================================================================
    # Telegram API Network Dispatchers
    # =========================================================================
    def send_telegram_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Sends an outbound message to Telegram API with optional keyboard markup."""
        if not self.bot_token:
            logger.warning("No TELEGRAM_BOT_TOKEN set; skipping network dispatch.")
            return False

        url = f"{TELEGRAM_API_BASE}{self.bot_token}/sendMessage"
        payload_data: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text
        }
        if reply_markup:
            payload_data["reply_markup"] = reply_markup

        payload = json.dumps(payload_data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
            return False

    def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None) -> bool:
        """Acknowledges a callback query from an inline keyboard button."""
        if not self.bot_token:
            return False
        url = f"{TELEGRAM_API_BASE}{self.bot_token}/answerCallbackQuery"
        payload_data = {"callback_query_id": callback_query_id}
        if text:
            payload_data["text"] = text
        payload = json.dumps(payload_data).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to answer callback query {callback_query_id}: {e}")
            return False

    def check_and_dispatch_due_reminders(self, current_time_iso: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Polls for due reminders, dispatches notifications to users in their registered language,
        and marks them delivered in SQLite to prevent duplicate delivery upon application restarts.
        """
        due = self.reminder_engine.process_due_reminders(current_time_iso)
        for r in due:
            uid = r.get("user_id")
            user = self.user_store.get_user(uid)
            lang = user.get("language", "English") if user else "English"
            msg = self.reminder_engine.format_reminder_notification(r, lang)
            self.send_telegram_message(uid, msg)
        return due

    def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """Validates the bot token and returns basic bot profile metadata."""
        if not self.bot_token:
            return None
        url = f"{TELEGRAM_API_BASE}{self.bot_token}/getMe"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("ok"):
                    return data.get("result")
        except Exception as e:
            logger.error(f"Failed to connect to Telegram getMe API: {e}")
            return None

    def poll_updates_once(self, offset: Optional[int] = None) -> Tuple[Optional[int], list]:
        """Polls getUpdates once via long polling, handling messages and callback queries."""
        if not self.bot_token:
            return offset, []

        # Periodically dispatch due scheduled reminders
        self.check_and_dispatch_due_reminders()

        url = f"{TELEGRAM_API_BASE}{self.bot_token}/getUpdates?timeout=20"
        if offset is not None:
            url += f"&offset={offset}"

        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                updates = data.get("result", [])
                max_update_id = offset
                for u in updates:
                    uid = u.get("update_id")
                    if uid is not None and (max_update_id is None or uid >= max_update_id):
                        max_update_id = uid + 1
                    # Process update
                    resp_dict = self.process_update(u)
                    if "chat_id" in resp_dict and "text" in resp_dict:
                        self.send_telegram_message(
                            resp_dict["chat_id"],
                            resp_dict["text"],
                            resp_dict.get("reply_markup")
                        )
                return max_update_id, updates
        except Exception as e:
            logger.error(f"Error polling Telegram updates: {e}")
            return offset, []


def run_bot(token: Optional[str] = None):
    """Interactive entry point for running the bot daemon."""
    if not token:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token and len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        token = sys.argv[1].strip()
    if not token and os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    if not token:
        print("=" * 60)
        print("  MotherlyPulse Telegram Bot Launcher")
        print("=" * 60)
        print("No TELEGRAM_BOT_TOKEN found in environment or .env file.")
        try:
            token = input("Please paste your Telegram Bot Token: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

    if not token:
        print("ERROR: A valid Telegram Bot Token is required.")
        sys.exit(1)

    bot = TelegramBotHandler(bot_token=token)
    info = bot.get_bot_info()
    if not info:
        print("ERROR: Could not connect to Telegram with provided token.")
        print("Please verify your bot token with @BotFather.")
        sys.exit(1)

    bot_user = info.get("username", "UnknownBot")
    bot_name = info.get("first_name", "MotherlyPulse")
    print("=" * 60)
    print(f" MotherlyPulse Bot Live: @{bot_user} ({bot_name})")
    print(" Listening for messages via Telegram Long Polling...")
    print(" Open Telegram and send /start to your bot!")
    print(" Press Ctrl+C to stop.")
    print("=" * 60)

    offset = None
    while True:
        try:
            offset, _ = bot.poll_updates_once(offset)
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected bot loop error: {e}")


if __name__ == "__main__":
    run_bot()