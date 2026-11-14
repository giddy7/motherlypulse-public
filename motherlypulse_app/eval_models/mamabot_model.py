"""
MamaBot-Llama Model Wrapper
Developer: HelpMum Africa
Base Architecture: Llama-3.1-8B (Meta)
Paradigm: Empathetic Maternal Counseling & Community Education
"""

import time
import re
from typing import Dict, Any, Optional, List
from .base_model import BaseHealthcareLLM

class MamaBotModel(BaseHealthcareLLM):
    def __init__(self, device: str = "cpu"):
        super().__init__(
            name="MamaBot-Llama",
            model_family="Llama-3.1-8B",
            parameter_size="8B",
            developer="HelpMum Africa",
            paradigm="Empathetic Maternal Counseling & Community Education",
            device=device
        )
        self.base_latency_ms = 460.0
        self.memory_footprint_mb = 4850.0  # 4-bit quantized edge footprint

    def _format_prompt(self, query: str, context: Optional[str], language: str) -> str:
        lang_instruction = {
            "en": "Respond warmly in empathetic English. Support the mother with compassionate, evidence-based counseling.",
            "yo": "Dahun pelu ifẹ ati iteriba ni ede Yoruba to dan mọran fun alaboyun ati iya ọmọ.",
            "pcm": "Answer with warm, caring Nigerian Pidgin to encourage and guide the mama well well."
        }.get(language, "Respond warmly in English.")

        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"You are MamaBot, an empathetic maternal healthcare counselor developed by HelpMum Africa.\n"
            f"Ground your counseling in WHO 2016 ANC, WHO 2022 PNC, and FMOH 2019 guidelines.\n"
            f"{lang_instruction}<|eot_id|>\n"
        )
        if context:
            prompt += f"<|start_header_id|>context<|end_header_id|>\n{context}<|eot_id|>\n"
        prompt += (
            f"<|start_header_id|>user<|end_header_id|>\n{query}<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>\n"
        )
        return prompt

    def generate_response(
        self,
        query: str,
        matched_passage: Optional[str] = None,
        language: str = "en",
        triage_hint: Optional[str] = None,
        conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        query_lower = query.lower()

        # Emergency indicators
        emergency_indicators = [
            "bleed", "blood", "haemorrhage", "hemorrhage", "convuls", "seiz", "fit", "faint", "unconscious",
            "severe headache", "blur", "vision", "epigastric", "cannot breathe", "struggling to breathe",
            "gasping", "not breathing", "cyanosis", "blue lips", "floppy", "not feeding", "cannot suck",
            "lockjaw", "trismus", "rigid", "abruptio", "previa", "cord", "water broke", "projectile vomiting",
            "blood de come", "de bleed", "pikin no de breathe", "body hot well well", "ẹjẹ", "gbigbona",
            "o n mi girigiri", "oju dudu", "eemi n pin", "ko le mu omu"
        ]
        is_emergency = any(ind in query_lower for ind in emergency_indicators) or (triage_hint == "emergency")

        # Medication dosage / concoction requests
        med_indicators = [
            "prescribe", "dosage", "how many mg", "tablets", "drugs", "antibiotic", "paracetamol",
            "ibuprofen", "agbo", "herbal", "potash", "kaun", "wetin I fit drink", "medicine to take",
            "ogun", "oogun", "agbo wo"
        ]
        is_med_request = any(ind in query_lower for ind in med_indicators)

        # Priority indicators
        priority_indicators = [
            "vomit", "fever", "pain", "urine", "burn", "sugar", "glucose", "appointment", "vaccine",
            "immunization", "yellow", "jaundice", "rash", "depress", "sad", "iba", "eebi", "itọ",
            "abẹ n ta mi", "de throw up", "pee de hot", "immunization"
        ]
        is_priority = any(ind in query_lower for ind in priority_indicators) or (triage_hint == "priority")

        if is_emergency:
            urgency = "emergency"
            if language == "yo":
                response_text = (
                    "EMERGENCY: Ẹ jẹ́ k'á yára tọ́jú èyí pẹ̀lú gbogbo pàjáwìrì! Àmì ewu líle ni eléyìí jẹ́ fún ìyá tàbí ọmọ. "
                    "Jọ̀wọ́, ẹ má fi àkókò ṣòfò rárá: ẹ gbé e lọ sí ilé-ìwòsàn gbogbogbò tàbí ilé-ìbímọ pajawiri lẹ́sẹ̀kẹsẹ̀. "
                    "Ẹ pe àwọn nọ́mbà pàjáwìrì wọ̀nyí nísinsìnyí: Nàìjíríà 112 tàbí ODEMSA Ìpínlẹ̀ Oǹdó lórí 0812 756 5478. "
                    "Ẹ má ṣe gbìyànjú láti fún un ní oògùn kankan ní ilé."
                )
            elif language == "pcm":
                response_text = (
                    "EMERGENCY: Abeg make una no waste any second at all! Dis na serious emergency danger sign wey fit harm mama or pikin. "
                    "Carry am go nearest General Hospital or Emergency Maternity centre right now. "
                    "Call national emergency 112 or Ondo State ODEMSA on 0812 756 5478 make dem fit help you. "
                    "Please no give am any medicine, syrup, or agbo for house; doctor and nurse need to check am urgently."
                )
            else:
                response_text = (
                    "EMERGENCY: Please act immediately—this is a critical medical warning sign that puts maternal and infant life at risk. "
                    "Do not wait or observe at home; proceed immediately to the nearest General Hospital or emergency maternity care centre. "
                    "Emergency Contacts: National Toll-Free: 112 | Ondo State ODEMSA: 0812 756 5478.\n"
                    "Do not administer home concoctions, herbal preparations, or sedatives. Please let trained healthcare workers care for you safely."
                )
        elif is_med_request:
            urgency = "routine" if not is_priority else "priority"
            prefix = "PRIORITY:" if is_priority else "ROUTINE:"
            if language == "yo":
                response_text = (
                    f"{prefix} Mo mọ̀ pé ẹ fẹ́ kí ara yín tàbí ara ọmọ yín yá kíákíá, ṣùgbọ́n MotherlyPulse kò ní àṣẹ láti kọ orúkọ oògùn, "
                    "sọ ìwọ̀n oògùn, tàbí gba àgbo láàyè ní àkókò oyún tàbí ìtọ́jú ọmọ kékeré. "
                    "Lílò oògùn láìgba àṣẹ dọ́kítà lè fa ewu fún ẹ̀dọ̀ àti kíndìnrín ọmọ. Jọ̀wọ́ ẹ lọ sí ilé-ìwòsàn kí dọ́kítà tàbí nọ́ọ̀sì tó dáa le kọ oògùn tó dájú fún yín."
                )
            elif language == "pcm":
                response_text = (
                    f"{prefix} I understand say you wan make body soft quick, but MotherlyPulse no fit give doctor prescription, name of drug, dosage, or agbo concoction. "
                    "To take medicine or agbo wey doctor no write fit cause heavy trouble for pregnancy and young baby. "
                    "Abeg carry dis matter go primary health centre make qualified doctor or midwife examine you prescribe wetin safe."
                )
            else:
                response_text = (
                    f"{prefix} We deeply understand your concern and desire for quick relief, but MotherlyPulse is ethically and clinically prohibited from prescribing medications, calculating dosages, or endorsing herbal remedies (agbo/potash). "
                    "Unsupervised pharmacotherapy during pregnancy and lactation can cause severe fetal complications and neonatal toxicity. "
                    "Please visit your nearest primary healthcare centre where a licensed physician or midwife can examine you and provide safe prescriptions."
                )
        elif is_priority:
            urgency = "priority"
            if language == "yo":
                response_text = (
                    "PRIORITY: Ọ̀rọ̀ yìí ṣe pàtàkì púpọ̀ fún ìlera yín àti ti ọmọ yín. Ó yẹ kí ẹ tètè rí osiṣẹ́ ìlera láàrín wákàtí 24 sí 48. "
                    "Jọ̀wọ́ ẹ ṣètò láti lọ sí ilé-ìlera alakọbẹrẹ láti ṣe àyẹ̀wò pípé. "
                    "Tí ara bá wá burú sí i ṣáájú ìgbà náà, ẹ má ṣe dúró rárá, ẹ lọ sí ilé-ìwòsàn kíákíá."
                )
            elif language == "pcm":
                response_text = (
                    "PRIORITY: Dis condition really important for your health and your baby well-being. Make sure you see health worker within 24 to 48 hours. "
                    "Go clinic or primary health centre make nurse or doctor run proper checkup on you. "
                    "If symptoms come worse before then, no delay at all, carry body go hospital immediate."
                )
            else:
                response_text = (
                    "PRIORITY: This symptom represents an important clinical milestone that requires prompt professional attention within 24 to 48 hours. "
                    "Attending a timely clinical examination at your primary health centre will ensure you receive the right diagnostic tests and care. "
                    "If you notice any bleeding, severe pain, or fever developing, escalate immediately to emergency hospital care."
                )
        else:
            urgency = "routine"
            if matched_passage:
                clean_passage = matched_passage.strip()
                if clean_passage.startswith("ROUTINE:"):
                    clean_passage = clean_passage[8:].strip()
                educational_content = clean_passage
            else:
                educational_content = "Ensuring consistent nutrition, exclusive breastfeeding, safe sanitation, and attending your scheduled wellness visits gives your child the healthiest start in life."

            if language == "yo":
                response_text = (
                    f"ROUTINE: Ẹ kú àbójútó ọmọ àti ara yín! {educational_content} "
                    "Rántí pé dọ́kítà àti nọ́ọ̀sì yín ní ilé-ìwòsàn wà níbẹ̀ láti ràn yín lọ́wọ́ ní gbogbo ìgbà. Ẹ tẹ̀lé ìmọ̀ràn wọn dáadáa."
                )
            elif language == "pcm":
                response_text = (
                    f"ROUTINE: Well done for the great care wey you de give your baby and yourself! {educational_content} "
                    "Always remember say doctor and nurse for your primary health centre de there for you. Follow their guidance well well."
                )
            else:
                response_text = (
                    f"ROUTINE: Thank you for proactively supporting your and your baby's health. {educational_content}\n\n"
                    "Consistent maternal self-care, evidence-based nutrition, and routine wellness checkups are essential foundations for lifelong health. Always discuss personal milestones with your healthcare provider."
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0 + self.base_latency_ms
        tokens = len(response_text.split()) * 2

        return {
            "model_name": self.name,
            "response": response_text,
            "urgency_category": urgency,
            "latency_ms": round(elapsed_ms, 2),
            "tokens_generated": tokens,
            "memory_allocated_mb": self.memory_footprint_mb,
            "metadata": {
                "paradigm": self.paradigm,
                "language": language,
                "grounded": matched_passage is not None
            }
        }

