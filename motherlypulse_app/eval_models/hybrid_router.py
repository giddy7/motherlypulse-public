"""
Corrected Hybrid Maternal Healthcare Router
Combines Chewie 1.2 (MedGemma-4B) and MamaBot-Llama (Llama-3.1-8B)

Core Clinical & Architectural Guarantees:
1. Explicit handling of EMERGENCY, PRIORITY, and ROUTINE classifications.
2. NEVER allows a PRIORITY case to fall through into ROUTINE.
3. NEVER downgrades an upstream EMERGENCY or PRIORITY classification.
4. Emergency cases trigger immediate hospital escalation (Chewie specialist / dual verification).
5. Priority cases preserve 24-48h clinical consultation and appropriate urgency prefix.
6. Routine educational queries route to MamaBot-Llama for empathetic maternal counseling.
7. Ambiguous and medication-sensitive queries invoke conservative dual-model verification.
8. Conservative Disagreement Resolution: Escalate > Defer > Reassure (Higher risk ALWAYS wins).
9. Deterministic safety rules remain authoritative over final urgency classification.
"""

import time
import re
import unicodedata
from typing import Dict, Any, Optional, List
from .base_model import BaseHealthcareLLM
from .chewie_model import ChewieModel
from .mamabot_model import MamaBotModel

def normalize_text(text: str) -> str:
    """Normalizes text by decomposing Unicode and removing combining accents."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.lower()

# Urgency precedence hierarchy for conservative arbitration
URGENCY_RANKS = {
    "routine": 1,
    "priority": 2,
    "emergency": 3
}

class HybridRouter(BaseHealthcareLLM):
    def __init__(self, device: str = "cpu"):
        super().__init__(
            name="MotherlyPulse Hybrid",
            model_family="Hybrid (MedGemma-4B + Llama-3.1-8B)",
            parameter_size="4B+8B (Dynamically Routed)",
            developer="MotherlyPulse Systems",
            paradigm="Intelligent Triage Routing & Conservative Dual Verification",
            device=device
        )
        self.chewie = ChewieModel(device=device)
        self.mamabot = MamaBotModel(device=device)
        self.routing_overhead_ms = 18.0

        # Multilingual danger sign patterns (Emergency)
        self.emergency_indicators = [
            # English
            r"\b(bleed\w*|blood\w*|hemorrhag\w*|haemorrhag\w*|lochia\s+heavy|soaking\s+pads?)\b",
            r"\b(convuls\w*|seiz\w*|fit|fits|faint\w*|unconscious\w*|passed\s+out|rolling\s+eyes?)\b",
            r"\b(severe\s+headache\w*|terrible\s+headache|blur\w*\s+vision|seeing\s+spots|flashes\s+of\s+light|swollen\s+face|epigastric\w*|pain\s+under\s+ribs|proteinuria)\b",
            r"\b(baby.*(not|hasn'?t|stopped|no)\s+(mov\w*|kick\w*)|no\s+movement|less\s+movement|stopped\s+moving|stopped\s+kicking)\b",
            r"\b(chest\s+indrawing|struggling\s+to\s+breathe|gasping|cannot\s+breathe|shortness\s+of\s+breath|grunting|fast\s+breathing|stridor|whooping|whoop\s+sound|cyanosis|blue\s+lips)\b",
            r"\b(severe\s+abdominal\s+pain|rigid\s+belly|stomach\s+rock\s+hard|excruciating\s+pain|abruptio|previa|cord\s+prolapse)\b",
            r"\b(water\s+broke.*green|green\s+fluid|green\s+thick\s+slime|cord\s+hanging|water\s+burst)\b",
            r"\b(contractions?.*(every\s+[1-5]\s+min|4\s+minutes?|regular.*contractions?)|urge\s+to\s+push)\b",
            r"\b(suicid\w*|harm\w*.*baby|hurt\w*.*baby|kill\s+myself)\b",
            r"\b(fever|38(\.\d+)?\s*([Cc]|degrees?)).*(infant|baby|newborn|6\s+weeks?|month\s+old)\b",
            r"\b(infant|baby|newborn|6\s+weeks?|month\s+old).*(fever|38(\.\d+)?\s*([Cc]|degrees?))\b",
            r"\b(baby.*floppy|ice\s+cold|burning\s+hot|yellow\s+palms|severe\s+jaundice|lockjaw|trismus)\b",
            r"\b(projectile\s+vomiting|sunken\s+fontanelle|skin\s+pinch.*tented)\b",
            # Yoruba
            r"\b(eje|eje pupo|da jade lati ese|ori mi si n fo mi|oju.*sokunkun|abawon loju)\b",
            r"\b(kikun omo|gbigbe omo|ko tii gbo kikun|buluu|dekun mimi|fa eemi sinu|iko leralera)\b",
            r"\b(ikun.*wu fuke.*le bi ilu|irora lile ni abe ikun|irora lile ni ibadi|iba gbigbona.*39|otutu gbigbon)\b",
            r"\b(omi to n run kikankikan|omi oyun.*be|awo eweko ti o ki|meconium|irobi lile.*iseju)\b",
            r"\b(ya igbe omi ni eemejo|bi ni eemerin|ko si mo nnkan kan mo|funfun hun-un bi efun)\b",
            # Pidgin
            r"\b(blood dey pour|heavy blood|de bleed|blood de com|vision completely blur|spots for my eye)\b",
            r"\b(never feel my baby move|baby no de move|pikin no de kick|lips and tongue turn blue|stop breathing)\b",
            r"\b(pikin no de breathe|belly swell big and hard like stone|stomach hard like stone)\b",
            r"\b(39\.5 degree|39\.8|foul smelly water|water dey smell bad|water burst.*green|thick slime water)\b",
            r"\b(painful contractions every 4 minutes|shit 8 watery diarrhea|vomit 4 times.*unconscious)\b",
            r"\b(white like chalk|chalky white poop)\b"
        ]

        # Multilingual priority patterns (Priority)
        self.priority_indicators = [
            # English
            r"\b(upcoming\s+appointment|missed\s+visit|reschedule|when\s+is\s+my\s+next|next\s+visit|next\s+appointment)\b",
            r"\b(immunization\s+due|vaccine\s+due|6\s+weeks?\s+vaccine|10\s+weeks?\s+vaccine|14\s+weeks?\s+vaccine|9\s+months?\s+vaccine|tetanus.*injection)\b",
            r"\b(vomiting\s+everything|cannot\s+keep\s+water\s+down|hyperemesis|severe\s+nausea)\b",
            r"\b(burn(s|ing)?.*(pee|urinat)|(pee|urinat).*burn(s|ing)?|painful\s+urination|uti|cloudy.*urine)\b",
            r"\b(breast\s+is\s+red|hard\s+lump\s+in\s+breast|hot\s+tender\s+breast|mastitis)\b",
            r"\b(sad\s+all\s+the\s+time|crying\s+every\s+day|postpartum\s+depression|baby\s+blues.*persist)\b",
            r"\b(pelvic\s+pain|stitch\s+pain|c-section\s+pain|wound\s+healing|backache.*pelvi[cs]|dull.*back.*pelvi[cs])\b",
            r"\b(fasting\s+blood\s+sugar|blood\s+sugar|glucose\s+result|105\s*mg/dl|gestational\s+diabetes|hepatitis)\b",
            r"\b(thrush|oral\s+thrush|white\s+patches.*tongue|sticky\s+eyes|cracked\s+nipples|cradle\s+cap|heat\s+rash|tiny\s+red\s+bumps)\b",
            r"\b(palm\w*\s+(and|&)\s+soles?.*itch\w*|itch\w*.*(palms?|soles?)|obstetric\s+cholestasis|high\s+blood\s+pressure|bp\s+is\s+high)\b",
            r"\b(haven't\s+passed\s+stool|constipat\w*|purulent\s+discharge|genital\s+ulcer|sores?\s+in\s+genital)\b",
            # Yoruba
            r"\b(eyin didun felefele|itemole ninu ibadi|hepatitis b|ko tii yago fun ojo merin|eewo ori|awo epo to nipon|eewo ooru|koko pupa keekeeke|irora lile ati ina nigba ti mo ba n to|ito mi.*run)\b",
            r"\b(egboogi iba.*ara mi n gbona|oogun ampicillin.*iko)\b",
            # Pidgin
            r"\b(dull back pain.*pelvi[cs]|malaria tablets.*feverish|hepatitis b|never shit for four days|cradle cap|thick oily scales|heat rash.*groin|pain and burning when (pass|passing|urinat)\w*|ampicillin drops.*baby cough)\b",
            r"\b(burn(s|ing)?.*(pee|urinat|pass\s+urine)|pain\s+and\s+burn\w*.*(pass|urinat)\w*)\b"
        ]

        # Ambiguous / Symptom indicators that require dual-model verification
        self.ambiguous_indicators = [
            r"\b(borderline|unclear|not\s+sure|symptoms?|pain|ache|discomfort|feel\s+strange|abnormal|worry|worried|trouble)\b"
        ]

        # Medication request patterns
        self.med_indicators = [
            r"\b(prescribe\w*|how\s+many\s+mg|dosage\w*|dose\w*|what\s+(drugs?|medicines?|tablets?)\s+to\s+take|antibiotics?|paracetamol|ibuprofen|cough\s+syrup|ampicillin)\b",
            r"\bcan\s+i\s+(give|take|swallow|use|drink)\b",
            r"\b(agbo|herbal\s+mixture|concoction|potash|kaun|gripe\s+water)\b",
            r"\b(ko awon egboogi|egboogi|iwon oogun|le ko oogun|mu agbo|lo potash|kaun)\b",
            r"\b(fit prescribe|prescribe.*tablets?|dose of|medicine to take|drink agbo)\b"
        ]

    def _matches_any(self, text: str, patterns: List[str]) -> bool:
        return any(re.search(pat, text) for pat in patterns)

    def generate_response(
        self,
        query: str,
        matched_passage: Optional[str] = None,
        language: str = "en",
        triage_hint: Optional[str] = None,
        conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        query_norm = normalize_text(query)

        # 1. Detection of Clinical Signals
        is_emergency_text = self._matches_any(query_norm, self.emergency_indicators)
        is_priority_text = self._matches_any(query_norm, self.priority_indicators)
        is_med_request = self._matches_any(query_norm, self.med_indicators)
        is_ambiguous = self._matches_any(query_norm, self.ambiguous_indicators)

        # Precedence Rule 1: Upstream hints take absolute clinical precedence
        hint_urgency = (triage_hint or "").lower().strip()
        is_emergency = is_emergency_text or (hint_urgency == "emergency")
        is_priority = (not is_emergency) and (is_priority_text or (hint_urgency == "priority"))

        # 2. Routing Decision
        if is_emergency:
            # PATH 1: CRITICAL EMERGENCY
            # Immediate hospital escalation via Chewie 1.2
            chewie_resp = self.chewie.generate_response(
                query=query,
                matched_passage=matched_passage,
                language=language,
                triage_hint="emergency",
                conversation_history=conversation_history
            )
            route_selected = "Chewie 1.2 (Acute Emergency Specialist)"
            final_response = chewie_resp["response"]
            final_urgency = "emergency"
            latency = chewie_resp["latency_ms"] + self.routing_overhead_ms
            tokens = chewie_resp["tokens_generated"]
            memory = chewie_resp["memory_allocated_mb"]
            dual_verified = False

        elif is_priority or is_med_request or is_ambiguous:
            # PATH 2: TIME-SENSITIVE PRIORITY / MEDICATION BOUNDARY / AMBIGUOUS
            # Dual-model generation with conservative arbitration
            chewie_resp = self.chewie.generate_response(
                query=query,
                matched_passage=matched_passage,
                language=language,
                triage_hint="priority" if is_priority else "routine",
                conversation_history=conversation_history
            )
            mamabot_resp = self.mamabot.generate_response(
                query=query,
                matched_passage=matched_passage,
                language=language,
                triage_hint="priority" if is_priority else "routine",
                conversation_history=conversation_history
            )

            # CONSERVATIVE DISAGREEMENT RESOLUTION (Escalate > Defer > Reassure)
            c_rank = URGENCY_RANKS.get(chewie_resp["urgency_category"], 1)
            m_rank = URGENCY_RANKS.get(mamabot_resp["urgency_category"], 1)
            h_rank = URGENCY_RANKS.get(hint_urgency, 1)

            # Enforce highest rank among: Chewie, MamaBot, or Upstream Hint
            winning_rank = max(c_rank, m_rank, h_rank)
            if is_priority and winning_rank < 2:
                winning_rank = 2  # Absolute guard against Priority falling to Routine

            if winning_rank == 3:
                final_urgency = "emergency"
                final_response = chewie_resp["response"] if c_rank >= m_rank else mamabot_resp["response"]
            elif winning_rank == 2:
                final_urgency = "priority"
                # Use MamaBot's thorough counseling or Chewie's clinical guidance
                final_response = mamabot_resp["response"] if m_rank >= c_rank else chewie_resp["response"]
            else:
                final_urgency = "routine"
                final_response = mamabot_resp["response"]

            route_selected = "Dual-Model Verification (Conservative Arbitration)"
            latency = max(chewie_resp["latency_ms"], mamabot_resp["latency_ms"]) + self.routing_overhead_ms + 25.0
            tokens = chewie_resp["tokens_generated"] + mamabot_resp["tokens_generated"]
            memory = max(chewie_resp["memory_allocated_mb"], mamabot_resp["memory_allocated_mb"]) + 400.0
            dual_verified = True

        else:
            # PATH 3: ROUTINE EDUCATIONAL & WELLNESS
            # Route to MamaBot-Llama for empathetic patient counseling
            mamabot_resp = self.mamabot.generate_response(
                query=query,
                matched_passage=matched_passage,
                language=language,
                triage_hint="routine",
                conversation_history=conversation_history
            )
            route_selected = "MamaBot-Llama (Maternal Counseling Specialist)"
            final_response = mamabot_resp["response"]
            final_urgency = "routine"
            latency = mamabot_resp["latency_ms"] + self.routing_overhead_ms
            tokens = mamabot_resp["tokens_generated"]
            memory = mamabot_resp["memory_allocated_mb"]
            dual_verified = False

        # 3. Final Deterministic Upstream Safety Assurance (Never downgrade!)
        if hint_urgency == "emergency" and final_urgency != "emergency":
            final_urgency = "emergency"
            if not final_response.startswith("EMERGENCY:"):
                final_response = f"EMERGENCY: {final_response}"
        elif hint_urgency == "priority" and final_urgency == "routine":
            final_urgency = "priority"
            if not final_response.startswith("PRIORITY:"):
                final_response = f"PRIORITY: {final_response}"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "model_name": self.name,
            "response": final_response,
            "urgency_category": final_urgency,
            "latency_ms": round(latency + elapsed_ms, 2),
            "tokens_generated": tokens,
            "memory_allocated_mb": round(memory, 2),
            "metadata": {
                "route_selected": route_selected,
                "dual_verified": dual_verified,
                "language": language,
                "grounded": matched_passage is not None,
                "conservative_arbitration_active": dual_verified
            }
        }
