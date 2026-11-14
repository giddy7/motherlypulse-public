"""
MotherlyPulse WhatsApp Cloud API Webhook Adapter
Parses inbound webhook events from Meta Cloud API (Graph API) and formats compliant outbound payloads.

Features:
- Webhook verification handling (hub.mode, hub.verify_token, hub.challenge).
- Inbound payload parser for Meta Cloud API format (text messages, location pins).
- Formats outbound replies according to Meta Cloud API schema.
- CLINICAL SAFETY INVARIANT:
    All inbound text messages are triaged for emergency danger signs FIRST.
    Emergency messages trigger immediate dial-112 escalation advice, bypassing regular dialog.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from .assistant import MotherlyPulseAssistant
from .classifier import DynamicTriageClassifier
from .user_store import UserStore
from .location_service import LocationService

logger = logging.getLogger(__name__)


class WhatsAppWebhookAdapter:
    def __init__(
        self,
        verify_token: Optional[str] = None,
        assistant: Optional[MotherlyPulseAssistant] = None,
        user_store: Optional[UserStore] = None,
        location_service: Optional[LocationService] = None
    ):
        self.verify_token = verify_token or os.environ.get("WHATSAPP_VERIFY_TOKEN", "MOTHERLYPULSE_VERIFY_TOKEN")
        self.assistant = assistant or MotherlyPulseAssistant()
        self.user_store = user_store or UserStore()
        self.location_service = location_service or LocationService()
        self.classifier = DynamicTriageClassifier()

    def verify_webhook(self, query_params: Dict[str, str]) -> Tuple[bool, str, int]:
        """
        Validates Meta's GET challenge verification request.
        Expects: hub.mode, hub.verify_token, hub.challenge
        """
        mode = query_params.get("hub.mode")
        token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge", "")

        if mode == "subscribe" and token == self.verify_token:
            return True, challenge, 200
        return False, "Verification token mismatch", 403

    def handle_incoming_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses an inbound POST payload from Meta Cloud API and returns a list of
        outbound message payloads ready for dispatch via Graph API.
        """
        outbound_payloads = []
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    response_obj = self._process_single_message(msg)
                    if response_obj:
                        outbound_payloads.append(response_obj)
        return outbound_payloads

    def _process_single_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg_from = message.get("from")
        if not msg_from:
            return None

        user_profile = self.user_store.get_user(msg_from)
        current_lang = user_profile["language"] if user_profile else "English"
        msg_type = message.get("type")

        # Location message handling
        if msg_type == "location":
            loc_data = message.get("location", {})
            lat = loc_data.get("latitude")
            lon = loc_data.get("longitude")
            reply_body = self._handle_location(lat, lon)
            return self._build_outbound_payload(msg_from, reply_body)

        # Text message handling
        if msg_type == "text":
            body = message.get("text", {}).get("body", "").strip()
            if not body:
                return None

            # PRIORITY EMERGENCY TRIAGE FIRST
            triage_res = self.classifier.classify(body)
            if triage_res.get("urgency_category") == "emergency":
                emergency_body = (
                    "EMERGENCY ALERT: This message describes a critical maternal/infant danger sign.\n\n"
                    "Please call 112 immediately or go to the nearest emergency health facility in Ondo State.\n\n"
                    "Do not wait. Dial 112 for urgent medical assistance."
                )
                return self._build_outbound_payload(msg_from, emergency_body)

            # Check for commands
            if body.startswith("/"):
                reply_body = self._handle_commands(msg_from, body, current_lang)
                return self._build_outbound_payload(msg_from, reply_body)

            # Standard conversational flow via assistant
            resp = self.assistant.handle_message(
                user_message=body,
                language=current_lang,
                user_group=user_profile.get("user_group") if user_profile else None
            )
            reply_text = resp.get("reply", "")
            return self._build_outbound_payload(msg_from, reply_text)

        # Unhandled message types (audio, image, etc.)
        return self._build_outbound_payload(
            msg_from,
            "MotherlyPulse currently supports text messages and shared location pins. Type /help for options."
        )

    def _handle_commands(self, user_id: str, cmd_text: str, current_lang: str) -> str:
        parts = cmd_text.split()
        cmd = parts[0].lower()

        if cmd == "/start":
            self.user_store.register_user(user_id=user_id, channel="whatsapp", language=current_lang)
            return (
                "Welcome to MotherlyPulse WhatsApp service. "
                "I provide maternal and infant health guidance for families in Ondo State.\n\n"
                "In any medical emergency, call 112 immediately.\n"
                "Commands:\n"
                "- /language english, /language yoruba, /language pidgin\n"
                "- /profile pregnant or /profile mother\n"
                "- /delete to delete your data"
            )
        elif cmd == "/language":
            if len(parts) > 1:
                arg = parts[1].lower()
                lang_map = {"english": "English", "yoruba": "Yoruba", "pidgin": "Nigerian Pidgin"}
                new_lang = lang_map.get(arg)
                if new_lang:
                    self.user_store.update_language(user_id, new_lang)
                    return f"Language updated to {new_lang}."
            return "Please specify: /language english, /language yoruba, or /language pidgin."
        elif cmd == "/delete":
            self.user_store.delete_user(user_id)
            return "Your profile and all data have been completely deleted."
        elif cmd == "/help":
            return (
                "MotherlyPulse Commands:\n"
                "/start - Restart assistant\n"
                "/language - Change language\n"
                "/delete - Erase data\n"
                "Or send your GPS location pin to find nearby clinics.\n"
                "Emergency: Call 112."
            )
        return "Unknown command. Type /help for assistance."

    def _handle_location(self, lat: Optional[float], lon: Optional[float]) -> str:
        if lat is None or lon is None:
            return "Could not determine GPS coordinates. Please share location pin again."

        facility = self.location_service.find_nearest_facility(lat, lon)
        imm = self.location_service.find_nearest_immunization_center(lat, lon)

        parts = ["Nearby Ondo State Facilities:"]
        if facility:
            parts.append(
                f"- Clinic: {facility['facility_name']} ({facility['facility_type']})\n"
                f"  Distance: {facility['distance_km']} km | LGA: {facility['lga']}\n"
                f"  Notice: {facility['disclaimer']}"
            )
        else:
            parts.append("- Clinic: No verified health facility found in immediate range.")

        if imm:
            sched = imm.get('immunization_schedule_days') or imm.get('session_frequency', 'Routine Clinic Days')
            parts.append(
                f"- Immunization: {imm['center_name']} ({sched})\n"
                f"  Distance: {imm['distance_km']} km | LGA: {imm['lga']}\n"
                f"  Notice: {imm['disclaimer']}"
            )
        else:
            parts.append("- Immunization: No verified immunization post found in range.")

        return "\n\n".join(parts)

    def _build_outbound_payload(self, to_phone: str, text: str) -> Dict[str, Any]:
        """
        Builds a compliant Meta Cloud API text message payload.
        Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/messages/text-messages
        """
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }
