# MotherlyPulse: Multilingual Human Review Checklist (Post-Remediation)
**Comprehensive Linguistic Quality, Tone & Clinical Register Audit**

**Audit Date:** November 4, 2026  
**Auditor:** AI Evaluation Specialist & Linguistic QA Auditor  
**Scope:** English (`en`), Yoruba (`yo`), and Nigerian Pidgin (`pcm`) Phrase Banks & Language-Scoped Lexicons in [`template_adapter.py`](motherlypulse_app/template_adapter.py#L26-L168)  
**Status:** **REMEDIATION IMPLEMENTED — HUMAN CLINICAL & NATIVE LINGUISTIC REVIEW PENDING**

---

## 1. Post-Remediation Linguistic Architecture

Following the post-implementation audit, the multilingual subsystem was restructured to permanently resolve cross-language overwrites, regional dialect mixing, and contextual domain mismatches.

| Identified Defect | Pre-Remediation Behavior | Remediated Behavior | Verification Test |
|---|---|---|---|
| **Flat Lexicon Key Overwrite** | Pidgin `"tired": "how your body de weak"` overwrote English `"tired"`, polluting English responses with Pidgin. | `LANGUAGE_SCOPED_SYMPTOM_LEXICONS` completely partitions English, Yoruba, and Pidgin dictionaries. | `test_lexicon_cross_language_key_isolation` (PASS) |
| **Symptom Expansion Distortion** | `"vomiting"` expanded to `"vomiting and nausea"`, introducing unstated symptoms. | Stripped expansions: `"vomiting"` maps strictly to `"vomiting"`; `"hard stool"` to `"hard stools"`. | `test_symptom_expansion_elimination` (PASS) |
| **Yoruba Prenatal Greeting in Infant Care** | `"Ẹ ku oju lona ọmọ mà"` delivered to postnatal mothers inquiring about infant care. | Domain gating detects `pregnancy` vs `infant` domain; prenatal greeting is strictly excluded for infant inquiries. | `test_domain_aware_yoruba_greetings` (PASS) |
| **Yoruba Orthographic Colloquialism** | `"ibeere pataki le bi yi"` was phonetically distorted. | Corrected to standard written Yoruba: `"ibeere pataki lẹ bi yii"`. | Verified in `PHRASE_BANKS["Yoruba"]` |
| **Regional Honorific Mixing in Pidgin** | Used Yoruba honorific in Pidgin: `"Epele my sister"`. | Corrected to standard national Nigerian Pidgin: `"Pele my sister"`. | `test_pidgin_honorific_correction` (PASS) |

---

## 2. Updated Language-Scoped Symptom Lexicon Register

```python
LANGUAGE_SCOPED_SYMPTOM_LEXICONS = {
    "English": {
        "vomiting": "vomiting", "throw up": "vomiting", "nausea": "nausea",
        "hard stool": "hard stools", "constipat": "constipation",
        "swollen feet": "swelling in your feet", "swollen leg": "swelling in your legs",
        "swelling": "swelling", "headache": "headache", "fever": "fever",
        "hot body": "feeling feverish", "back pain": "back pain", "backache": "back pain",
        "breast pain": "breast pain", "cracked nipple": "cracked nipples",
        "sadness": "feeling sad", "crying": "crying spells", "tired": "feeling tired",
        "fatigue": "fatigue", "weakness": "weakness",
        "pain when peeing": "pain during urination", "burn when peeing": "burning during urination",
        "foul discharge": "vaginal discharge", "diarrhea": "diarrhea",
        "cough": "cough", "heat rash": "heat rash"
    },
    "Yoruba": {
        "ebi": "ebi ti ẹ n bi", "gbígbóná": "ara ti o n gbona", "gbigbona": "ara ti o n gbona",
        "igbẹ gbuuru": "igbẹ gbuuru", "igbe gbuuru": "igbẹ gbuuru", "orí fífó": "ori fifo",
        "ori fifo": "ori fifo", "ẹsẹ wiwu": "ẹsẹ ti o n wú", "ese wiwu": "ẹsẹ ti o n wú",
        "omú dídùn": "ọmu ti o n dun yin", "omu didun": "ọmu ti o n dun yin",
        "aibalẹ ọkan": "aibalẹ ọkan", "aibale okan": "aibalẹ ọkan",
        "aare": "aare ti o n da yin", "àárẹ̀": "aare ti o n da yin", "otutu": "otutu"
    },
    "Nigerian Pidgin": {
        "de vomit": "vomiting wey you talk", "vomit": "vomiting wey you talk",
        "body hot": "hot body wey you get", "fever": "fever wey you mention",
        "belly pain": "belly pain", "shit watery": "watery stool",
        "head de pain": "headache", "headache": "headache",
        "leg swell": "leg wey swell", "swollen leg": "leg wey swell",
        "breast pain": "breast pain", "sad": "how you de feel sad",
        "tired": "how your body de weak", "weak": "weak body"
    }
}
```

---

## 3. Updated Phrase Banks Register

### 3.1 English Phrase Bank
- **Empathy Routine (Pregnancy):**
  - *"I understand your question, and I am glad you are checking on your health."*
  - *"Thank you for reaching out about this. Taking proactive care of yourself and your baby is wonderful."*
  - *"That is a very common question during pregnancy and early motherhood."*
- **Empathy Routine (Infant Care):**
  - *"I understand your question, and I am glad you are checking on your baby's care."*
  - *"Thank you for reaching out. Taking proactive care of your baby is wonderful."*
  - *"That is a very common question in caring for your baby."*
- **Empathy Priority:**
  - *"I hear your concern, and it is very important that we address how you are feeling."*
  - *"I understand this symptom can be uncomfortable, and attending to it promptly protects both you and your baby."*
  - *"Thank you for sharing this with me. It is important to pay close attention to how your body is responding."*
- **Action Reminders:**
  - Reminder: *"Please consult your healthcare provider or visit your primary health centre within 24 to 48 hours for proper clinical assessment."*
  - Reinforcement (Deduplicated): *"Please make sure you follow through with this clinical visit promptly to protect your health."*

### 3.2 Yoruba Phrase Bank
- **Empathy Routine (Pregnancy):**
  - `Ẹ pẹlẹ mà, ibeere pataki lẹ bi yii, o si dara bi ẹ ṣe n tọju ara yin pẹlu ọmọ yin.`
  - `Ẹ ku oju lona ọmọ mà. O dara pupọ bi ẹ ṣe n tọpinpin ilera yin lẹsẹkẹsẹ.`
  - `Ẹ pẹlẹ mà, ọrọ to wọpọ ninu oyun ati itọju ọmọ lẹhin ibimọ ni eyi.`
- **Empathy Routine (Infant Care - Domain Gated):**
  - `Ẹ pẹlẹ mà, ibeere pataki lẹ bi yii, o si dara bi ẹ ṣe n tọju ara yin pẹlu ọmọ yin.`
  - `Ẹ pẹlẹ mà, ẹ ku itọju ọmọ. O dara pupọ bi ẹ ṣe n tọpinpin ilera ọmọ yin lẹsẹkẹsẹ.`
  - `Ẹ pẹlẹ mà, ọrọ to wọpọ ninu itọju ọmọ lẹhin ibimọ ni eyi.`
  *(Notice: `Ẹ ku oju lona ọmọ mà` is strictly excluded from infant care).*
- **Empathy Priority:**
  - `Ẹ pẹlẹ mà, mo gbọ bi ara ṣe n ṣe yin, o si ṣe pataki pupọ lati tete wa iranlọwọ.`
  - `Ẹ pẹlẹ mà, aibalẹ ọkan ti nkan yi n fa ko rọrun, ṣugbọn a gbọdọ ṣe abojuto rẹ lẹsẹkẹsẹ lati daabo bo ẹyin ati ọmọ yin.`
  - `Ẹ pẹlẹ mà, gbigbọ nipa bi ara ṣe n ṣe yin jẹ ki a mọ pe o yẹ ki oṣiṣẹ ilera yẹ yin wo laipẹ.`

### 3.3 Nigerian Pidgin Phrase Bank
- **Empathy Routine (Pregnancy):**
  - *"I hear you well-well, and e good say you de ask this important question about your health."*
  - *"Well done as you de take care of yourself and your pikin body."*
  - *"No worry, this question na wetin many pregnant women and new mothers de ask."*
- **Empathy Routine (Infant Care):**
  - *"I hear you well-well, and e good say you de ask this important question about your pikin."*
  - *"Well done as you de take care of your pikin body."*
  - *"No worry, this question na wetin many new mothers de ask."*
- **Empathy Priority:**
  - *"Sorry about how you dey feel, and e good say you talk am make we fit help you sharp-sharp."*
  - *"I understand say this thing de worry you, and we must check am well so that you and your pikin go dey safe."*
  - *"Pele my sister. This symptom wey you mention need make beta health worker check you quickly."* *(Corrected from `Epele`).*

---

## 4. Formal Human Review Checklist

The table below registers all phrase elements requiring physical clinical and linguistic verification by Nigerian healthcare professionals and certified linguists:

| Item ID | Content Under Review | Reviewer Role | Automated Status | Clinical / Native Status | Signature / Date |
|---|---|---|---|---|---|
| **REV-01** | Yoruba Infant Greeting: `Ẹ pẹlẹ mà, ẹ ku itọju ọmọ...` replacing antenatal greeting. | Yoruba Linguist & Bilingual Midwife | **VERIFIED** | **PENDING CLINICAL SIGN-OFF** | `[ ________________ ]` |
| **REV-02** | Yoruba Orthographic Standard: `ibeere pataki lẹ bi yii`. | Yoruba Linguistic Specialist | **VERIFIED** | **PENDING CLINICAL SIGN-OFF** | `[ ________________ ]` |
| **REV-03** | Pidgin Honorific Standard: `Pele my sister...` replacing `Epele`. | Nigerian Pidgin Specialist | **VERIFIED** | **PENDING CLINICAL SIGN-OFF** | `[ ________________ ]` |
| **REV-04** | Primary Health Centre Translation: `ile-iwosan alakọbẹrẹ`. | Ondo State Primary Care Physician | **VERIFIED** | **PENDING CLINICAL SIGN-OFF** | `[ ________________ ]` |
| **REV-05** | Emergency Danger Sign Translation: `ami eewu ilera to le koko`. | Emergency Ob/Gyn Specialist | **VERIFIED** | **PENDING CLINICAL SIGN-OFF** | `[ ________________ ]` |
| **REV-06** | Lexicon Symptom Pruning: Pure symptom mapping (`vomiting` without `and nausea`). | Clinical Safety Officer | **VERIFIED** | **PENDING CLINICAL SIGN-OFF** | `[ ________________ ]` |
| **REV-07** | Yoruba Priority Reinforcement: `Ẹ jọwọ ẹ ri daju pe ẹ lọ si ile-iwosan...`. | Bilingual Registered Nurse | **VERIFIED** | **PENDING CLINICAL SIGN-OFF** | `[ ________________ ]` |
| **REV-08** | Pidgin Priority Reinforcement: `Abeg make you sure say you follow this advice carry body go clinic sharp-sharp.`. | Bilingual Community Health Officer | **VERIFIED** | **PENDING CLINICAL SIGN-OFF** | `[ ________________ ]` |
