"""
MotherlyPulse Core Response & Safety Engine
Handles user messages in English, Yoruba, and Nigerian Pidgin.
Routes based on dynamic urgency classification, provides safe grounded educational answers,
and formats emergency escalations.
Enforces strict category prefixes: 'EMERGENCY:', 'PRIORITY:', 'ROUTINE:'.
Decouples clinical urgency from medication safety.
Integrates Phase 1: Deterministic Template-Based Conversational Adaptation Engine.
"""

import logging
from typing import Dict, Any, List, Optional
from .classifier import DynamicTriageClassifier
from .template_adapter import TemplateAdaptationEngine
from .ai_connector import AIModelConnector

logger = logging.getLogger(__name__)

class MotherlyPulseAssistant:
    def __init__(
        self,
        language: str = "English",
        enable_adaptation: bool = True,
        ai_connector: Optional[AIModelConnector] = None
    ):
        self.language = language
        self.enable_adaptation = enable_adaptation
        self.classifier = DynamicTriageClassifier()
        self.adapter = TemplateAdaptationEngine()
        self.ai_connector = ai_connector or AIModelConnector()
        
        # Supported languages (English, Yoruba, Nigerian Pidgin)
        self.supported_languages = ["English", "Yoruba", "Nigerian Pidgin"]
        
        # Fixed emergency template
        self.emergency_templates = {
            "English": (
                "EMERGENCY: This is a critical medical warning sign that requires immediate medical attention. "
                "Please do not wait. Go immediately to the nearest hospital or emergency maternity centre.\n"
                "Emergency Contacts:\n"
                "- National Emergency: Call 112 (Toll-Free)\n"
                "- Ondo State Emergency Medical Services (ODEMSA): 0812 756 5478\n"
                "If you can safely travel, proceed to your nearest General Hospital or Comprehensive Health Centre now."
            ),
            "Yoruba": (
                "EMERGENCY: Eyi jẹ ami eewu ilera to le koko ti o nilo itọju ile-iwosan lẹsẹkẹsẹ. "
                "Ẹ jọwọ ẹ ma ṣe duro. Ẹ lọ lẹsẹkẹsẹ si ile-iwosan ti o sunmọ julọ tabi ile-iṣẹ pajawiri alaboyun.\n"
                "Awọn nọmba pajawiri:\n"
                "- Pajawiri ti Orilẹ-ede: Pe 112 (Ọfẹ)\n"
                "- Pajawiri Ipinle Ondo (ODEMSA): 0812 756 5478\n"
                "Ti ẹ ba le rin irin-ajo lailewu, ẹ lọ si Ile-iwosan Gbogbogbo tabi Ile-iṣẹ Ilera to peye lẹsẹkẹsẹ."
            ),
            "Nigerian Pidgin": (
                "EMERGENCY: This na serious danger sign wey need quick medical attention for hospital now-now. "
                "Abeg make you no wait at all. Go immediately to the nearest hospital or emergency maternity clinic.\n"
                "Emergency Phone Numbers:\n"
                "- National Emergency: Call 112 (Toll-Free)\n"
                "- Ondo State Emergency Medical Services (ODEMSA): 0812 756 5478\n"
                "If you fit travel safely, make you carry body go the nearest General Hospital or Comprehensive Health Centre right now."
            )
        }
        
        # Fixed emergency + medication decline template
        self.emergency_med_templates = {
            "English": (
                "EMERGENCY: This is a critical medical warning sign requiring immediate hospital care. "
                "MotherlyPulse cannot provide medication prescriptions or dosages. "
                "Do not attempt to self-medicate or delay emergency care; proceed immediately to the nearest hospital emergency unit.\n"
                "Emergency Contacts: National 112 | Ondo ODEMSA: 0812 756 5478."
            ),
            "Yoruba": (
                "EMERGENCY: Eyi jẹ ami eewu to le koko ti o nilo itọju ile-iwosan ni kiakia. "
                "MotherlyPulse ko le kọ oogun tabi sọ iye oogun ti ẹ gbọdọ lo. "
                "Ẹ ma ṣe lo oogun ti dokita ko kọ fun yin tabi fi itọju pajawiri falẹ; ẹ lọ lẹsẹkẹsẹ si ile-iwosan to sunmọ.\n"
                "Awọn nọmba pajawiri: Orilẹ-ede 112 | Ondo ODEMSA: 0812 756 5478."
            ),
            "Nigerian Pidgin": (
                "EMERGENCY: This na heavy danger sign wey need urgent hospital care right now. "
                "MotherlyPulse no fit give medicine prescription or tell you dose to drink. "
                "Make you no drink any medicine by yourself or delay emergency care; carry body go hospital now-now.\n"
                "Emergency Numbers: National 112 | Ondo ODEMSA: 0812 756 5478."
            )
        }

        # Fixed priority + medication decline template
        self.priority_med_templates = {
            "English": (
                "PRIORITY: This symptom requires prompt clinical evaluation by a qualified healthcare professional. "
                "MotherlyPulse cannot prescribe medications or provide dosages. "
                "Please visit your primary healthcare clinic or hospital today so a doctor or midwife can examine you safely."
            ),
            "Yoruba": (
                "PRIORITY: Aami aisan yi nilo ayẹwo to daju lati ọwọ oṣiṣẹ ilera ti o pegede. "
                "MotherlyPulse ko le kọ oogun tabi sọ iye ti ẹ gbọdọ lo. "
                "Ẹ jọwọ ẹ lọ si ile-iṣẹ ilera alakọbẹrẹ tabi ile-iwosan loni ki dokita tabi agbẹbi le yẹ yin wo lailewu."
            ),
            "Nigerian Pidgin": (
                "PRIORITY: This symptom need beta checkup from qualified health worker today. "
                "MotherlyPulse no fit write medicine prescription or give dosage. "
                "Abeg make you visit your primary health clinic or hospital today make doctor or nurse examine you well."
            )
        }
        
        # Fixed routine medication / dosage decline template
        self.decline_templates = {
            "English": (
                "ROUTINE: MotherlyPulse cannot prescribe medications, recommend dosages, or recommend herbal mixtures (agbo). "
                "Taking unverified medicines or concoctions during pregnancy and breastfeeding can harm both you and your baby. "
                "Please speak directly with your doctor, nurse, or midwife at your primary health centre."
            ),
            "Yoruba": (
                "ROUTINE: MotherlyPulse ko le kọ oogun, sọ iye oogun ti ẹ gbọdọ lo, tabi gbani niyanju lati mu agbo. "
                "Lilo awọn oogun ti dokita ko fọwọsi tabi agbo lasiko oyun ati igba to n fun ọmọ ni ọmu le ṣe ipalara fun ẹyin ati ọmọ yin. "
                "Ẹ jọwọ ẹ ba dokita tabi agbẹbi yin sọrọ ni ile-iṣẹ ilera alakọbẹrẹ yin."
            ),
            "Nigerian Pidgin": (
                "ROUTINE: MotherlyPulse no fit prescribe medicine, recommend dose, or tell you make you drink agbo. "
                "Drinking medicine wey doctor no approve or taking herbal concoctions during pregnancy and breastfeeding fit harm you and your pikin. "
                "Abeg talk directly with your doctor, nurse, or midwife for your primary health centre."
            )
        }

    def set_language(self, language: str) -> bool:
        if language in self.supported_languages:
            self.language = language
            return True
        return False

    def respond(
        self,
        message: Optional[str] = None,
        conversation_history: List[str] = None,
        matched_passage: str = None,
        language: Optional[str] = None,
        user_group: Optional[str] = None,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a user message and returns a structured response with urgency classification.
        Guarantees that response starts with 'EMERGENCY:', 'PRIORITY:', or 'ROUTINE:'.
        When enable_adaptation is True, applies four-slot conversational adaptation while
        preserving the exact clinical advice, warnings, and contacts.
        Emergency responses strictly bypass conversational adaptation with zero delay.
        If an unsupported language is requested, returns an explicit language limitation notice.
        If adaptation throws an unexpected error, safely falls back to the exact reference response.
        """
        if message is None and user_message is not None:
            message = user_message
        if message is None:
            message = ""
        # 1. Resolve requested language if provided
        active_language = self.language
        is_supported_language = True
        requested_lang_str = None
        if language is not None:
            clean_lang = str(language).strip()
            requested_lang_str = clean_lang
            lang_mapping = {
                "en": "English", "english": "English",
                "yo": "Yoruba", "yoruba": "Yoruba",
                "pcm": "Nigerian Pidgin", "pidgin": "Nigerian Pidgin", "nigerian pidgin": "Nigerian Pidgin"
            }
            resolved = lang_mapping.get(clean_lang.lower())
            if resolved:
                active_language = resolved
            else:
                is_supported_language = False

        # 2. Dynamic triage classification (Runs BEFORE language gating)
        triage = self.classifier.classify(message, conversation_history)
        category = triage["urgency_category"]
        med_safety = triage["medication_safety_triggered"]
        
        # 3. Handle EMERGENCY: Strict Emergency Bypass (No conversational delay)
        # Emergency classification is independent of requested language and is NEVER downgraded
        if category == "emergency":
            if is_supported_language:
                if med_safety:
                    reply_text = self.emergency_med_templates.get(active_language) or self.emergency_med_templates["English"]
                else:
                    reply_text = self.emergency_templates.get(active_language) or self.emergency_templates["English"]
            else:
                base_tmpl = self.emergency_med_templates["English"] if med_safety else self.emergency_templates["English"]
                reply_text = (
                    f"{base_tmpl}\n\n"
                    f"Notice: You requested '{requested_lang_str}'. While MotherlyPulse cannot converse in '{requested_lang_str}', "
                    "a critical medical emergency was detected. Please call 112 or ODEMSA immediately as instructed above."
                )
                
            return {
                "user_message": message,
                "urgency_category": "emergency",
                "medication_safety_triggered": med_safety,
                "language": active_language if is_supported_language else "English",
                "requested_language": requested_lang_str,
                "response": reply_text,
                "reply": reply_text,
                "classification_metadata": triage,
                "delay_incurred": False,
                "adaptation_metadata": {
                    "adaptation_applied": False,
                    "reason": "Emergency bypass applied - zero conversational delay"
                },
                "action": "Immediate Emergency Hospital Escalation"
            }

        # 4. Handle Unsupported Language when Emergency was NOT established
        # CRITICAL: Never report 'routine' as an assessed result for unsupported languages!
        if not is_supported_language:
            notice = (
                "MotherlyPulse currently provides verified clinical responses in English, Yoruba, and Nigerian Pidgin. "
                f"Support for '{requested_lang_str}' is not yet available, and medical urgency cannot be reliably assessed in this language. "
                "For urgent medical concerns or emergencies, please call emergency services immediately at 112 or visit your nearest healthcare facility."
            )
            return {
                "user_message": message,
                "urgency_category": "unassessed",
                "medication_safety_triggered": False,
                "language": "English",
                "requested_language": requested_lang_str,
                "status": "language_not_supported",
                "supported_languages": list(self.supported_languages),
                "response": notice,
                "reply": notice,
                "classification_metadata": {
                    "triage": "unassessed",
                    "reason": f"Input language '{requested_lang_str}' unsupported; urgency cannot be reliably determined"
                },
                "adaptation_metadata": {
                    "adaptation_applied": False,
                    "reason": f"Language '{requested_lang_str}' unsupported. Explicit language limitation notice returned."
                },
                "action": "Language Guidance / Emergency Referral"
            }
        
        # 2. Handle PRIORITY
        if category == "priority":
            if med_safety:
                base_reply = self.priority_med_templates.get(active_language) or self.priority_med_templates["English"]
            elif matched_passage:
                clean_passage = matched_passage.strip()
                if not clean_passage.startswith("PRIORITY:"):
                    clean_passage = f"PRIORITY: {clean_passage}"
                base_reply = f"{clean_passage}\n\nNote: Please attend your scheduled clinic visit or consult your health worker promptly."
            else:
                base_reply = (
                    "PRIORITY: This is an important, time-sensitive healthcare milestone. "
                    "Addressing this promptly protects your health and your baby's development. "
                    "Please consult your health worker or attend your scheduled clinic visit within 24 to 48 hours."
                )
                
            if self.ai_connector and self.ai_connector.backend != "disabled" and not med_safety:
                ai_res = self.ai_connector.generate_response(
                    user_message=message,
                    urgency_category="priority",
                    language=active_language,
                    reference_response=base_reply
                )
                final_response = ai_res["response"]
                adapt_meta = {
                    "adaptation_applied": True,
                    "ai_generated": ai_res.get("ai_generated", False),
                    "model_used": ai_res.get("model_used", ""),
                    "safety_validated": ai_res.get("safety_validated", True),
                    "latency_ms": ai_res.get("latency_ms", 0.0),
                    "fallback_triggered": ai_res.get("fallback_triggered", False),
                    "validation_details": ai_res.get("validation_details", {})
                }
            elif self.enable_adaptation:
                try:
                    adapt_res = self.adapter.adapt_response(
                        user_message=message,
                        reference_response=base_reply,
                        urgency_category="priority",
                        language=active_language
                    )
                    final_response = adapt_res["adapted_response"]
                    adapt_meta = adapt_res
                except Exception as e:
                    logger.error(f"Priority adaptation error: {e}", exc_info=True)
                    final_response = base_reply
                    adapt_meta = {
                        "adaptation_applied": False,
                        "fallback_triggered": True,
                        "error": str(e),
                        "reason": "Exception during response adaptation; safe fallback to reference response"
                    }
            else:
                final_response = base_reply
                adapt_meta = {"adaptation_applied": False, "reason": "Adaptation disabled"}

            return {
                "user_message": message,
                "urgency_category": "priority",
                "medication_safety_triggered": med_safety,
                "language": active_language,
                "response": final_response,
                "reply": final_response,
                "classification_metadata": triage,
                "adaptation_metadata": adapt_meta,
                "ai_generated": adapt_meta.get("ai_generated", False),
                "model_used": adapt_meta.get("model_used", "TemplateEngine"),
                "action": "Prompt Clinical Follow-up"
            }
            
        # 3. Handle ROUTINE
        if med_safety:
            base_reply = self.decline_templates.get(active_language) or self.decline_templates["English"]
            if self.enable_adaptation:
                try:
                    adapt_res = self.adapter.adapt_response(
                        user_message=message,
                        reference_response=base_reply,
                        urgency_category="routine",
                        language=active_language
                    )
                    final_response = adapt_res["adapted_response"]
                    adapt_meta = adapt_res
                except Exception as e:
                    logger.error(f"Routine safety adaptation error: {e}", exc_info=True)
                    final_response = base_reply
                    adapt_meta = {
                        "adaptation_applied": False,
                        "fallback_triggered": True,
                        "error": str(e),
                        "reason": "Exception during response adaptation; safe fallback to reference response"
                    }
            else:
                final_response = base_reply
                adapt_meta = {"adaptation_applied": False, "reason": "Adaptation disabled"}

            return {
                "user_message": message,
                "urgency_category": "routine",
                "medication_safety_triggered": True,
                "language": active_language,
                "response": final_response,
                "reply": final_response,
                "classification_metadata": triage,
                "adaptation_metadata": adapt_meta,
                "action": "Clinical Safety Decline"
            }
            
        # Standard routine educational inquiry
        if matched_passage:
            clean_passage = matched_passage.strip()
            if not clean_passage.startswith("ROUTINE:"):
                clean_passage = f"ROUTINE: {clean_passage}"
            base_reply = clean_passage
        else:
            base_reply = (
                "ROUTINE: Attending routine checkups and practicing healthy nutrition and care routines support you and your baby. "
                "Always follow the personalized care guidance provided by your doctor or midwife at your health centre."
            )
            
        if self.ai_connector and self.ai_connector.backend != "disabled":
            ai_res = self.ai_connector.generate_response(
                user_message=message,
                urgency_category="routine",
                language=active_language,
                reference_response=base_reply
            )
            final_response = ai_res["response"]
            adapt_meta = {
                "adaptation_applied": True,
                "ai_generated": ai_res.get("ai_generated", False),
                "model_used": ai_res.get("model_used", ""),
                "safety_validated": ai_res.get("safety_validated", True),
                "latency_ms": ai_res.get("latency_ms", 0.0),
                "fallback_triggered": ai_res.get("fallback_triggered", False),
                "validation_details": ai_res.get("validation_details", {})
            }
        elif self.enable_adaptation:
            try:
                adapt_res = self.adapter.adapt_response(
                    user_message=message,
                    reference_response=base_reply,
                    urgency_category="routine",
                    language=active_language
                )
                final_response = adapt_res["adapted_response"]
                adapt_meta = adapt_res
            except Exception as e:
                logger.error(f"Routine education adaptation error: {e}", exc_info=True)
                final_response = base_reply
                adapt_meta = {
                    "adaptation_applied": False,
                    "fallback_triggered": True,
                    "error": str(e),
                    "reason": "Exception during response adaptation; safe fallback to reference response"
                }
        else:
            final_response = base_reply
            adapt_meta = {"adaptation_applied": False, "reason": "Adaptation disabled"}

        return {
            "user_message": message,
            "urgency_category": "routine",
            "medication_safety_triggered": False,
            "language": active_language,
            "response": final_response,
            "reply": final_response,
            "classification_metadata": triage,
            "adaptation_metadata": adapt_meta,
            "ai_generated": adapt_meta.get("ai_generated", False),
            "model_used": adapt_meta.get("model_used", "TemplateEngine"),
            "action": "Educational Support & Wellness"
        }

    # Alias for backward and channel compatibility
    handle_message = respond
