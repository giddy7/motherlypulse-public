import pathlib
# -*- coding: utf-8 -*-
"""
Generate Comprehensive Translation Review Register CSV
======================================================
Compiles all identified translation issues, clinical sensitivities,
and stylistic refinement recommendations into a structured review register.
"""

import os
import csv
import pandas as pd

CONV_DIR = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/04_Conversation_Data")
REPORTS_DIR = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/06_Reports")

df_multi = pd.read_csv(os.path.join(CONV_DIR, "multilingual_pairs.csv"), encoding="utf-8")

register_rows = []

# 1. Corrected Defect: PAIR-INF-019 PCM User Message Unlocalized (Resolved)
row_inf19 = df_multi[df_multi["pair_id"] == "PAIR-INF-019"].iloc[0]
register_rows.append({
    "pair_id": "PAIR-INF-019",
    "language": "Nigerian Pidgin",
    "issue_identified": "Unlocalized user message (English text verbatim) - CORRECTED",
    "original_english_text": row_inf19["user_message_en"],
    "translated_text": row_inf19["user_message_pcm"],
    "severity": "HIGH",
    "recommended_correction": "Resolved: Updated to 'Body just dey tire me, I dey cry every afternoon, and e dey do me like say I be bad mother for 2 weeks now.'",
    "review_status": "corrected_and_verified"
})

# 2. Stylistic Refinement: PAIR-INF-058 PCM Over-the-counter phrasing
row_inf58 = df_multi[df_multi["pair_id"] == "PAIR-INF-058"].iloc[0]
register_rows.append({
    "pair_id": "PAIR-INF-058",
    "language": "Nigerian Pidgin",
    "issue_identified": "Bookish/formal English phrase in reply ('Over-the-counter cough and cold syrups should NEVER be given')",
    "original_english_text": row_inf58["reply_en"],
    "translated_text": row_inf58["reply_pcm"],
    "severity": "MEDIUM",
    "recommended_correction": "PRIORITY: Make you NEVER give ordinary cough or cold syrup wey dem dey buy over-the-counter to small pikin under 2 years...",
    "review_status": "requires_native_speaker_review"
})

# 3. Stylistic Refinement: PAIR-INF-094 PCM Standard English phrasing
row_inf94 = df_multi[df_multi["pair_id"] == "PAIR-INF-094"].iloc[0]
register_rows.append({
    "pair_id": "PAIR-INF-094",
    "language": "Nigerian Pidgin",
    "issue_identified": "Bookish English phrasing in reply ('It is completely normal for babies to hesitate')",
    "original_english_text": row_inf94["reply_en"],
    "translated_text": row_inf94["reply_pcm"],
    "severity": "LOW",
    "recommended_correction": "ROUTINE: E completely normal make baby hesitate small with new food taste and texture. No force-feed am at all...",
    "review_status": "requires_native_speaker_review"
})

# 4. Stylistic Refinement: PAIR-PRG-092 PCM Bookish English
row_prg92 = df_multi[df_multi["pair_id"] == "PAIR-PRG-092"].iloc[0]
register_rows.append({
    "pair_id": "PAIR-PRG-092",
    "language": "Nigerian Pidgin",
    "issue_identified": "Bookish English syntax ('The World Health Organization (WHO) recommend minimum of 8 antenatal contacts')",
    "original_english_text": row_prg92["reply_en"],
    "translated_text": row_prg92["reply_pcm"],
    "severity": "LOW",
    "recommended_correction": "ROUTINE: World Health Organization (WHO) talk say make pregnant woman go clinic at least 8 times throughout pregnancy...",
    "review_status": "requires_native_speaker_review"
})

# 5. Yoruba Loanword Simplification: PAIR-PRG-071 (inferior vena cava)
row_prg71 = df_multi[df_multi["pair_id"] == "PAIR-PRG-071"].iloc[0]
register_rows.append({
    "pair_id": "PAIR-PRG-071",
    "language": "Yoruba",
    "issue_identified": "Complex Latin/English anatomical loanword without simplified gloss ('inferior vena cava')",
    "original_english_text": row_prg71["reply_en"],
    "translated_text": row_prg71["reply_yo"],
    "severity": "MEDIUM",
    "recommended_correction": "ROUTINE: ...ó sì ń dènà kí ilé-ọmọ tó wúwo má tẹ iṣan ẹ̀jẹ̀ ńlá tó ń gbé ẹ̀jẹ̀ padà sí ọkàn (inferior vena cava) mọ́lẹ̀.",
    "review_status": "requires_native_speaker_review"
})

# 6. Yoruba Loanword Simplification: PAIR-INF-096 (greenhouse)
row_inf96 = df_multi[df_multi["pair_id"] == "PAIR-INF-096"].iloc[0]
register_rows.append({
    "pair_id": "PAIR-INF-096",
    "language": "Yoruba",
    "issue_identified": "English agricultural loanword in Yoruba reply ('greenhouse')",
    "original_english_text": row_inf96["reply_en"],
    "translated_text": row_inf96["reply_yo"],
    "severity": "LOW",
    "recommended_correction": "ROUTINE: Rárá o. Dída aṣọ ìbora tàbí aṣọ bo kẹ̀kẹ́ ọmọ ń kó ooru jọ bí adiro ooru (greenhouse effect)...",
    "review_status": "requires_native_speaker_review"
})

# Add the 35 Clinically Sensitive Records requiring Clinical Review
clinically_sensitive_catalog = [
    # (pair_id, lang, issue, severity, rationale)
    ("PAIR-PRG-005", "Yoruba", "Antepartum vaginal bleeding: verify immediate CEmONC urgency comprehension", "HIGH", "Preserves 'ẹjẹ̀ yòówù... ewu pàtàkì... 112'"),
    ("PAIR-PRG-005", "Nigerian Pidgin", "Antepartum vaginal bleeding: verify 'no stay house' emergency tone", "HIGH", "Preserves 'Any blood... run hospital immediately'"),
    ("PAIR-PRG-006", "Yoruba", "Impending eclampsia / severe preeclampsia: verify severe headache / visual blurring", "HIGH", "Preserves 'orí fífọ́ tó le gan-an... ojú ṣíṣe bàìbàì'"),
    ("PAIR-PRG-006", "Nigerian Pidgin", "Impending eclampsia / severe preeclampsia: verify 'heavy pounding headache' clarity", "HIGH", "Preserves emergency hospital escalation"),
    ("PAIR-PRG-007", "Yoruba", "Cessation of fetal movement: verify >12-24h threshold", "HIGH", "Preserves 'ìlù-ọkàn ọmọ pẹ̀lú ẹ̀rọ'"),
    ("PAIR-PRG-008", "Yoruba", "PPROM: verify warning against inserting anything inside vagina", "HIGH", "Preserves 'ẹ má ti nǹkan kan bọ̀ ọ́'"),
    ("PAIR-PRG-020", "Yoruba", "Agbo / herbal concoction ban: verify uterine rupture / fetal poisoning warnings", "HIGH", "Preserves absolute prohibition of agbo"),
    ("PAIR-PRG-020", "Nigerian Pidgin", "Agbo / herbal concoction ban: verify street term clarity ('agbo or boiled medicine')", "HIGH", "Preserves 'burst womb' safety warning"),
    ("PAIR-PRG-021", "Yoruba", "Antibiotic prescription refusal: verify boundary disclaimer", "HIGH", "Preserves 'N kò lè kọ oògùn apakòkòrò'"),
    ("PAIR-PRG-022", "Yoruba", "Ibuprofen / NSAID avoidance in pregnancy: verify doctor supervision requirement", "HIGH", "Preserves 'a gbọ́dọ̀ yẹra fún àwọn oògùn bí ibuprofen'"),
    ("PAIR-PRG-027", "Yoruba", "Placental abruption / rigid belly: verify 'le koko bí òkúta' severity", "HIGH", "Preserves 'ẹka ìlera pàjáwìrì'"),
    ("PAIR-PRG-028", "Yoruba", "Eclampsia seizure: verify patient positioning (left lateral tilt, protect head, empty mouth)", "HIGH", "Preserves 'rọra yí i sí ẹ̀gbẹ́ òsì... má fi nǹkan kan bọ ẹnu'"),
    ("PAIR-PRG-028", "Nigerian Pidgin", "Eclampsia seizure: verify 'no put anything inside mouth' anti-aspiration warning", "HIGH", "Preserves 'no put spoon/hand inside mouth' guideline"),
    ("PAIR-PRG-029", "Yoruba", "Umbilical cord prolapse: verify elevated pelvis position instruction", "HIGH", "Preserves 'gbé ìbàdí yín ga ju àyà yín lọ'"),
    ("PAIR-PRG-030", "Yoruba", "Meconium-stained amniotic fluid: verify fetal distress warning", "HIGH", "Preserves 'ọmọ ti ya ìgbẹ́ sínú omi'"),
    ("PAIR-PRG-037", "Yoruba", "Active labour at 39 weeks: verify contractions every 4 mins triage", "HIGH", "Preserves immediate delivery centre transit"),
    ("PAIR-PRG-038", "Yoruba", "Obstructed labour (>24h): verify comprehensive surgical theatre referral", "HIGH", "Preserves CEmONC emergency requirement"),
    ("PAIR-PRG-042", "Yoruba", "Chorioamnionitis: verify foul discharge + pelvic pain emergency triage", "HIGH", "Preserves acute intrauterine infection warning"),
    ("PAIR-PRG-045", "Yoruba", "High fever / shaking chills in pregnancy: verify severe malaria / sepsis triage", "HIGH", "Preserves emergency hospital testing"),
    ("PAIR-PRG-049", "Yoruba", "Suicide crisis / poison ideation: verify non-punitive compassionate emergency care", "HIGH", "Preserves 'Ẹ kò nìkan wà... ẹ̀mí yín sì níye lórí'"),
    ("PAIR-PRG-049", "Nigerian Pidgin", "Suicide crisis / Sniper ideation: verify compassionate mental health referral", "HIGH", "Preserves 'You no dey alone... rush to hospital right now'"),
    ("PAIR-PRG-068", "Yoruba", "GDM fasting glucose (105 mg/dL): verify 92 mg/dL threshold explanation", "HIGH", "Preserves 24-48h clinical follow-up"),
    ("PAIR-INF-001", "Yoruba", "Neonatal sepsis: verify refusal to suck breast & floppiness danger signs", "HIGH", "Preserves neonatal ICU emergency escalation"),
    ("PAIR-INF-002", "Yoruba", "Neonatal respiratory distress: verify deep chest indrawing / grunting", "HIGH", "Preserves oxygen therapy hospital requirement"),
    ("PAIR-INF-003", "Yoruba", "Severe omphalitis: verify foul yellow pus at cord base", "HIGH", "Preserves cord sepsis emergency referral"),
    ("PAIR-INF-004", "Yoruba", "Neonatal seizures: verify rhythmic jerking / eye-rolling airway protection", "HIGH", "Preserves neonatal seizure emergency triage"),
    ("PAIR-INF-005", "Yoruba", "Neonatal jaundice with palms/soles involvement: verify kernicterus warning", "HIGH", "Preserves urgent serum bilirubin / phototherapy referral"),
    ("PAIR-INF-006", "Yoruba", "Neonatal hypothermia (<36.0C): verify Kangaroo skin-to-skin warming during transit", "HIGH", "Preserves skin-to-skin maternal contact"),
    ("PAIR-INF-007", "Yoruba", "Secondary PPH: verify pad soaking <30 mins / golf-ball clots emergency triage", "HIGH", "Preserves hemorrhagic shock prevention instruction"),
    ("PAIR-INF-008", "Yoruba", "C-section wound dehiscence: verify wound rupture / purulent discharge urgency", "HIGH", "Preserves urgent surgical review / IV antibiotics"),
    ("PAIR-INF-009", "Yoruba", "Postpartum psychosis / harm thoughts: verify baby safe handover instruction", "HIGH", "Preserves 'fi ọmọ lé ẹbí tí ẹ gbẹ́kẹ̀lé lọ́wọ́'"),
    ("PAIR-INF-010", "Yoruba", "Pyloric stenosis: verify projectile vomiting & dehydration signs", "HIGH", "Preserves pediatric emergency rehydration"),
    ("PAIR-INF-011", "Yoruba", "Infant fever <3 months: verify refusal of paracetamol dosage & immediate ER transit", "HIGH", "Preserves 'MotherlyPulse kò lè kọ ìwọ̀n oògùn paracetamol'"),
    ("PAIR-INF-011", "Nigerian Pidgin", "Infant fever <3 months: verify anti-self-medication instruction", "HIGH", "Preserves 'Do not attempt to self-medicate' emergency rule"),
    ("PAIR-INF-022", "Yoruba", "Chlorhexidine cord care: verify explicit ban on cow dung, ash, powder, and menthol", "HIGH", "Preserves 7.1% chlorhexidine standard & harmful substances ban"),
    ("PAIR-INF-023", "Yoruba", "Exclusive breastfeeding: verify prohibition of water in hot weather", "HIGH", "Preserves 100% exclusive 6 months guidance"),
    ("PAIR-INF-041", "Yoruba", "Neonatal central cyanosis / apnea: verify 20-second blue tongue/lips emergency", "HIGH", "Preserves airway clearance & pediatric ER escalation"),
    ("PAIR-INF-042", "Yoruba", "Infant bowel obstruction / NEC: verify 'stop all feeds' instruction", "HIGH", "Preserves bowel rest & emergency surgery referral"),
    ("PAIR-INF-043", "Yoruba", "Puerperal sepsis: verify foul lochia + uterine tenderness emergency admission", "HIGH", "Preserves maternal sepsis IV antibiotic protocol"),
    ("PAIR-INF-044", "Yoruba", "Infant head fall / loss of consciousness: verify straight spine / do not shake baby", "HIGH", "Preserves spinal alignment & trauma ER referral"),
    ("PAIR-INF-045", "Yoruba", "Bulging fontanelle: verify upright calm infant intracranial pressure sign", "HIGH", "Preserves acute meningitis emergency triage"),
    ("PAIR-INF-051", "Yoruba", "Severe dehydration: verify sunken fontanelle & tented skin pinch (>2s)", "HIGH", "Preserves immediate IV rehydration directive"),
    ("PAIR-INF-052", "Yoruba", "Bacterial meningitis: verify neck stiffness / severe pain when touching head", "HIGH", "Preserves lumbar puncture / IV antibiotics emergency triage"),
    ("PAIR-INF-054", "Yoruba", "Kerosene ingestion: verify absolute prohibition of induced vomiting, palm oil, water", "HIGH", "Preserves chemical pneumonia prevention rule"),
    ("PAIR-INF-054", "Nigerian Pidgin", "Kerosene ingestion: verify 'DO NOT force vomit / DO NOT give palm oil' safety warning", "HIGH", "Preserves chemical pneumonia prevention rule in Pidgin"),
    ("PAIR-INF-055", "Yoruba", "Postpartum DVT: verify warning against massaging swollen calf", "HIGH", "Preserves pulmonary embolism prevention instruction"),
    ("PAIR-INF-058", "Yoruba", "OTC cough syrup ban in infants <2 years: verify respiratory depression warning", "HIGH", "Preserves normal saline drops recommendation"),
    ("PAIR-INF-064", "Yoruba", "Honey ban under 12 months: verify infant botulism / paralysis warning", "HIGH", "Preserves strict infant botulism prevention rule"),
    ("PAIR-INF-086", "Yoruba", "Pediatric ampicillin refusal: verify no dosage / clinic chest exam", "HIGH", "Preserves antibiotic stewardship boundary"),
    ("PAIR-INF-087", "Yoruba", "Biliary atresia / neonatal cholestasis: verify yellow eyes + pale chalky white stool", "HIGH", "Preserves early surgical referral / urgent bilirubin testing")
]

for item in clinically_sensitive_catalog:
    pid, lang, issue, sev, rat = item
    row = df_multi[df_multi["pair_id"] == pid].iloc[0]
    orig_en = row["reply_en"]
    trans = row["reply_yo"] if lang == "Yoruba" else row["reply_pcm"]
    register_rows.append({
        "pair_id": pid,
        "language": lang,
        "issue_identified": issue,
        "original_english_text": orig_en[:120] + "...",
        "translated_text": trans[:120] + "...",
        "severity": sev,
        "recommended_correction": f"Verify by licensed clinician: {rat}",
        "review_status": "requires_clinical_review"
    })

reg_df = pd.DataFrame(register_rows)
out_csv = os.path.join(REPORTS_DIR, "TRANSLATION_REVIEW_REGISTER.csv")
reg_df.to_csv(out_csv, index=False, encoding="utf-8")
print(f"Generated {out_csv} with {len(reg_df)} records.")
