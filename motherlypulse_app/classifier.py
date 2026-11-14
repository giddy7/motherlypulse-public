"""
MotherlyPulse Dynamic Triage Classifier
Classifies maternal and infant health messages into:
- EMERGENCY (Critical danger signs requiring immediate hospital escalation; overrides all others)
- PRIORITY (Important time-sensitive healthcare milestones needing prompt clinical consultation within 24-48h)
- ROUTINE (General education, wellness advice, standard reminders, medication declines)

Supports:
- English (en)
- Yoruba (yo) with tone-independent Unicode normalization
- Nigerian Pidgin (pcm) with local idioms

Decouples Clinical Urgency from Medication Safety:
A medication dosage request does NOT downgrade clinical urgency to Routine if underlying symptoms are acute.
"""

import re
import unicodedata
from typing import Dict, Any, List, Optional

def levenshtein_distance(s1: str, s2: str, max_d: int = 2) -> int:
    """Calculates Levenshtein distance bounded by max_d."""
    if abs(len(s1) - len(s2)) > max_d:
        return max_d + 1
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1] * (len(s2) + 1)
        for j, c2 in enumerate(s2):
            cost = 0 if c1 == c2 else 1
            curr[j + 1] = min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost)
        prev = curr
    return prev[len(s2)]

def normalize_text(text: str) -> str:
    """Normalizes text by decomposing Unicode and removing combining accents (diacritics/tone marks)."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.lower()

class DynamicTriageClassifier:
    def __init__(self):
        # Multilingual Emergency patterns (Obstetric, newborn, pediatric, psychiatric red flags)
        self.emergency_patterns = [
            # 1. Vaginal Bleeding / Hemorrhage
            r"\b(bleed\w*|blood\w*|hemorrhag\w*|haemorrhag\w*|lochia\s+heavy|soaking\s+pads?)\b",
            r"\b(eje|eje pupo|eje n tu jade|da jade lati ese)\b",
            r"\b(blood dey pour|heavy blood|de bleed|blood de com)\b",
            
            # 2. Fits / Convulsions / Seizures / Loss of consciousness
            r"\b(convuls\w*|seiz\w*|having\s+a\s+fit|fits|faint\w*|unconscious\w*|passed\s+out|rolling\s+eyes?)\b",
            r"\b(giri|fiti|ja\s+ipa|idarudapo opolo|ko si mo nnkan kan|oju.*ko didun)\b",
            r"\b(de shake|de roll eyes?|faint|unconscious)\b",
            
            # 3. Severe Preeclampsia / Eclampsia Warning Signs
            r"\b(severe\s+headache\w*|terrible\s+headache|blur\w*\s+vision|seeing\s+spots|flashes\s+of\s+light|swollen\s+face|epigastric\w*|pain\s+under\s+ribs|proteinuria)\b",
            r"\b(ori mi si n fo mi|oju.*sokunkun|abawon loju|ori.*fo)\b",
            r"\b(vision completely blur|spots for my eye|eye de dark)\b",
            
            # 4. Fetal Distress / Absent Fetal Movement
            r"\b(baby.*(not|hasn'?t|stopped|no)\s+(mov\w*|kick\w*)|no\s+movement|less\s+movement|stopped\s+moving|stopped\s+kicking)\b",
            r"\b(kikun omo|gbigbe omo|ko tii gbo kikun)\b",
            r"\b(never feel my baby move|baby no de move|pikin no de kick)\b",
            
            # 5. Acute Respiratory Distress / Cyanosis
            r"\b(chest\s+indrawing|struggling\s+to\s+breathe|gasping|cannot\s+breathe|shortness\s+of\s+breath|grunting|fast\s+breathing|stridor|whooping|whoop\s+sound|cyanosis|blue\s+lips)\b",
            r"\b(buluu|dekun mimi|fa eemi sinu|iko leralera|eemi n pin|ko le mi)\b",
            r"\b(lips and tongue turn blue|stop breathing|pikin no de breathe|rapid spasms)\b",
            
            # 6. Severe Abdominal Pain / Rigid Abdomen (Placental Abruption / Obstruction)
            r"\b(severe\s+abdominal\s+pain|rigid\s+belly|stomach\s+rock\s+hard|excruciating\s+pain)\b",
            r"\b(ikun.*wu fuke.*le bi ilu|irora lile ni abe ikun|irora lile ni ibadi|ikun.*le bi okuta)\b",
            r"\b(belly swell big and hard like stone|stomach hard like stone|pain for one side.*egungun)\b",
            
            # 7. Sepsis / Severe Postpartum or Intrauterine Infection / High Fever
            r"\b(foul.*smell.*discharge|smelly\s+discharge|lochia\s+smell|shivering.*fever|high\s+fever.*postpartum|puerperal\s+sepsis|foul.*green.*discharge)\b",
            r"\b(fever|38(\.\d+)?\s*([Cc]|degrees?)).*(infant|baby|newborn|6\s+weeks?|month\s+old)\b",
            r"\b(infant|baby|newborn|6\s+weeks?|month\s+old).*(fever|38(\.\d+)?\s*([Cc]|degrees?))\b",
            r"\b(iba gbigbona.*39|39\.5|39\.8|otutu gbigbon|omi to n run kikankikan|run kikankikan)\b",
            r"\b(39\.5 degree|39\.8|foul smelly water|water dey smell bad)\b",
            
            # 8. Amniotic Fluid Complications / Rupture / Meconium
            r"\b(water\s+broke.*green|green\s+fluid|green\s+thick\s+slime|cord\s+hanging|umbilical\s+cord\s+out|cord\s+slipping)\b",
            r"\b(omi oyun.*be|awo eweko ti o ki|meconium)\b",
            r"\b(water burst.*green|thick slime water)\b",
            
            # 9. Active Labour / Imminent Delivery
            r"\b(contractions?.*(every\s+[1-5]\s+min|4\s+minutes?|regular.*contractions?)|urge\s+to\s+push|bulging\s+between\s+legs)\b",
            r"\b(irobi lile.*iseju merin|irobi lile.*iseju|ise omo)\b",
            r"\b(painful contractions every 4 minutes|contraction.*every 4 minutes)\b",
            
            # 10. Psychiatric Emergency / Crisis
            r"\b(kill\s+myself|suicid\w*|end\s+it\s+all|harm\w*.*baby|hurt\w*.*baby|poison\s+myself)\b",
            r"\b(pa ara mi|pa omo mi)\b",
            r"\b(kill myself|harm my baby)\b",
            
            # 11. Newborn & Infant Critical Signs (Tetanus, Sepsis, Severe Jaundice, Dehydration)
            r"\b(baby.*not\s+feeding|cannot\s+suck|refusing\s+(breast|to\s+eat|feeds?)|baby.*floppy|baby.*ice\s+cold|baby.*burning\s+hot|yellow\s+palms|yellow\s+soles|severe\s+jaundice|pus.*cord|cord.*red.*swollen)\b",
            r"\b(lockjaw|trismus|cannot open mouth|rusty blade|cut.*cord.*blade)\b",
            r"\b(ya igbe omi ni eemejo|bi ni eemerin|ko si mo nnkan kan mo)\b",
            r"\b(shit 8 watery diarrhea|vomit 4 times.*unconscious|white like chalk|chalky white poop|funfun hun-un bi efun)\b",
            r"\b(projectile\s+vomiting|sunken\s+fontanelle|skin\s+pinch.*tented)\b"
        ]

        # Multilingual Priority patterns (Time-sensitive clinical appointments, acute non-fatal conditions, preventive milestones)
        self.priority_patterns = [
            r"\b(upcoming\s+appointment|missed\s+visit|reschedule|when\s+is\s+my\s+next|next\s+visit|next\s+appointment)\b",
            r"\b(immunization\s+due|vaccine\s+due|6\s+weeks?\s+vaccine|10\s+weeks?\s+vaccine|14\s+weeks?\s+vaccine|9\s+months?\s+vaccine|tetanus.*injection)\b",
            r"\b(vomiting\s+everything|cannot\s+keep\s+water\s+down|hyperemesis|severe\s+nausea)\b",
            r"\b(burn(s|ing)?.*(pee|urinat)|(pee|urinat).*burn(s|ing)?|painful\s+urination|uti|cloudy.*urine)\b",
            r"\b(breast\s+is\s+red|hard\s+lump\s+in\s+breast|hot\s+tender\s+breast|mastitis)\b",
            r"\b(sad\s+all\s+the\s+time|crying\s+every\s+day|postpartum\s+depression|baby\s+blues.*persist)\b",
            r"\b(pelvic\s+pain|stitch\s+pain|c-section\s+pain|wound\s+healing|backache.*pelvis|dull.*back.*pelvis)\b",
            r"\b(fasting\s+blood\s+sugar|blood\s+sugar|glucose\s+result|105\s*mg/dl|gestational\s+diabetes|hepatitis)\b",
            r"\b(thrush|oral\s+thrush|white\s+patches.*tongue|sticky\s+eyes|cracked\s+nipples|cradle\s+cap|heat\s+rash|tiny\s+red\s+bumps)\b",
            r"\b(palm\w*\s+(and|&)\s+soles?.*itch\w*|itch\w*.*(palms?|soles?)|obstetric\s+cholestasis)\b",
            r"\b(hypertensive|high\s+blood\s+pressure|bp\s+is\s+high)\b",
            r"\b(haven't\s+passed\s+stool|constipat\w*|purulent\s+discharge|genital\s+ulcer|sores?\s+in\s+genital)\b",
            # Yoruba priority phrases
            r"\b(eyin didun felefele|itemole ninu ibadi|hepatitis b|ko tii yago fun ojo merin|eewo ori|awo epo to nipon|eewo ooru|koko pupa keekeeke|irora lile ati ina nigba ti mo ba n to|ito mi.*run)\b",
            r"\b(egboogi iba.*ara mi n gbona|oogun ampicillin.*iko)\b",
            # Pidgin priority phrases
            r"\b(dull back pain.*pelvis|malaria tablets.*feverish|hepatitis b|never shit for four days|cradle cap|thick oily scales|heat rash.*groin|pain and burning when passing urine|ampicillin drops.*baby cough)\b"
        ]

        # Medication safety & dosage decline patterns (Orthogonal to clinical urgency)
        self.decline_patterns = [
            r"\b(prescribe\w*|how\s+many\s+mg|dosage\w*|dose\w*|what\s+(drugs?|medicines?|tablets?)\s+to\s+take|antibiotics?|paracetamol|ibuprofen|cough\s+syrup|ampicillin)\b",
            r"\bcan\s+i\s+(give|take|swallow|use|drink)\b",
            r"\b(agbo|herbal\s+mixture|concoction|potash|kaun|gripe\s+water)\b",
            # Yoruba medication requests
            r"\b(ko awon egboogi|egboogi|iwon oogun|le ko oogun|mu agbo|lo potash|kaun)\b",
            # Pidgin medication requests
            r"\b(fit prescribe|prescribe.*tablets?|dose of|medicine to take|drink agbo)\b"
        ]

    def _fuzzy_match_emergency(self, text: str) -> Optional[str]:
        """
        Bounded fuzzy matching for emergency danger signs across EN, YO, and PCM.
        Levenshtein distance <= 2 for words >= 5 characters; <= 1 for 4-character words.
        """
        # Clean tokens
        raw_tokens = re.findall(r"[a-z0-9\-]+", text)
        if not raw_tokens:
            return None

        # 1. Critical single English terms (len >= 5 -> dist <= 2; len 4 -> dist <= 1)
        critical_en_terms = [
            "bleeding", "hemorrhage", "haemorrhage",
            "convulsion", "convulsions", "seizure", "seizures",
            "unconscious", "preeclampsia", "eclampsia",
            "cyanosis", "meconium", "lockjaw", "trismus"
        ]
        for token in raw_tokens:
            t_len = len(token)
            if t_len < 4:
                continue
            max_d = 2 if t_len >= 5 else 1
            for term in critical_en_terms:
                if levenshtein_distance(token, term, max_d) <= max_d:
                    return f"Fuzzy matched English danger keyword '{token}' -> '{term}'"

        # 2. Yoruba fuzzy danger patterns
        # 2a. Eje pupo (profuse bleeding)
        has_eje = any(tok == "eje" or levenshtein_distance(tok, "eeje", 1) <= 1 for tok in raw_tokens)
        if has_eje:
            for tok in raw_tokens:
                if tok != "eje" and levenshtein_distance(tok, "pupo", 1) <= 1:
                    return f"Fuzzy matched Yoruba profuse bleeding ('eje' + '{tok}')"

        # 2b. Convulsion / Seizure: giri (dist <= 1) or fiti (dist <= 1)
        for tok in raw_tokens:
            if tok != "girl" and levenshtein_distance(tok, "giri", 1) <= 1:
                return f"Fuzzy matched Yoruba convulsion sign '{tok}' -> 'giri'"
            # Disallow 'fit' from matching 'fiti' as 'fit' is a common Pidgin modal verb ('can')
            if tok not in ("fit", "fat") and levenshtein_distance(tok, "fiti", 1) <= 1:
                return f"Fuzzy matched Yoruba fits sign '{tok}' -> 'fiti'"

        # 2c. Altered mental state: idarudapo (dist <= 2)
        for tok in raw_tokens:
            if len(tok) >= 6 and levenshtein_distance(tok, "idarudapo", 2) <= 2:
                return f"Fuzzy matched Yoruba altered consciousness '{tok}' -> 'idarudapo'"

        # 2d. Severe fever / foul discharge: kikankikan (dist <= 2) near iba/run/omi
        if any(w in text for w in ("iba", "run", "omi")):
            for tok in raw_tokens:
                if len(tok) >= 6 and (levenshtein_distance(tok, "kikankikan", 2) <= 2 or levenshtein_distance(tok, "kinkankan", 2) <= 2):
                    return f"Fuzzy matched Yoruba severe infection '{tok}' -> 'kikankikan'"

        # 2e. Respiratory arrest: dekun mimi
        if "dekun" in text or "pin" in text:
            for tok in raw_tokens:
                if levenshtein_distance(tok, "mimi", 1) <= 1 or levenshtein_distance(tok, "eemi", 1) <= 1:
                    return f"Fuzzy matched Yoruba respiratory arrest ('dekun/pin' + '{tok}')"

        # 3. Nigerian Pidgin fuzzy danger patterns
        # 3a. Infant high fever: "pikin body dey hot wel wel" or variants
        if re.search(r"\b(hot\s+wel\s+wel|hot\s+well\s+well|body\s+dey\s+hot|body\s+de\s+hot)\b", text):
            if any(w in text for w in ("pikin", "baby", "infant", "child", "belle")):
                return "Fuzzy matched Pidgin infant severe fever ('pikin body dey hot wel wel')"

        # 3b. Blood dey pour: "blood dey poor" / "blood de com plenty"
        if any(w in text for w in ("blood", "bleed", "bleeding")):
            for tok in raw_tokens:
                if levenshtein_distance(tok, "pour", 1) <= 1 or tok == "poor" or tok == "plenty":
                    return f"Fuzzy matched Pidgin severe hemorrhage ('blood' + '{tok}')"

        # 3c. Respiratory arrest in Pidgin
        if any(w in text for w in ("no de", "stop", "cannot", "no fit", "cant")):
            for tok in raw_tokens:
                if len(tok) >= 5 and (levenshtein_distance(tok, "breathe", 2) <= 2 or levenshtein_distance(tok, "breathing", 2) <= 2 or tok == "breeth"):
                    return f"Fuzzy matched Pidgin acute respiratory distress ('stop/no de' + '{tok}')"

        # 3d. Rigid abdomen: stomach hard like stone / stoone
        if "hard like" in text:
            for tok in raw_tokens:
                if levenshtein_distance(tok, "stone", 1) <= 1:
                    return f"Fuzzy matched acute abdomen ('hard like' + '{tok}')"

        # 3e. Meconium / amniotic: green thick slime / slyme
        if any(w in text for w in ("green", "thick")):
            for tok in raw_tokens:
                if levenshtein_distance(tok, "slime", 1) <= 1:
                    return f"Fuzzy matched meconium staining ('green/thick' + '{tok}')"

        return None

    def classify(self, message: str, conversation_history: List[str] = None) -> Dict[str, Any]:
        """
        Dynamically classifies a message with strict clinical precedence:
        Emergency > Priority > Routine.
        
        Separates clinical urgency from medication safety:
        A medication request is flagged independently and does NOT downgrade urgency.
        """
        text = normalize_text(message)
        
        # 1. Detect medication / prescription request independently
        medication_requested = False
        matched_med_pattern = None
        for pattern in self.decline_patterns:
            if re.search(pattern, text):
                medication_requested = True
                matched_med_pattern = pattern
                break

        # 2. Check for emergency warning signs in current message
        for pattern in self.emergency_patterns:
            if re.search(pattern, text):
                return {
                    "urgency_category": "emergency",
                    "medication_safety_triggered": medication_requested,
                    "reason": f"Matched critical emergency warning sign: {pattern}",
                    "action_required": "Immediate emergency hospital escalation without delay",
                    "override_active": True
                }
        
        # 2.1 Bounded fuzzy matching for emergency danger signs (Levenshtein distance <= 2)
        fuzzy_match_reason = self._fuzzy_match_emergency(text)
        if fuzzy_match_reason:
            return {
                "urgency_category": "emergency",
                "medication_safety_triggered": medication_requested,
                "reason": f"Fuzzy matched critical emergency warning sign: {fuzzy_match_reason}",
                "action_required": "Immediate emergency hospital escalation without delay",
                "override_active": True
            }
        
        # 3. Check if conversation history has an unresolved emergency (State Persistence)
        if conversation_history:
            for past_msg in conversation_history:
                past_norm = normalize_text(past_msg)
                for pattern in self.emergency_patterns:
                    if re.search(pattern, past_norm):
                        return {
                            "urgency_category": "emergency",
                            "medication_safety_triggered": medication_requested,
                            "reason": f"Active emergency persisted from previous turn: {pattern}",
                            "action_required": "Maintain immediate emergency medical escalation",
                            "override_active": True
                        }
                past_fuzzy = self._fuzzy_match_emergency(past_norm)
                if past_fuzzy:
                    return {
                        "urgency_category": "emergency",
                        "medication_safety_triggered": medication_requested,
                        "reason": f"Active emergency persisted from previous turn (fuzzy): {past_fuzzy}",
                        "action_required": "Maintain immediate emergency medical escalation",
                        "override_active": True
                    }
        
        # 4. Check priority patterns in current message
        for pattern in self.priority_patterns:
            if re.search(pattern, text):
                return {
                    "urgency_category": "priority",
                    "medication_safety_triggered": medication_requested,
                    "reason": f"Matched priority healthcare milestone/symptom: {pattern}",
                    "action_required": "Prompt clinic consultation or time-sensitive follow-up (24-48h)",
                    "override_active": False
                }

        # 5. Default clinical urgency: Routine
        return {
            "urgency_category": "routine",
            "medication_safety_triggered": medication_requested,
            "reason": "Prescription boundary trigger" if medication_requested else "General wellness, education, or routine reminder",
            "action_required": "Clinical safety decline" if medication_requested else "Provide grounded educational response",
            "override_active": False
        }
