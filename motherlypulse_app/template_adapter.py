"""
MotherlyPulse Phase 1 Remediation: Deterministic Template-Based Conversational Response Adaptation Engine

Core Architecture:
Four-Slot Conversational Assembly:
  [Slot 1: Empathy Opening - Language & Domain Aware]
  [Slot 2: Symptom Mirroring - Negation-Aware & Language-Scoped]
  [Slot 3: Clinical Core (Authoritative Medically Approved Text)]
  [Slot 4: Action / Referral Directive - Deduplicated & Timeframe Preserved]

Guarantees & Clinical Invariants:
1. The medically approved reference response remains the immutable source of truth.
2. The AI/engine NEVER generates independent medical diagnoses, drugs, or dosages.
3. Language-scoped symptom lexicons (English, Yoruba, Nigerian Pidgin) prevent cross-language overwrites.
4. Negation-aware symptom extraction: Denied symptoms ('no fever', 'not vomiting') are NEVER mirrored affirmatively.
5. Multi-sentence clinical core invariance: Inspects ALL reference sentences and enforces mandatory clinical warnings.
6. Medication polarity verification: Inversion of medication prohibition into permission is strictly detected and rejected.
7. Word-boundary anchored referral validation: Rejects false matches like 'clinical evaluation' without physical facility referral.
8. Domain-aware empathy selection: Differentiates pregnancy from infant-care to eliminate contextual greeting mismatches.
9. Emergency responses strictly bypass conversational adaptation with zero delay and zero conversational questions.
10. Invariant validation failure falls back silently and deterministically to the original approved reference response.
"""

import re
import time
import unicodedata
from typing import Dict, Any, List, Optional, Tuple

def normalize_text(text: str) -> str:
    """Normalizes text by decomposing Unicode and removing combining accents."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.lower()

# Pre-approved phrase banks for English, Yoruba, and Nigerian Pidgin
PHRASE_BANKS = {
    "English": {
        "empathy_routine_pregnancy": [
            "I understand your question, and I am glad you are checking on your health.",
            "Thank you for reaching out about this. Taking proactive care of yourself and your baby is wonderful.",
            "That is a very common question during pregnancy and early motherhood."
        ],
        "empathy_routine_infant": [
            "I understand your question, and I am glad you are checking on your baby's care.",
            "Thank you for reaching out. Taking proactive care of your baby is wonderful.",
            "That is a very common question in caring for your baby."
        ],
        "empathy_priority": [
            "I hear your concern, and it is very important that we address how you are feeling.",
            "I understand this symptom can be uncomfortable, and attending to it promptly protects both you and your baby.",
            "Thank you for sharing this with me. It is important to pay close attention to how your body is responding."
        ],
        "mirror_prefix": "Regarding what you shared about {symptom}: ",
        "mirror_prefix_general": "Regarding the question you shared: ",
        "action_priority_reminder": "Please consult your healthcare provider or visit your primary health centre within 24 to 48 hours for proper clinical assessment.",
        "action_priority_reinforcement": "Please make sure you follow through with this clinical visit promptly to protect your health.",
        "action_routine_closing": "Feel free to check in if you have more questions about your daily routine."
    },
    "Yoruba": {
        "empathy_routine_pregnancy": [
            "Ẹ pẹlẹ mà, ibeere pataki lẹ bi yii, o si dara bi ẹ ṣe n tọju ara yin pẹlu ọmọ yin.",
            "Ẹ ku oju lona ọmọ mà. O dara pupọ bi ẹ ṣe n tọpinpin ilera yin lẹsẹkẹsẹ.",
            "Ẹ pẹlẹ mà, ọrọ to wọpọ ninu oyun ati itọju ọmọ lẹhin ibimọ ni eyi."
        ],
        "empathy_routine_infant": [
            "Ẹ pẹlẹ mà, ibeere pataki lẹ bi yii, o si dara bi ẹ ṣe n tọju ara yin pẹlu ọmọ yin.",
            "Ẹ pẹlẹ mà, ẹ ku itọju ọmọ. O dara pupọ bi ẹ ṣe n tọpinpin ilera ọmọ yin lẹsẹkẹsẹ.",
            "Ẹ pẹlẹ mà, ọrọ to wọpọ ninu itọju ọmọ lẹhin ibimọ ni eyi."
        ],
        "empathy_priority": [
            "Ẹ pẹlẹ mà, mo gbọ bi ara ṣe n ṣe yin, o si ṣe pataki pupọ lati tete wa iranlọwọ.",
            "Ẹ pẹlẹ mà, aibalẹ ọkan ti nkan yi n fa ko rọrun, ṣugbọn a gbọdọ ṣe abojuto rẹ lẹsẹkẹsẹ lati daabo bo ẹyin ati ọmọ yin.",
            "Ẹ pẹlẹ mà, gbigbọ nipa bi ara ṣe n ṣe yin jẹ ki a mọ pe o yẹ ki oṣiṣẹ ilera yẹ yin wo laipẹ."
        ],
        "mirror_prefix": "Nipa {symptom} ti ẹ sọ nipa rẹ: ",
        "mirror_prefix_general": "Nipa ibeere ti ẹ beere: ",
        "action_priority_reminder": "Ẹ jọwọ, ẹ lọ si ile-iwosan alakọbẹrẹ tabi kan si oṣiṣẹ ilera yin laarin wakati merinlelogun si mejidinlaaadota fun ayẹwo to peye.",
        "action_priority_reinforcement": "Ẹ jọwọ ẹ ri daju pe ẹ lọ si ile-iwosan gẹgẹ bi a ṣe sọ fun aabo ilera yin ati ọmọ yin.",
        "action_routine_closing": "Ẹ le beere ibeere siwaju sii ti ẹ ba nilo alaye lori itọju ojoojumọ yin."
    },
    "Nigerian Pidgin": {
        "empathy_routine_pregnancy": [
            "I hear you well-well, and e good say you de ask this important question about your health.",
            "Well done as you de take care of yourself and your pikin body.",
            "No worry, this question na wetin many pregnant women and new mothers de ask."
        ],
        "empathy_routine_infant": [
            "I hear you well-well, and e good say you de ask this important question about your pikin.",
            "Well done as you de take care of your pikin body.",
            "No worry, this question na wetin many new mothers de ask."
        ],
        "empathy_priority": [
            "Sorry about how you dey feel, and e good say you talk am make we fit help you sharp-sharp.",
            "I understand say this thing de worry you, and we must check am well so that you and your pikin go dey safe.",
            "Pele my sister. This symptom wey you mention need make beta health worker check you quickly."
        ],
        "mirror_prefix": "Concerning the {symptom} wey you talk about: ",
        "mirror_prefix_general": "Concerning wetin you ask so: ",
        "action_priority_reminder": "Abeg make you visit your primary health centre or see your nurse within 24 to 48 hours make dem examine you well.",
        "action_priority_reinforcement": "Abeg make you sure say you follow this advice carry body go clinic sharp-sharp.",
        "action_routine_closing": "Make you feel free to ask more questions anytime you need guidance."
    }
}

# Compatibility aliases for legacy lookups
for lang in PHRASE_BANKS:
    PHRASE_BANKS[lang]["empathy_routine"] = PHRASE_BANKS[lang]["empathy_routine_pregnancy"]

# Language-specific symptom lexicons for safe, non-hallucinatory lexical mirroring
LANGUAGE_SCOPED_SYMPTOM_LEXICONS = {
    "English": {
        "vomiting": "vomiting",
        "throw up": "vomiting",
        "nausea": "nausea",
        "hard stool": "hard stools",
        "constipat": "constipation",
        "swollen feet": "swelling in your feet",
        "swollen leg": "swelling in your legs",
        "swelling": "swelling",
        "headache": "headache",
        "fever": "fever",
        "hot body": "feeling feverish",
        "back pain": "back pain",
        "backache": "back pain",
        "breast pain": "breast pain",
        "cracked nipple": "cracked nipples",
        "sadness": "feeling sad",
        "crying": "crying spells",
        "tired": "feeling tired",
        "fatigue": "fatigue",
        "weakness": "weakness",
        "pain when peeing": "pain during urination",
        "burn when peeing": "burning during urination",
        "foul discharge": "vaginal discharge",
        "diarrhea": "diarrhea",
        "cough": "cough",
        "heat rash": "heat rash"
    },
    "Yoruba": {
        "ebi": "ebi ti ẹ n bi",
        "gbígbóná": "ara ti o n gbona",
        "gbigbona": "ara ti o n gbona",
        "igbẹ gbuuru": "igbẹ gbuuru",
        "igbe gbuuru": "igbẹ gbuuru",
        "orí fífó": "ori fifo",
        "ori fifo": "ori fifo",
        "ẹsẹ wiwu": "ẹsẹ ti o n wú",
        "ese wiwu": "ẹsẹ ti o n wú",
        "omú dídùn": "ọmu ti o n dun yin",
        "omu didun": "ọmu ti o n dun yin",
        "aibalẹ ọkan": "aibalẹ ọkan",
        "aibale okan": "aibalẹ ọkan",
        "aare": "aare ti o n da yin",
        "àárẹ̀": "aare ti o n da yin",
        "otutu": "otutu"
    },
    "Nigerian Pidgin": {
        "de vomit": "vomiting wey you talk",
        "vomit": "vomiting wey you talk",
        "body hot": "hot body wey you get",
        "fever": "fever wey you mention",
        "belly pain": "belly pain",
        "shit watery": "watery stool",
        "head de pain": "headache",
        "headache": "headache",
        "leg swell": "leg wey swell",
        "swollen leg": "leg wey swell",
        "breast pain": "breast pain",
        "sad": "how you de feel sad",
        "tired": "how your body de weak",
        "weak": "weak body"
    }
}

# Backward-compatibility alias
SYMPTOM_LEXICON = LANGUAGE_SCOPED_SYMPTOM_LEXICONS["English"]

# Forbidden negative tokens: Prescriptions, dosages, units, dangerous obstetric drugs, and herbal mixtures (agbo)
FORBIDDEN_MEDICATION_TOKENS = [
    # Common Pharmaceuticals & antimicrobials
    r"\bparacetamol\b", r"\bibuprofen\b", r"\baspirin\b", r"\bamoxicillin\b",
    r"\bciprofloxacin\b", r"\bartemether\b", r"\blumefantrine\b", r"\bflagyl\b",
    r"\bmetronidazole\b", r"\bdiclofenac\b", r"\bampicillin\b", r"\bchlorpheniramine\b",
    r"\bantibiotic[s]?\b", r"\bpainkiller[s]?\b", r"\bsedative[s]?\b",
    r"\bcefuroxime\b", r"\bceftriaxone\b", r"\berythromycin\b", r"\bazithromycin\b",
    r"\bcotrimoxazole\b", r"\bseptrin\b", r"\bgentamicin\b", r"\bdoxycycline\b",
    r"\btetracycline\b", r"\bchloroquine\b", r"\binjection[s]?\b",
    # Obstetric, cardiovascular, teratogenic & controlled analgesics
    r"\bmisoprostol\b", r"\boxytocin\b", r"\bcytotec\b", r"\btramadol\b",
    r"\bcodeine\b", r"\bmorphine\b", r"\bpentazocine\b", r"\bwarfarin\b",
    r"\bheparin\b", r"\bmethyldopa\b", r"\blabetalol\b", r"\bnifedipine\b",
    r"\bhydralazine\b", r"\bmagnesium\s+sulfate\b", r"\bmagnesium\s+sulphate\b",
    r"\bindomethacin\b",
    # Antimalarials
    r"\bartesunate\b", r"\bquinine\b", r"\bfansidar\b", r"\bsulfadoxine\b",
    r"\bpyrimethamine\b",
    # Supplements & micronutrients
    r"\biron\b", r"\bfolic\s+acid\b", r"\bfolate\b", r"\bcalcium\b",
    r"\bmultivitamin[s]?\b", r"\bvitamin\s+a\b", r"\bvitamin\s+c\b", r"\bzinc\b",
    # Specific units and dosage patterns
    r"\b\d+(?:\.\d+)?\s*mg\b", r"\b\d+(?:\.\d+)?\s*ml\b", r"\b\d+(?:\.\d+)?\s*mcg\b",
    r"\b\d+(?:\.\d+)?\s*g\b", r"\b\d+(?:\.\d+)?\s*iu\b",
    r"\b\d+\s*tablet[s]?\b", r"\b\d+\s*capsule[s]?\b",
    r"\b\d+\s*teaspoon[s]?\b", r"\b\d+\s*tablespoon[s]?\b", r"\b\d+\s*drops?\b",
    r"\bmg/kg\b",
    # Traditional & unverified mixtures
    r"\bagbo\b", r"\bherbal\s+mixture\b", r"\bconcoction\b", r"\bnative\s+medicine\b"
]

# Clinical prohibition markers
PROHIBITION_PATTERNS = [
    r"\bdo\s+not\b", r"\bdon'?t\b", r"\bavoid\b", r"\bnever\b",
    r"\bcannot\b", r"\bcan'?t\b", r"\bprohibit\w*\b", r"\bnot\s+safe\b",
    r"\bharm\w*\b", r"\bdanger\w*\b", r"\bstop\b", r"\bno\s+fit\b",
    r"\bmake\s+you\s+no\b", r"\bẹ\s+ma\s+ṣe\b", r"\be\s+ma\s+se\b",
    r"\bko\s+le\b", r"\bko\s+gbọdọ\b", r"\bko\s+gbodo\b"
]

# Clinical permission markers
PERMISSION_PATTERNS = [
    r"\byou\s+can\s+(safely\s+)?(take|use|drink|swallow|administer)\b",
    r"\bsafe\s+to\s+(take|use|drink|administer)\b",
    r"\bfit\s+take\b", r"\bfit\s+drink\b",
    r"\bẹ\s+le\s+lo\b", r"\be\s+le\s+lo\b",
    r"\bpermitted\b", r"\ballowed\b", r"\brecommended\b",
    r"\btake\s+your\s+(prescribed\s+)?(supplement|vitamin|iron|folic|calcium)\b",
    r"\bcontinue\s+(taking\s+)?(your\s+)?(iron|folic|calcium|vitamins?|supplements?)\b"
]

# Physical healthcare facility & provider patterns (Anchored with word boundaries)
REFERRAL_PATTERNS = [
    r"\bclinic\b", r"\bhealth\s+centre\b", r"\bhealth\s+center\b",
    r"\bhospital\b", r"\bdoctor\b", r"\bmidwife\b", r"\bnurse\b",
    r"\b(antenatal\s+care\s+|healthcare\s+|care\s+)?provider\b", r"\bprimary\s+health\b",
    # Yoruba
    r"\bile-?iwosan\b", r"\boṣiṣẹ\s+ilera\b", r"\bosise\s+ilera\b",
    r"\bagbẹbi\b", r"\bagbebi\b", r"\bdokita\b",
    # Nigerian Pidgin
    r"\bhealth\s+worker\b", r"\bprimary\s+health\s+centre\b"
]

# Mandatory clinical warning condition markers
CRITICAL_CLINICAL_MARKERS = [
    r"\bpreeclampsia\b", r"\beclampsia\b", r"\bdehydration\b",
    r"\bconvuls\w*\b", r"\bseiz\w*\b", r"\bhemorrhag\w*\b",
    r"\bhaemorrhag\w*\b", r"\bgestational\s+diabetes\b",
    r"\bpremature\s+labour\b", r"\bpremature\s+labor\b",
    r"\bkidney\w*\b", r"\bectopic\b", r"\bsepsis\b",
    r"\binfection\b", r"\bmastitis\b"
]

# Mandatory clinical imperatives (Short sentences & critical actions)
MANDATORY_IMPERATIVE_PATTERNS = [
    (r"\bdo\s+not\s+wait\b", "do not wait"),
    (r"\bgo\s+to\s+(the\s+)?(clinic|hospital|health\s+centre|health\s+center|doctor)\b", "go to clinic/hospital"),
    (r"\bseek\s+(immediate|prompt|emergency)?\s*(medical\s+)?(help|care|attention)\b", "seek medical help/care"),
    (r"\bdo\s+not\s+(take|use|drink|ingest|administer)\b", "do not take/use medication"),
    (r"\bcall\s+(emergency|112|hospital|health\s+centre)\b", "call emergency/contacts"),
    (r"\breturn\s+if\s+(symptoms?\s+)?worsen\b", "return if symptoms worsen"),
    (r"\battend\s+(your\s+)?(scheduled\s+)?(clinic\s+visit|health\s+centre)\b", "attend clinic visit"),
    (r"\bconsult\s+(your\s+)?(doctor|midwife|health\s+worker|healthcare\s+provider)\b", "consult health provider"),
    (r"\be\s+lo\s+si\b", "e lo si"),
    (r"\be\s+ma\s+se\b", "e ma se"),
    (r"\bko\s+gbodo\b", "ko gbodo"),
    (r"\bgo\s+hospital\b", "go hospital"),
    (r"\bmake\s+you\s+no\b", "make you no")
]


# Unit and written number normalizations for unambiguous equivalence
WORD_TO_NUMBER = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
    "twenty-four": "24", "twenty four": "24",
    "thirty": "30", "forty": "40", "forty-eight": "48", "forty eight": "48",
    "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80", "ninety": "90",
    "one hundred": "100", "two hundred": "200", "two hundred and fifty": "250",
    "five hundred": "500", "one thousand": "1000"
}

UNIT_NORMALIZATIONS = [
    (r"\b(millilitres?|milliliters?)\b", "ml"),
    (r"\b(milligrams?)\b", "mg"),
    (r"\b(micrograms?)\b", "mcg"),
    (r"\b(grams?)\b", "g"),
    (r"\b(tablespoons?|tbsp)\b", "tablespoon"),
    (r"\b(teaspoons?|tsp)\b", "teaspoon"),
    (r"\b(tablets?|capsules?|pills?|tabs?|caps?)\b", "tablet"),
    (r"\b(doses?)\b", "dose"),
    (r"\b(drops?)\b", "drop")
]

MEDICATION_AND_SUPPLEMENT_TOKENS = [
    "paracetamol", "ibuprofen", "aspirin", "amoxicillin", "ciprofloxacin",
    "artemether", "lumefantrine", "flagyl", "metronidazole", "diclofenac",
    "ampicillin", "chlorpheniramine", "cefuroxime", "ceftriaxone",
    "erythromycin", "azithromycin", "cotrimoxazole", "septrin", "gentamicin",
    "doxycycline", "tetracycline", "chloroquine", "misoprostol", "oxytocin",
    "cytotec", "tramadol", "codeine", "morphine", "pentazocine", "warfarin",
    "heparin", "methyldopa", "labetalol", "nifedipine", "hydralazine",
    "magnesium sulfate", "magnesium sulphate", "indomethacin", "artesunate",
    "quinine", "fansidar", "sulfadoxine", "pyrimethamine", "iron",
    "folic acid", "folate", "calcium", "multivitamin", "multivitamins",
    "vitamin a", "vitamin c", "zinc", "agbo", "herbal mixture", "concoction",
    "native medicine", "potash", "kaun", "gripe water", "antibiotic",
    "antibiotics", "painkiller", "painkillers", "sedative", "sedatives"
]


class ClinicalInvariantValidator:
    """
    Deterministic validator that inspects candidate adapted responses against clinical invariants.
    Guarantees:
    1. Upstream category prefix is preserved ('EMERGENCY:', 'PRIORITY:', 'ROUTINE:').
    2. Zero unauthorized drug names, dosages, or herbal concoctions are introduced.
    3. Medication instruction omission is detected and strictly prohibited.
    4. Exact medication-to-dosage and instruction bindings are verified (zero cross-swapping).
    5. Unambiguous word-based numbers ('three days', 'two tablets') are normalized and checked.
    6. Medication instruction polarity is preserved (prohibition cannot be inverted to permission,
       and permitted supplements/medications cannot be inverted to prohibition).
    7. Exact numerical dosages, durations, and administration frequencies are preserved without mutation.
    8. Emergency directness & contacts are preserved (zero delay/questions, mandatory 112/ODEMSA).
    9. Multi-sentence clinical core invariance: ALL meaningful reference sentences, warnings,
       and short imperatives (e.g. 'Do not wait.', 'Go to clinic.') are preserved.
    10. Mandatory referral destinations and timeframes are verified using word-boundary matching.
    """

    def __init__(self):
        self.validation_failures: List[Dict[str, Any]] = []

    def _normalize_numerical_words(self, text: str) -> str:
        """
        Normalizes unambiguous written numbers and unit words to standardized numeric strings.
        """
        norm = text.lower()
        for pat, rep in UNIT_NORMALIZATIONS:
            norm = re.sub(pat, rep, norm)
        target_units = r"(?:days?|weeks?|months?|hours?|tablet|capsule|drop|teaspoon|tablespoon|ml|mg|mcg|g|iu|dose|times?)"
        for word, num in WORD_TO_NUMBER.items():
            pattern = rf"\b{re.escape(word)}\s+({target_units})\b"
            norm = re.sub(pattern, rf"{num} \1", norm)
            norm = re.sub(rf"\b{re.escape(word)}\s+(times?\s+(?:a|per)\s+day)\b", rf"{num} \1", norm)
        norm = re.sub(r"\bonce\s+(daily|a\s+day)\b|\b1\s+time\s+(a|per)\s+day\b|\bone\s+time\s+(a|per)\s+day\b", "once daily", norm)
        norm = re.sub(r"\btwice\s+(daily|a\s+day)\b|\b2\s+times\s+(a|per)\s+day\b|\btwo\s+times\s+(a|per)\s+day\b", "twice daily", norm)
        norm = re.sub(r"\bthrice\s+(daily|a\s+day)\b|\b3\s+times\s+(a|per)\s+day\b|\bthree\s+times\s+(a|per)\s+day\b", "thrice daily", norm)
        return norm

    def _extract_dosages(self, text: str) -> List[Tuple[float, str]]:
        """
        Extracts (value, unit) dosage pairs from normalized text, supporting fractions and decimals.
        """
        norm = self._normalize_numerical_words(text)
        pattern = r"\b(?:(\d+/\d+)|(\d+(?:\.\d+)?))\s*(mg|ml|mcg|g|iu|tablets?|capsules?|drops?|teaspoons?|tablespoons?|doses?)\b"
        matches = []
        for match in re.finditer(pattern, norm, re.IGNORECASE):
            if match.group(1):
                n, d = match.group(1).split('/')
                val = float(n) / float(d) if float(d) != 0 else 0.0
            else:
                val = float(match.group(2))
            unit = match.group(3).lower()
            matches.append((val, unit))
        return matches

    def _extract_durations(self, text: str) -> List[Tuple[int, str]]:
        """
        Extracts (value, unit) duration pairs from normalized text.
        """
        norm = self._normalize_numerical_words(text)
        pattern = r"\b(\d+)\s+(days?|weeks?|months?)\b"
        matches = []
        for match in re.finditer(pattern, norm, re.IGNORECASE):
            val = int(match.group(1))
            unit = match.group(2).lower()
            matches.append((val, unit))
        return matches

    def _extract_frequencies(self, text: str) -> List[str]:
        """
        Extracts normalized dosing frequencies from text.
        """
        norm = self._normalize_numerical_words(text)
        freqs = []
        if re.search(r"\bonce\s+daily\b", norm):
            freqs.append("once daily")
        if re.search(r"\btwice\s+daily\b", norm):
            freqs.append("twice daily")
        if re.search(r"\bthrice\s+daily\b", norm):
            freqs.append("thrice daily")
        hour_match = re.search(r"\bevery\s+(\d+)\s+hours?\b", norm)
        if hour_match:
            freqs.append(f"every {hour_match.group(1)} hours")
        return freqs

    def _get_medication_clauses(self, text: str) -> Dict[str, str]:
        """
        Extracts the surrounding clause/sentence for each medication mentioned in text.
        Handles compound sentences connected by 'and', 'while', ';', '.', '\n'.
        """
        clauses = re.split(r'[.!\n;]|\b(?:and|while|also)\s+(?=[a-z\s]*\b(?:take|use|drink|administer|avoid|do\s+not)\b)', text)
        med_contexts = {}
        for med in MEDICATION_AND_SUPPLEMENT_TOKENS:
            pat = rf"\b{re.escape(med)}\b"
            matching_clauses = [c.strip() for c in clauses if re.search(pat, c, re.IGNORECASE)]
            if matching_clauses:
                med_contexts[med] = " ".join(matching_clauses)
        return med_contexts

    def _extract_medication_bindings(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Binds dosages, durations, and frequencies to their specific medication using
        both clause splitting and character-distance token proximity.
        Guarantees that compound sentences (e.g. 'Take 500 mg paracetamol and 200 mg iron')
        cannot swap dosages across medications.
        """
        norm = self._normalize_numerical_words(text)
        
        # 1. Identify all medication mentions and their spans
        med_mentions = []
        for med in MEDICATION_AND_SUPPLEMENT_TOKENS:
            for m in re.finditer(rf"\b{re.escape(med)}\b", norm, re.IGNORECASE):
                med_mentions.append((med, m.start(), m.end()))

        bindings = {med: {"dosages": [], "durations": [], "frequencies": [], "clause": ""} for med, _, _ in med_mentions}
        if not med_mentions:
            return bindings

        # Also populate clauses for polarity checks
        clauses = self._get_medication_clauses(norm)
        for med in bindings:
            bindings[med]["clause"] = clauses.get(med, "")

        # 2. Bind dosages to the closest medication mention
        dosage_pattern = r"\b(?:(\d+/\d+)|(\d+(?:\.\d+)?))\s*(mg|ml|mcg|g|iu|tablets?|capsules?|drops?|teaspoons?|tablespoons?|doses?)\b"
        for d_match in re.finditer(dosage_pattern, norm, re.IGNORECASE):
            if d_match.group(1):
                n, d = d_match.group(1).split('/')
                val = float(n) / float(d) if float(d) != 0 else 0.0
            else:
                val = float(d_match.group(2))
            unit = d_match.group(3).lower()
            ds, de = d_match.start(), d_match.end()
            
            closest_med = None
            min_dist = float('inf')
            for med_name, ms, me in med_mentions:
                dist = max(0, ms - de) if ms >= de else max(0, ds - me)
                if dist < min_dist:
                    min_dist = dist
                    closest_med = med_name
            if closest_med:
                bindings[closest_med]["dosages"].append((val, unit))

        # 3. Bind durations to the closest medication mention
        dur_pattern = r"\b(\d+)\s+(days?|weeks?|months?)\b"
        for dur_match in re.finditer(dur_pattern, norm, re.IGNORECASE):
            val = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            ds, de = dur_match.start(), dur_match.end()
            
            closest_med = None
            min_dist = float('inf')
            for med_name, ms, me in med_mentions:
                dist = max(0, ms - de) if ms >= de else max(0, ds - me)
                if dist < min_dist:
                    min_dist = dist
                    closest_med = med_name
            if closest_med:
                bindings[closest_med]["durations"].append((val, unit))

        # 4. Bind frequencies to the closest medication mention
        freq_patterns = [
            r"\bonce\s+daily\b", r"\btwice\s+daily\b", r"\bthrice\s+daily\b", r"\bevery\s+\d+\s+hours?\b"
        ]
        for f_pat in freq_patterns:
            for f_match in re.finditer(f_pat, norm, re.IGNORECASE):
                freq_str = f_match.group(0).lower()
                fs, fe = f_match.start(), f_match.end()
                
                closest_med = None
                min_dist = float('inf')
                for med_name, ms, me in med_mentions:
                    dist = max(0, ms - fe) if ms >= fe else max(0, fs - me)
                    if dist < min_dist:
                        min_dist = dist
                        closest_med = med_name
                if closest_med:
                    bindings[closest_med]["frequencies"].append(freq_str)

        return bindings

    def validate(
        self,
        candidate_response: str,
        reference_response: str,
        urgency_category: str,
        user_message: str,
        language: str = "English"
    ) -> Tuple[bool, Optional[str]]:
        cat_lower = urgency_category.lower()
        ref_lower = reference_response.lower()
        cand_lower = candidate_response.lower()

        # 1. Prefix Verification
        expected_prefix = f"{urgency_category.upper()}:"
        if not candidate_response.startswith(expected_prefix):
            reason = f"ERR_PREFIX_MISMATCH: Response does not start with {expected_prefix}"
            self._log_failure(reason, candidate_response, reference_response, user_message)
            return False, reason

        # 2. Medication Instruction Omission & Dosage-to-Medication Association
        ref_norm = self._normalize_numerical_words(ref_lower)
        cand_norm = self._normalize_numerical_words(cand_lower)
        
        ref_meds = self._extract_medication_bindings(ref_norm)
        cand_meds = self._extract_medication_bindings(cand_norm)

        # A. Detect omission of reference medication from candidate
        for med in ref_meds:
            if med not in cand_meds:
                reason = f"ERR_OMITTED_MEDICATION: Prescribed medication/supplement '{med}' in reference response was omitted from candidate"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

        # B. Detect ungrounded medication introduction in candidate
        for med in cand_meds:
            if med not in ref_meds:
                reason = f"ERR_INVENTED_MEDICATION: Detected ungrounded drug/supplement token '{med}'"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

        # C. Dosage, duration, frequency, and polarity association per medication
        for med, r_bind in ref_meds.items():
            c_bind = cand_meds[med]

            # Dosages associated with this specific medication
            ref_dosages = r_bind["dosages"]
            cand_dosages = c_bind["dosages"]
            if ref_dosages and not cand_dosages:
                reason = f"ERR_OMITTED_DOSAGE: Dosage for '{med}' was omitted from candidate"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason
            for r_val, r_unit in ref_dosages:
                norm_r_unit = r_unit.rstrip('s')
                matching_cands = [c_val for c_val, c_u in cand_dosages if c_u.rstrip('s') == norm_r_unit]
                if not matching_cands:
                    reason = f"ERR_OMITTED_DOSAGE: Dosage {r_val} {r_unit} for '{med}' was omitted from candidate"
                    self._log_failure(reason, candidate_response, reference_response, user_message)
                    return False, reason
                if not any(abs(c_val - r_val) < 1e-4 for c_val in matching_cands):
                    reason = f"ERR_NUMERICAL_DOSAGE_MUTATED: Dosage for '{med}' was altered from {r_val} {r_unit} to {matching_cands[0]} {r_unit}"
                    self._log_failure(reason, candidate_response, reference_response, user_message)
                    return False, reason

            # Durations associated with this specific medication
            ref_durations = r_bind["durations"]
            cand_durations = c_bind["durations"]
            if ref_durations and not cand_durations:
                reason = f"ERR_OMITTED_DURATION: Duration for '{med}' was omitted from candidate"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason
            for r_dur, r_dunit in ref_durations:
                norm_dunit = r_dunit.rstrip('s')
                matching_durs = [c_v for c_v, c_u in cand_durations if c_u.rstrip('s') == norm_dunit]
                if not matching_durs:
                    reason = f"ERR_OMITTED_DURATION: Duration {r_dur} {r_dunit} for '{med}' was omitted from candidate"
                    self._log_failure(reason, candidate_response, reference_response, user_message)
                    return False, reason
                if not any(c_v == r_dur for c_v in matching_durs):
                    reason = f"ERR_NUMERICAL_DOSAGE_MUTATED: Duration for '{med}' was altered from {r_dur} {r_dunit} to {matching_durs[0]} {r_dunit}"
                    self._log_failure(reason, candidate_response, reference_response, user_message)
                    return False, reason

            # Frequencies associated with this specific medication
            ref_freqs = r_bind["frequencies"]
            cand_freqs = c_bind["frequencies"]
            if ref_freqs and not cand_freqs:
                reason = f"ERR_OMITTED_FREQUENCY: Frequency for '{med}' was omitted from candidate"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason
            for rf in ref_freqs:
                if rf not in cand_freqs:
                    reason = f"ERR_NUMERICAL_DOSAGE_MUTATED: Dosing frequency '{rf}' for '{med}' was altered or omitted"
                    self._log_failure(reason, candidate_response, reference_response, user_message)
                    return False, reason

            # Polarity associated with this specific medication
            ref_pol_clause = r_bind["clause"] or ref_norm
            cand_pol_clause = c_bind["clause"] or cand_norm
            is_valid_pol, pol_reason = self._verify_medication_polarity(cand_pol_clause, ref_pol_clause, med)
            if not is_valid_pol:
                self._log_failure(pol_reason, candidate_response, reference_response, user_message)
                return False, pol_reason

        # 3. Overall Negative Token Screen & Polarity Verification
        for pattern in FORBIDDEN_MEDICATION_TOKENS:
            match_cand = re.search(pattern, cand_norm)
            if match_cand:
                match_ref = re.search(pattern, ref_norm)
                if not match_ref:
                    reason = f"ERR_INVENTED_MEDICATION: Detected ungrounded drug/dosage token '{match_cand.group(0)}'"
                    self._log_failure(reason, candidate_response, reference_response, user_message)
                    return False, reason
                else:
                    # Token exists in reference; verify instruction polarity has not been reversed
                    token_str = match_cand.group(0)
                    is_valid_pol, pol_reason = self._verify_medication_polarity(cand_lower, ref_lower, token_str)
                    if not is_valid_pol:
                        self._log_failure(pol_reason, candidate_response, reference_response, user_message)
                        return False, pol_reason

        # 4. Overall Dosage Numerical, Duration & Frequency Invariance (Normalized)
        ref_dosages = self._extract_dosages(ref_norm)
        cand_dosages = self._extract_dosages(cand_norm)
        for ref_val, ref_unit in ref_dosages:
            norm_ref_unit = ref_unit.rstrip('s')
            matching_cand_vals = [
                c_val for c_val, c_u in cand_dosages
                if c_u.rstrip('s') == norm_ref_unit
            ]
            if not matching_cand_vals:
                reason = f"ERR_NUMERICAL_DOSAGE_MUTATED: Prescribed dosage {ref_val} {ref_unit} was omitted from candidate"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason
            if not any(abs(c_val - ref_val) < 1e-4 for c_val in matching_cand_vals):
                reason = f"ERR_NUMERICAL_DOSAGE_MUTATED: Prescribed dosage {ref_val} {ref_unit} was altered to {matching_cand_vals[0]} {ref_unit}"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

        ref_durations = self._extract_durations(ref_norm)
        cand_durations = self._extract_durations(cand_norm)
        for ref_dur, ref_dunit in ref_durations:
            norm_dunit = ref_dunit.rstrip('s')
            matching_cand_durs = [
                c_val for c_val, c_u in cand_durations
                if c_u.rstrip('s') == norm_dunit
            ]
            if not matching_cand_durs:
                reason = f"ERR_NUMERICAL_DOSAGE_MUTATED: Clinical duration {ref_dur} {ref_dunit} was omitted from candidate"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason
            if not any(c_val == ref_dur for c_val in matching_cand_durs):
                reason = f"ERR_NUMERICAL_DOSAGE_MUTATED: Clinical duration {ref_dur} {ref_dunit} was altered to {matching_cand_durs[0]} {ref_dunit}"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

        ref_freqs = self._extract_frequencies(ref_norm)
        cand_freqs = self._extract_frequencies(cand_norm)
        for rf in ref_freqs:
            if rf not in cand_freqs:
                reason = f"ERR_NUMERICAL_DOSAGE_MUTATED: Dosing frequency '{rf}' was altered or omitted"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

        # 5. Emergency Directness & Delay Verification
        if cat_lower == "emergency":
            # Emergency replies must have NO question marks
            if "?" in candidate_response:
                reason = "ERR_EMERGENCY_DELAY: Emergency response contains conversational question mark"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

            # Emergency must contain emergency contacts
            if "112" not in candidate_response or "0812 756 5478" not in candidate_response:
                reason = "ERR_MISSING_EMERGENCY_CONTACTS: 112 or ODEMSA contact omitted"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

        # 6. Multi-Sentence Clinical Core Invariance Check (CCP-01)
        ref_core = reference_response
        for pfix in ["EMERGENCY:", "PRIORITY:", "ROUTINE:"]:
            if ref_core.startswith(pfix):
                ref_core = ref_core[len(pfix):].strip()

        # Enforce critical condition warning markers
        for marker in CRITICAL_CLINICAL_MARKERS:
            if re.search(marker, ref_core.lower()):
                if not re.search(marker, cand_lower):
                    clean_marker = marker.replace(r"\b", "").replace(r"\s+", " ")
                    reason = f"ERR_OMITTED_WARNING: Mandatory clinical warning '{clean_marker}' was omitted from candidate"
                    self._log_failure(reason, candidate_response, reference_response, user_message)
                    return False, reason

        # Check every clinical sentence/clause in reference response (No length bypass)
        ref_sentences = [s.strip() for s in re.split(r'[.!\n;]', ref_core) if len(s.strip()) >= 3]
        cand_words = set(re.findall(r"\b\w{3,}\b", cand_lower))
        stop_words = {"the", "and", "you", "your", "for", "with", "that", "this"}

        for s in ref_sentences:
            s_lower = s.lower()
            # A. Check mandatory imperatives first
            imperative_found_in_ref = False
            for pat, name in MANDATORY_IMPERATIVE_PATTERNS:
                if re.search(pat, s_lower):
                    imperative_found_in_ref = True
                    if not re.search(pat, cand_lower):
                        reason = f"ERR_CLINICAL_CORE_MUTATED: Mandatory clinical imperative omitted or weakened: '{s}'"
                        self._log_failure(reason, candidate_response, reference_response, user_message)
                        return False, reason

            # B. Check content words recall
            content_words = [w for w in re.findall(r"\b\w{3,}\b", s_lower) if w not in stop_words]
            if content_words:
                s_words_set = set(content_words)
                overlap = s_words_set.intersection(cand_words)
                recall = len(overlap) / len(s_words_set)
                if len(s_words_set) <= 2:
                    if not imperative_found_in_ref and recall < 1.0:
                        reason = f"ERR_CLINICAL_CORE_MUTATED: Short imperative/clinical advice altered: '{s}'"
                        self._log_failure(reason, candidate_response, reference_response, user_message)
                        return False, reason
                else:
                    if recall < 0.65:
                        reason = f"ERR_CLINICAL_CORE_MUTATED: Clinical core advice from reference response was altered (missing sentence content: '{s[:40]}...')"
                        self._log_failure(reason, candidate_response, reference_response, user_message)
                        return False, reason

        # 7. Mandatory Action / Referral Preservation (Word-Boundary Anchored)
        if cat_lower == "priority":
            has_facility_referral = any(re.search(pat, cand_lower) for pat in REFERRAL_PATTERNS)
            if not has_facility_referral:
                reason = "ERR_WEAKENED_REFERRAL: Priority response omitted healthcare facility referral"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

            # Verify timeframe presence
            timeframe_patterns = [
                r"\b24\b", r"\b48\b", r"\btoday\b", r"\bpromptly\b", r"\bimmediately\b",
                r"\bloni\b", r"\bkiakia\b", r"\bsharp-sharp\b", r"\blaarin\s+wakati\b"
            ]
            has_timeframe = any(re.search(pat, cand_lower) for pat in timeframe_patterns)
            if not has_timeframe:
                reason = "ERR_WEAKENED_REFERRAL: Priority response omitted referral timeframe"
                self._log_failure(reason, candidate_response, reference_response, user_message)
                return False, reason

        return True, None

    def _verify_medication_polarity(self, cand_lower: str, ref_lower: str, token: str) -> Tuple[bool, Optional[str]]:
        """
        Verifies that a medication instruction's polarity (prohibition vs permission) is preserved.
        Guarantees that:
        - If a medication/supplement is prohibited in reference, candidate MUST prohibit it and NOT permit it.
        - If a medication/supplement is permitted in reference, candidate MUST NOT prohibit it and MUST permit it.
        """
        token_pat = r"\b" + re.escape(token) + r"\b"
        ref_clauses = [s for s in re.split(r'[\.\n;]', ref_lower) if re.search(token_pat, s)]
        cand_clauses = [s for s in re.split(r'[\.\n;]', cand_lower) if re.search(token_pat, s)]

        if not ref_clauses or not cand_clauses:
            return True, None

        ref_text = " ".join(ref_clauses)
        cand_text = " ".join(cand_clauses)

        ref_is_prohibited = any(re.search(p, ref_text) for p in PROHIBITION_PATTERNS)
        ref_is_permitted = any(re.search(p, ref_text) for p in PERMISSION_PATTERNS)

        cand_has_permission = any(re.search(p, cand_text) for p in PERMISSION_PATTERNS)
        cand_has_prohibition = any(re.search(p, cand_text) for p in PROHIBITION_PATTERNS)

        if ref_is_prohibited:
            if cand_has_permission or not cand_has_prohibition:
                return False, f"ERR_MEDICATION_POLARITY_INVERSION: Prohibited medication '{token}' was rendered permissive or stripped of prohibition"

        if ref_is_permitted and not ref_is_prohibited:
            if cand_has_prohibition:
                return False, f"ERR_MEDICATION_POLARITY_INVERSION: Permitted medication/supplement '{token}' was rendered prohibited"
            if not cand_has_permission:
                return False, f"ERR_MEDICATION_POLARITY_INVERSION: Permitted medication/supplement '{token}' was stripped of permissive guidance"

        return True, None

    def _log_failure(self, reason: str, candidate: str, reference: str, user_message: str):
        self.validation_failures.append({
            "timestamp": time.time(),
            "reason": reason,
            "user_message": user_message,
            "candidate_response": candidate,
            "reference_response": reference
        })


class TemplateAdaptationEngine:
    """
    Lightweight, deterministic conversational adaptation engine.
    Assembles a four-slot response while enforcing complete clinical fidelity.
    """

    def __init__(self):
        self.phrase_banks = PHRASE_BANKS
        self.language_lexicons = LANGUAGE_SCOPED_SYMPTOM_LEXICONS
        self.symptom_lexicon = SYMPTOM_LEXICON  # backward compatibility
        self.validator = ClinicalInvariantValidator()

    def detect_domain(self, user_message: str, reference_response: str = "") -> str:
        """
        Differentiates pregnancy-related inquiries from infant-care inquiries.
        """
        text = normalize_text(f"{user_message} {reference_response}")
        infant_patterns = [
            r"\b(infant|baby|newborn|pikin|omo|breastfeed\w*|latch\w*|immuniz\w*|vaccin\w*|cord\s+care|teething|diaper|circumcis\w*|wean\w*)\b",
            r"\b(itoju\s+omo|oju\s+omo|abere\s+ajesara|ajesara|fifun\s+lomu|fifun\s+l'?omu|ose\s+mefa)\b",
            r"\b(six\s+weeks?\s+vaccine|10\s+weeks?\s+vaccine|14\s+weeks?\s+vaccine|9\s+months?\s+vaccine)\b"
        ]
        pregnancy_patterns = [
            r"\b(pregnant|pregnancy|trimester|fetal|fetus|womb|antenatal|anc|oyun|alaboyun|belly|water\s+broke|labour|labor|contractions?)\b",
            r"\b(early\s+pregnancy|late\s+pregnancy|first\s+trimester|second\s+trimester|third\s+trimester)\b"
        ]
        infant_score = sum(1 for p in infant_patterns if re.search(p, text))
        pregnancy_score = sum(1 for p in pregnancy_patterns if re.search(p, text))

        if infant_score > pregnancy_score:
            return "infant"
        elif pregnancy_score > infant_score:
            return "pregnancy"
        return "general"

    def is_generic_greeting(self, message: str) -> bool:
        """
        Detects if the user message is a general greeting or conversational prompt without specific medical content.
        """
        if not message:
            return True
        msg_clean = re.sub(r"[^\w\s]", "", message.lower()).strip()
        greeting_patterns = [
            r"^(hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening|greetings|well\s+done)(\s+nurse|\s+doctor|\s+ma|\s+sir|\s+there)?(\s+i\s+have\s+a\s+question|\s+how\s+are\s+you|\s+how\s+far)?(\s+about\s+.*|\s+today)?$",
            r"^(hello|hi)(\s+nurse|\s+doctor|\s+ma)?\s+(i\s+have\s+a\s+question|how\s+are\s+you|how\s+far|how\s+una\s+dey|e\s+kaaro|bawo\s+ni)(\s+about\s+.*|\s+today)?$",
            r"^(e\s+nle|e\s+kaaro|e\s+kaasan|e\s+kaale|bawo\s+ni)(\s+ma|\s+o)?$",
            r"^(how\s+far|how\s+una\s+dey|wetin\s+dey|good\s+day)(\s+nurse|\s+doctor)?$"
        ]
        return any(re.match(p, msg_clean) for p in greeting_patterns)

    def extract_symptom(self, message: str, language: str = "English") -> Optional[str]:
        """
        Extracts an explicitly stated, affirmed symptom from the user message.
        Guarantees:
        1. Uses language-specific symptom lexicons (English, Yoruba, Nigerian Pidgin).
        2. Strictly ignores and filters out negated symptoms (e.g., 'not vomiting', 'no fever').
        3. Never hallucinates or infers unstated symptoms.
        Returns None if no supported symptom is explicitly and affirmatively stated.
        """
        if not message:
            return None

        lang_key = language if language in self.language_lexicons else "English"
        lexicon = self.language_lexicons[lang_key]
        msg_lower = message.lower()

        affirmed_symptoms = []

        for key, description in lexicon.items():
            pattern = r"\b" + re.escape(key) + r"\b"
            for match in re.finditer(pattern, msg_lower):
                start, end = match.start(), match.end()
                if not self._is_symptom_negated(msg_lower, start, end, language=lang_key):
                    affirmed_symptoms.append(description)
                    break  # Record once per lexicon key

        if affirmed_symptoms:
            return affirmed_symptoms[0]

        return None

    def _is_symptom_negated(self, text: str, start: int, end: int, language: str = "English") -> bool:
        """
        Determines whether a matched symptom token is within a negative or resolved scope.
        """
        # Preceding context clause check
        pre = text[:start]
        clauses = re.split(r'[\.,;!\?]|\b(but|however|although|yet|ṣugbọn|sugbon)\b', pre)
        clause = clauses[-1] if clauses else pre

        if language == "Yoruba":
            neg_pattern = r"\b(kò|ko|kò\s+tíì|ko\s+tii|kì\s+í|ki\s+i|kọ́|kò\s+sí|ko\s+si|laisi|lai\s+si|kò\s+ní|ko\s+ni)\b"
        elif language == "Nigerian Pidgin":
            neg_pattern = r"\b(no|never|no\s+de|no\s+dey|not|stop|no\s+more|no\s+longer|no\s+get|never\s+get)\b"
        else: # English
            neg_pattern = r"\b(no|not|never|neither|nor|without|stop|stopped|no\s+longer|haven'?t|hasn'?t|hadn'?t|don'?t|doesn'?t|didn'?t|ain'?t|won'?t|cannot|can'?t|free\s+of)\b"

        if re.search(neg_pattern, clause, re.IGNORECASE):
            return True

        # Coordinated negative check e.g. 'no headache or dizziness', 'ko si ebi tabi iba'
        coord_pattern = r"\b(no|without|ko\s+si|kò\s+sí)\s+([a-z\s]+)?\b(or|nor|and|tabi)\s*$"
        if re.search(coord_pattern, clause, re.IGNORECASE):
            return True

        # Suffix negation check e.g. 'vomiting has stopped', 'belly pain don stop'
        post = text[end:end+25]
        post_clause = re.split(r'[\.,;!\?]', post)[0]
        if language == "Nigerian Pidgin":
            post_neg = r"\b(don\s+)?(stop|clear|finish)\b"
        elif language == "Yoruba":
            post_neg = r"\b(ti\s+)?(dẹkun|dekun|tan)\b"
        else:
            post_neg = r"\b(is\s+|has\s+)?(stopped|stop|gone|cleared|cured)\b"

        if re.search(post_neg, post_clause, re.IGNORECASE):
            return True

        return False

    def adapt_response(
        self,
        user_message: str,
        reference_response: str,
        urgency_category: str,
        language: str = "English",
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adapts an approved reference response into a conversational four-slot response.
        If urgency is EMERGENCY, strictly bypasses conversational scaffolding.
        If validation fails, falls back silently to the exact reference response.
        """
        start_time = time.perf_counter()
        cat_lower = urgency_category.lower()
        lang_key = language if language in self.phrase_banks else "English"
        pbank = self.phrase_banks[lang_key]

        # ----------------------------------------------------
        # 1. EMERGENCY BYPASS: Immediate Direct Escalation
        # ----------------------------------------------------
        if cat_lower == "emergency":
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "adapted_response": reference_response,
                "adaptation_applied": False,
                "urgency_category": "emergency",
                "language": lang_key,
                "latency_ms": elapsed_ms,
                "validation_passed": True,
                "fallback_triggered": False,
                "slot_breakdown": {
                    "empathy": None,
                    "mirroring": None,
                    "clinical_core": reference_response,
                    "action_referral": "Immediate Emergency Hospital Escalation"
                }
            }

        # ----------------------------------------------------
        # 2. Extract Medically Approved Clinical Core
        # ----------------------------------------------------
        clean_core = reference_response
        for pfix in ["PRIORITY:", "ROUTINE:", "EMERGENCY:"]:
            if clean_core.startswith(pfix):
                clean_core = clean_core[len(pfix):].strip()

        # ----------------------------------------------------
        # 3. Assemble Four Slots
        # ----------------------------------------------------
        # Determine Domain (pregnancy vs infant)
        active_domain = domain or self.detect_domain(user_message, reference_response)

        # Slot 1: Empathy Opening
        if cat_lower == "priority":
            empathy_list = pbank["empathy_priority"]
        else:
            domain_key = f"empathy_routine_{active_domain}" if f"empathy_routine_{active_domain}" in pbank else "empathy_routine_pregnancy"
            empathy_list = pbank.get(domain_key, pbank["empathy_routine_pregnancy"])

        empathy_slot = empathy_list[len(user_message) % len(empathy_list)]

        # Slot 2: Symptom Mirroring
        is_greeting = self.is_generic_greeting(user_message)
        detected_symptom = self.extract_symptom(user_message, language=lang_key)

        if detected_symptom:
            mirror_slot = pbank["mirror_prefix"].format(symptom=detected_symptom)
        elif is_greeting:
            # For pure conversational greetings, omit Slot 2 framing
            mirror_slot = ""
        else:
            mirror_slot = pbank["mirror_prefix_general"]

        # Slot 3: Clinical Core
        clinical_core_slot = clean_core

        # Slot 4: Action & Referral (With Deduplication)
        if cat_lower == "priority":
            # Check if reference core already has an explicit facility referral
            has_existing_referral = any(re.search(pat, clean_core.lower()) for pat in REFERRAL_PATTERNS)
            if has_existing_referral:
                action_slot = pbank.get("action_priority_reinforcement", pbank["action_priority_reminder"])
            else:
                action_slot = pbank["action_priority_reminder"]
        else:
            action_slot = pbank["action_routine_closing"]

        # Format full adapted candidate response with mandatory uppercase category prefix
        prefix = f"{urgency_category.upper()}:"
        if mirror_slot:
            candidate_response = f"{prefix} {empathy_slot} {mirror_slot}{clinical_core_slot} {action_slot}"
        else:
            candidate_response = f"{prefix} {empathy_slot} {clinical_core_slot} {action_slot}"

        # ----------------------------------------------------
        # 4. Clinical Invariance Validation
        # ----------------------------------------------------
        is_valid, failure_reason = self.validator.validate(
            candidate_response=candidate_response,
            reference_response=reference_response,
            urgency_category=urgency_category,
            user_message=user_message,
            language=lang_key
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if not is_valid:
            # Deterministic Fallback: Return original reference response unmodified
            return {
                "adapted_response": reference_response,
                "adaptation_applied": False,
                "urgency_category": urgency_category,
                "language": lang_key,
                "latency_ms": elapsed_ms,
                "validation_passed": False,
                "fallback_triggered": True,
                "failure_reason": failure_reason,
                "slot_breakdown": None
            }

        return {
            "adapted_response": candidate_response,
            "adaptation_applied": True,
            "urgency_category": urgency_category,
            "language": lang_key,
            "latency_ms": elapsed_ms,
            "validation_passed": True,
            "fallback_triggered": False,
            "failure_reason": None,
            "slot_breakdown": {
                "empathy": empathy_slot,
                "mirroring": mirror_slot if mirror_slot else None,
                "clinical_core": clinical_core_slot,
                "action_referral": action_slot
            }
        }
