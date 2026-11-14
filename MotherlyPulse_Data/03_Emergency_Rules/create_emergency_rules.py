import pathlib
import csv
import json

rules = [
    # 1. Maternal Bleeding (Pregnancy)
    {
        "rule_id": "RUL-EMG-001",
        "population": "pregnant",
        "stage_or_age": "Any stage of pregnancy",
        "danger_sign": "Vaginal bleeding during pregnancy",
        "plain_description": "Any vaginal bleeding, spotting, or blood clots occurring while pregnant.",
        "example_user_phrasings_en": "I am pregnant and bleeding; blood is coming out of my private part; I see fresh blood on my pad; blood stains in my pants while pregnant (suggested wording for team adaptation; not from source)",
        "official_classification": "Severe obstetric complication / Antepartum haemorrhage",
        "triage_level": "Emergency",
        "recommended_action": "Immediate urgent transfer and clinical evaluation at the nearest hospital or comprehensive emergency obstetric care facility. Do not insert anything vaginally.",
        "source_id": "SRC-WHO-IMPAC-2017",
        "source_page_or_section": "Section S-15 to S-25",
        "clinical_review_status": "pending clinical review",
        "notes": "Triggers immediate fixed emergency escalation."
    },
    # 2. Maternal Bleeding (Postpartum)
    {
        "rule_id": "RUL-EMG-002",
        "population": "postpartum",
        "stage_or_age": "Postpartum (first 6 weeks)",
        "danger_sign": "Severe postpartum haemorrhage (PPH)",
        "plain_description": "Heavy bleeding soaking two or more large pads in an hour, or passing large blood clots with weakness.",
        "example_user_phrasings_en": "I gave birth and I cannot stop bleeding; blood is gushing out after delivery; I soaked two big pads in 30 minutes; I feel very faint and bleeding heavily (suggested wording for team adaptation; not from source)",
        "official_classification": "Postpartum haemorrhage (PPH)",
        "triage_level": "Emergency",
        "recommended_action": "Emergency medical treatment immediately. Call emergency transport or rush to the nearest emergency health facility for uterine massage, oxytocics, and resuscitation.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 12, p. 48-51",
        "clinical_review_status": "pending clinical review",
        "notes": "Leading cause of maternal mortality in Nigeria."
    },
    # 3. Convulsions / Seizures (Pregnancy/Postpartum)
    {
        "rule_id": "RUL-EMG-003",
        "population": "pregnant, postpartum",
        "stage_or_age": "Pregnancy (>20 weeks) or up to 6 weeks postpartum",
        "danger_sign": "Convulsions / Fits / Loss of consciousness",
        "plain_description": "Shaking fits, jerking movements, or loss of consciousness during pregnancy or following delivery.",
        "example_user_phrasings_en": "My pregnant sister is convulsing; she is shaking all over and passed out; she had a fit and cannot talk; sudden seizure during pregnancy (suggested wording for team adaptation; not from source)",
        "official_classification": "Eclampsia",
        "triage_level": "Emergency",
        "recommended_action": "Immediate emergency transfer to hospital. Clear airway, place on her left side, protect from injury, and administer magnesium sulphate as per protocol.",
        "source_id": "SRC-WHO-IMPAC-2017",
        "source_page_or_section": "Section S-45 to S-55",
        "clinical_review_status": "pending clinical review",
        "notes": "Extreme red flag requiring immediate emergency response."
    },
    # 4. Severe Headache & Visual Disturbances (Preeclampsia)
    {
        "rule_id": "RUL-EMG-004",
        "population": "pregnant, postpartum",
        "stage_or_age": "From 20 weeks pregnancy to 6 weeks postpartum",
        "danger_sign": "Severe persistent headache with blurred vision",
        "plain_description": "Intense throbbing headache not relieved by rest or paracetamol, accompanied by blurred vision, flashes, or spots.",
        "example_user_phrasings_en": "My head is pounding terribly and I cannot see clearly; severe headache and my eyes are blurring; I am seeing bright spots and my head hurts bad (suggested wording for team adaptation; not from source)",
        "official_classification": "Severe pre-eclampsia / Imminent eclampsia",
        "triage_level": "Emergency",
        "recommended_action": "Urgent hospital evaluation to assess blood pressure, check proteinuria, and initiate anti-hypertensive and anticonvulsant prophylaxis.",
        "source_id": "SRC-FMOH-LSS-2019",
        "source_page_or_section": "Module 4, Hypertensive Disorders in Pregnancy, p. 35-40",
        "clinical_review_status": "pending clinical review",
        "notes": "Warning sign of imminent seizure."
    },
    # 5. Severe Epigastric / Upper Abdominal Pain
    {
        "rule_id": "RUL-EMG-005",
        "population": "pregnant, postpartum",
        "stage_or_age": "Third trimester or early postpartum",
        "danger_sign": "Severe pain beneath the ribs / epigastric pain",
        "plain_description": "Severe, sharp, or persistent pain high in the stomach right under the ribs, often mistaken for severe heartburn.",
        "example_user_phrasings_en": "Terrible sharp pain under my right ribs; my upper stomach hurts so bad I cannot breathe; severe pain high up in my belly while pregnant (suggested wording for team adaptation; not from source)",
        "official_classification": "Imminent eclampsia / HELLP syndrome (Hepatic capsule distension)",
        "triage_level": "Emergency",
        "recommended_action": "Immediate hospital admission and urgent obstetric workup.",
        "source_id": "SRC-WHO-IMPAC-2017",
        "source_page_or_section": "Section S-48",
        "clinical_review_status": "pending clinical review",
        "notes": "Frequently misdiagnosed by patients as stomach acid."
    },
    # 6. Reduced or Absent Fetal Movement
    {
        "rule_id": "RUL-EMG-006",
        "population": "pregnant",
        "stage_or_age": "From 24 weeks gestation to delivery",
        "danger_sign": "Decreased, weak, or absent baby movement",
        "plain_description": "Significant reduction or complete absence of fetal kicks, turns, or flutters for several hours.",
        "example_user_phrasings_en": "My baby has not kicked since morning; I do not feel my baby moving at all; the baby movements have suddenly slowed down or stopped (suggested wording for team adaptation; not from source)",
        "official_classification": "Fetal distress / Risk of intrauterine demise",
        "triage_level": "Emergency",
        "recommended_action": "Immediate presentation at maternity centre for fetal heart auscultation and cardiotocography/ultrasound.",
        "source_id": "SRC-WHO-ANC-2016",
        "source_page_or_section": "Recommendation B.3, p. 48",
        "clinical_review_status": "pending clinical review",
        "notes": "Prompt presentation can save fetal life in acute placental compromise."
    },
    # 7. Difficulty Breathing / Chest Pain
    {
        "rule_id": "RUL-EMG-007",
        "population": "pregnant, postpartum",
        "stage_or_age": "Pregnancy or postpartum (0-12 months)",
        "danger_sign": "Acute shortness of breath or severe chest pain",
        "plain_description": "Sudden difficulty taking breath, gasping, rapid shallow breathing, or crushing pain in the chest.",
        "example_user_phrasings_en": "I cannot catch my breath; sudden tight chest pain and struggling to breathe; chest pain and gasping for air after delivery (suggested wording for team adaptation; not from source)",
        "official_classification": "Suspected pulmonary embolism / Pulmonary oedema / Severe cardiac distress",
        "triage_level": "Emergency",
        "recommended_action": "Emergency hospital admission with high-flow oxygen support and urgent medical evaluation.",
        "source_id": "SRC-WHO-IMPAC-2017",
        "source_page_or_section": "Section S-145",
        "clinical_review_status": "pending clinical review",
        "notes": "Pulmonary embolism is a major cause of maternal mortality."
    },
    # 8. Severe Abdominal Pain in Pregnancy
    {
        "rule_id": "RUL-EMG-008",
        "population": "pregnant",
        "stage_or_age": "Any stage of pregnancy",
        "danger_sign": "Severe, persistent abdominal pain or rigid belly",
        "plain_description": "Constant severe abdominal pain that is sharp or rigid, different from ordinary mild cramps.",
        "example_user_phrasings_en": "My whole stomach is painful and rock hard; unbearable belly pain that will not stop; excruciating lower abdomen tearing pain (suggested wording for team adaptation; not from source)",
        "official_classification": "Placental abruption / Uterine rupture / Acute abdomen / Ruptured ectopic",
        "triage_level": "Emergency",
        "recommended_action": "Immediate emergency facility transfer for surgical and obstetric evaluation.",
        "source_id": "SRC-WHO-IMPAC-2017",
        "source_page_or_section": "Section S-17 & S-140",
        "clinical_review_status": "pending clinical review",
        "notes": "May indicate concealed haemorrhage or uterine rupture."
    },
    # 9. High Fever Postpartum
    {
        "rule_id": "RUL-EMG-009",
        "population": "postpartum",
        "stage_or_age": "Postpartum (0 to 6 weeks)",
        "danger_sign": "High fever, chills, and foul-smelling vaginal discharge",
        "plain_description": "Body temperature feeling very hot, shivering chills, along with bad-smelling lochia or lower abdominal tenderness.",
        "example_user_phrasings_en": "I have high fever and shivering after birth; my lochia discharge smells terrible and hot body; fever and my delivery stitches smell rotten (suggested wording for team adaptation; not from source)",
        "official_classification": "Puerperal sepsis / Endometritis",
        "triage_level": "Emergency",
        "recommended_action": "Immediate medical attention for IV broad-spectrum antibiotics and sepsis evaluation.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 15, p. 55-58",
        "clinical_review_status": "pending clinical review",
        "notes": "Sepsis can progress to septic shock within hours."
    },
    # 10. Thoughts of Self-Harm or Harming Baby
    {
        "rule_id": "RUL-EMG-010",
        "population": "postpartum, pregnant",
        "stage_or_age": "Pregnancy or postpartum (up to 12 months)",
        "danger_sign": "Thoughts of self-harm, suicide, or hurting the baby",
        "plain_description": "Desire or thoughts to end one's life, feelings of despair, hallucinations, or urge to harm the baby.",
        "example_user_phrasings_en": "I want to kill myself; I feel like ending it all; I have thoughts of hurting my baby; I cannot cope and want to die (suggested wording for team adaptation; not from source)",
        "official_classification": "Psychiatric emergency / Severe postpartum depression / Psychosis",
        "triage_level": "Emergency",
        "recommended_action": "Immediate crisis intervention. Ensure woman and baby are not left alone; escort to nearest hospital or mental health specialist immediately.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 25, p. 79-81",
        "clinical_review_status": "pending clinical review",
        "notes": "Zero delay in emergency mental health referral."
    },
    # 11. Premature Rupture of Membranes with Foul or Green Fluid
    {
        "rule_id": "RUL-EMG-011",
        "population": "pregnant",
        "stage_or_age": "Before 37 weeks or any stage with abnormal colour/odour",
        "danger_sign": "Waters breaking with foul smell or greenish/brown meconium stain",
        "plain_description": "Gush or trickle of fluid from vagina that smells offensive or is greenish-brown in colour.",
        "example_user_phrasings_en": "My water broke and it looks green and dirty; smelly water coming out of my vagina; water broke way before my delivery date (suggested wording for team adaptation; not from source)",
        "official_classification": "Chorioamnionitis / Meconium aspiration risk / Preterm PROM",
        "triage_level": "Emergency",
        "recommended_action": "Immediate hospital transfer. Do not insert fingers or tampons; pad dry and present to labor ward.",
        "source_id": "SRC-WHO-IMPAC-2017",
        "source_page_or_section": "Section S-133",
        "clinical_review_status": "pending clinical review",
        "notes": "Green fluid indicates fetal distress (meconium passage)."
    },
    # 12. Cord Prolapse
    {
        "rule_id": "RUL-EMG-012",
        "population": "pregnant",
        "stage_or_age": "Labour or after water breaking",
        "danger_sign": "Umbilical cord protruding from vagina",
        "plain_description": "Feeling or seeing a loop of the umbilical cord hanging or slipping out of the vagina.",
        "example_user_phrasings_en": "The baby cord is hanging out of my vagina; I feel the cord inside my private part after water broke (suggested wording for team adaptation; not from source)",
        "official_classification": "Cord prolapse",
        "triage_level": "Emergency",
        "recommended_action": "Extreme surgical emergency. Call for an ambulance immediately. Mother should assume knee-chest position or elevate hips. Do not push cord back inside. Urgent hospital delivery.",
        "source_id": "SRC-FMOH-LSS-2019",
        "source_page_or_section": "Module 6, Obstetric Emergencies, p. 58-60",
        "clinical_review_status": "pending clinical review",
        "notes": "Cord compression can cut off baby's oxygen within minutes."
    },
    # 13. Prolonged or Obstructed Labour
    {
        "rule_id": "RUL-EMG-013",
        "population": "pregnant",
        "stage_or_age": "Labour / Childbirth",
        "danger_sign": "Labour lasting over 12-24 hours without progress / severe maternal exhaustion",
        "plain_description": "Active strong labour contractions continuing for excessive hours without delivery of baby.",
        "example_user_phrasings_en": "I have been in active labour for two days; labour pains won't stop and baby is not coming out; she has been pushing for hours and is exhausted (suggested wording for team adaptation; not from source)",
        "official_classification": "Obstructed labour / Prolonged second stage",
        "triage_level": "Emergency",
        "recommended_action": "Immediate transfer to comprehensive emergency obstetric facility with surgical theatre capabilities for assisted delivery or Caesarean section.",
        "source_id": "SRC-WHO-IMPAC-2017",
        "source_page_or_section": "Section S-73",
        "clinical_review_status": "pending clinical review",
        "notes": "Leads to uterine rupture and obstetric fistula if untreated."
    },
    # 14. Newborn Not Feeding / Unable to Suckle
    {
        "rule_id": "RUL-EMG-014",
        "population": "newborn, infant",
        "stage_or_age": "First 28 days of life",
        "danger_sign": "Inability to suckle, latch, or feed at all",
        "plain_description": "Newborn refuses or is completely unable to attach to the breast or swallow milk.",
        "example_user_phrasings_en": "My newborn baby cannot suck breast at all; baby is not sucking and spits everything out; baby is too weak to feed (suggested wording for team adaptation; not from source)",
        "official_classification": "Possible serious bacterial infection (pSBI) / Severe neonatal illness",
        "triage_level": "Emergency",
        "recommended_action": "Immediate hospital evaluation for underlying severe systemic infection, hypothermia, or hypoglycemia.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 40, p. 120-124",
        "clinical_review_status": "pending clinical review",
        "notes": "Early cardinal sign of neonatal sepsis."
    },
    # 15. Newborn Convulsions / Abnormal Spasms
    {
        "rule_id": "RUL-EMG-015",
        "population": "newborn",
        "stage_or_age": "First 28 days of life",
        "danger_sign": "Newborn convulsions, twitching, or stiff body spasms",
        "plain_description": "Rhythmic jerking of arms/legs, abnormal bicycling movements, eye rolling, or body arching stiffly.",
        "example_user_phrasings_en": "My newborn baby is jerking and twitching; baby is having convulsions; baby's body is stiff and eyes rolling back (suggested wording for team adaptation; not from source)",
        "official_classification": "Neonatal seizures / Neonatal tetanus / Encephalopathy",
        "triage_level": "Emergency",
        "recommended_action": "Immediate hospital admission for airway management, anticonvulsant therapy, and infection workup.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 40, p. 120-124",
        "clinical_review_status": "pending clinical review",
        "notes": "Medical emergency with high risk of mortality or neurological injury."
    },
    # 16. Newborn Fast Breathing / Chest Indrawing
    {
        "rule_id": "RUL-EMG-016",
        "population": "newborn, infant",
        "stage_or_age": "First 28 days of life",
        "danger_sign": "Severe respiratory distress / Fast breathing (>=60 bpm) / Severe chest indrawing",
        "plain_description": "Breathing very rapidly, skin sucking in deeply between ribs or below ribcage, with grunting sounds.",
        "example_user_phrasings_en": "My baby is breathing very fast and chest sinking in; newborn breathing hard with grunting noise; baby is panting fast and ribs pulling in (suggested wording for team adaptation; not from source)",
        "official_classification": "Severe respiratory distress / Neonatal pneumonia",
        "triage_level": "Emergency",
        "recommended_action": "Emergency hospital presentation. Keep infant warm; urgent oxygen and antibiotic therapy required.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 40, p. 120-124",
        "clinical_review_status": "pending clinical review",
        "notes": "Rapid deterioration can occur in neonates with respiratory distress."
    },
    # 17. Newborn Abnormal Temperature (Hypothermia / Severe Fever)
    {
        "rule_id": "RUL-EMG-017",
        "population": "newborn",
        "stage_or_age": "First 28 days of life",
        "danger_sign": "Severe hypothermia (<36.5C) or high fever (>37.5C)",
        "plain_description": "Baby feels unusually burning hot or unusually cold to the touch, cold hands and feet with poor colour.",
        "example_user_phrasings_en": "My baby is ice cold and not warming up; newborn baby is burning with high fever; baby temperature is very low and shivering (suggested wording for team adaptation; not from source)",
        "official_classification": "Thermal instability / Severe infection / Neonatal hypothermia",
        "triage_level": "Emergency",
        "recommended_action": "Immediate medical assessment. If hypothermic, practice immediate skin-to-skin warming en route to facility.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 40, p. 120-124",
        "clinical_review_status": "pending clinical review",
        "notes": "Hypothermia can rapidly kill a newborn even in warm climates."
    },
    # 18. Newborn Lethargy / Unresponsiveness
    {
        "rule_id": "RUL-EMG-018",
        "population": "newborn, infant",
        "stage_or_age": "First 28 days of life",
        "danger_sign": "Extreme lethargy, floppiness, or unresponsiveness",
        "plain_description": "Baby is difficult to wake, does not respond to touch or crying stimuli, body feels like a limp rag doll.",
        "example_user_phrasings_en": "My baby is completely floppy and will not wake up; newborn is unconscious and limp; baby barely moves or cries when pinched (suggested wording for team adaptation; not from source)",
        "official_classification": "Altered level of consciousness / Critical neonatal collapse",
        "triage_level": "Emergency",
        "recommended_action": "Extreme emergency resuscitation and urgent hospital transport.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 40, p. 120-124",
        "clinical_review_status": "pending clinical review",
        "notes": "Critical indicator of late-stage sepsis or severe metabolic crisis."
    },
    # 19. Severe Newborn Jaundice
    {
        "rule_id": "RUL-EMG-019",
        "population": "newborn",
        "stage_or_age": "First 14 days of life",
        "danger_sign": "Severe jaundice (yellow skin extending to palms and soles, or appearing on Day 1)",
        "plain_description": "Intense yellow colour of eyes, face, abdomen, palms, and feet, especially if accompanied by floppiness or high-pitched cry.",
        "example_user_phrasings_en": "Baby's whole body and palms are deep yellow; baby eyes and feet turned yellow on first day of birth; newborn yellow skin and very weak (suggested wording for team adaptation; not from source)",
        "official_classification": "Severe hyperbilirubinemia / Impending kernicterus",
        "triage_level": "Emergency",
        "recommended_action": "Immediate hospital evaluation for phototherapy or exchange blood transfusion to prevent permanent brain damage.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 42, p. 126-128",
        "clinical_review_status": "pending clinical review",
        "notes": "Sunlight exposure is not adequate for severe pathological jaundice."
    },
    # 20. Severe Newborn Cord Infection (Omphalitis)
    {
        "rule_id": "RUL-EMG-020",
        "population": "newborn",
        "stage_or_age": "First 28 days of life",
        "danger_sign": "Red, swollen cord stump discharging pus or foul odour spreading to abdominal skin",
        "plain_description": "Redness, swelling, and pus around the belly button stump extending onto the baby's surrounding stomach skin.",
        "example_user_phrasings_en": "My baby's navel is swollen red, smells bad, and draining pus; yellow pus coming out of umbilical cord and belly is red; cord is infected and red circle spreading (suggested wording for team adaptation; not from source)",
        "official_classification": "Omphalitis / Severe localized or systemic cord infection",
        "triage_level": "Emergency",
        "recommended_action": "Urgent medical treatment with parenteral antibiotics to prevent rapid systemic bacteremia and peritonitis.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 37 & 40, p. 110-124",
        "clinical_review_status": "pending clinical review",
        "notes": "Dangerous infection route directly into portal venous system."
    },
    # 21. Priority Rule: Persistent Vomiting with Dehydration (Hyperemesis)
    {
        "rule_id": "RUL-PRI-001",
        "population": "pregnant",
        "stage_or_age": "First and second trimester",
        "danger_sign": "Severe continuous vomiting and inability to keep fluids down >24h",
        "plain_description": "Vomiting everything consumed for over 24 hours with dark concentrated urine, extreme thirst, and dizziness.",
        "example_user_phrasings_en": "I have been vomiting non stop for two days cannot keep water down; I am so dizzy and vomiting everything I drink; dark urine and constant vomiting (suggested wording for team adaptation; not from source)",
        "official_classification": "Hyperemesis gravidarum with dehydration",
        "triage_level": "Priority",
        "recommended_action": "Prompt clinic/hospital attendance for IV rehydration, electrolyte balance, and antiemetic therapy.",
        "source_id": "SRC-WHO-ANC-2016",
        "source_page_or_section": "Recommendation C.1, p. 55",
        "clinical_review_status": "pending clinical review",
        "notes": "Needs same-day clinical assessment to avoid acute kidney injury."
    },
    # 22. Priority Rule: Painful Urination with Fever (UTI / Pyelonephritis)
    {
        "rule_id": "RUL-PRI-002",
        "population": "pregnant, postpartum",
        "stage_or_age": "Pregnancy or postpartum",
        "danger_sign": "Painful burning urination with flank pain or fever",
        "plain_description": "Severe stinging or pain when passing urine, frequent urge with little output, accompanied by backache or mild fever.",
        "example_user_phrasings_en": "It burns terribly when I pee and my lower back hurts; hot pain when urinating and cloudy urine; peeing pain with fever in pregnancy (suggested wording for team adaptation; not from source)",
        "official_classification": "Urinary tract infection / Suspected acute pyelonephritis",
        "triage_level": "Priority",
        "recommended_action": "Visit primary health centre within 24 hours for urine microscopy, culture, and pregnancy-safe antibiotics.",
        "source_id": "SRC-FMOH-ANC-2020",
        "source_page_or_section": "Section 3.2 & 7.1, p. 20-22",
        "clinical_review_status": "pending clinical review",
        "notes": "Untreated UTIs in pregnancy frequently trigger preterm labour."
    },
    # 23. Priority Rule: Painful, Red, Swollen Breast with Fever (Mastitis)
    {
        "rule_id": "RUL-PRI-003",
        "population": "postpartum",
        "stage_or_age": "Postpartum / Lactating",
        "danger_sign": "Tender, hard, hot, red breast wedge accompanied by flu-like fever",
        "plain_description": "One part of breast is red, swollen, hot to touch, very painful, accompanied by fever and body aches.",
        "example_user_phrasings_en": "My right breast is swollen red hot and very painful; fever and hard red lump in breast while breastfeeding; breast is engorged and burning with chills (suggested wording for team adaptation; not from source)",
        "official_classification": "Infectious mastitis / Impending breast abscess",
        "triage_level": "Priority",
        "recommended_action": "Same-day clinic evaluation for antibiotic therapy, continue gentle frequent breast drainage, warm compress.",
        "source_id": "SRC-WHO-PNC-2022",
        "source_page_or_section": "Recommendation 34, p. 102-105",
        "clinical_review_status": "pending clinical review",
        "notes": "Prompt treatment prevents surgical abscess formation."
    },
    # 24. Priority Rule: Mild or Dependent Leg Swelling (Non-Systemic)
    {
        "rule_id": "RUL-ROU-001",
        "population": "pregnant",
        "stage_or_age": "Third trimester",
        "danger_sign": "Mild bilateral ankle swelling without headache or facial puffiness",
        "plain_description": "Gradual swelling in ankles at the end of the day that improves when resting with legs up, with normal vision and no head pain.",
        "example_user_phrasings_en": "My feet are slightly swollen after standing; ankle swelling in late pregnancy; my feet swell in the evening but my face is fine (suggested wording for team adaptation; not from source)",
        "official_classification": "Physiological dependent oedema of pregnancy",
        "triage_level": "Routine",
        "recommended_action": "Rest with feet elevated, maintain hydration, monitor for danger signs, and mention at next routine antenatal visit for blood pressure check.",
        "source_id": "SRC-WHO-ANC-2016",
        "source_page_or_section": "Recommendation C.4, p. 62",
        "clinical_review_status": "pending clinical review",
        "notes": "Must be distinguished from preeclampsia with sudden facial/hand edema."
    }
]

print(f"Total emergency rules: {len(rules)}")

# Write CSV
csv_path = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/03_Emergency_Rules/emergency_rules.csv")
fieldnames = list(rules[0].keys())
with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rules)

# Write JSON
json_path = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/03_Emergency_Rules/emergency_rules.json")
with open(json_path, mode="w", encoding="utf-8") as f:
    json.dump(rules, f, indent=2, ensure_ascii=False)

# Traceability CSV
traceability = []
for r in rules:
    traceability.append({
        "rule_id": r["rule_id"],
        "source_id": r["source_id"],
        "source_page_or_section": r["source_page_or_section"],
        "danger_sign": r["danger_sign"],
        "recommendation_paraphrase": r["recommended_action"]
    })

trace_csv_path = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/03_Emergency_Rules/rule_traceability.csv")
with open(trace_csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(traceability[0].keys()))
    writer.writeheader()
    writer.writerows(traceability)

# Emergency Contacts CSV (public release retains only confirmed national 112 routing)
contacts = [
    {
        "contact_id": "CNT-NAT-112",
        "organization": "National Emergency Communications Centre (NCC)",
        "jurisdiction": "National / Nigeria Toll-Free",
        "phone_number": "112",
        "service_scope": "Toll-free 24/7 central emergency routing for police, ambulance, and medical emergency rescue services nationwide.",
        "official_source": "Nigerian Communications Commission / National Emergency Medical Service and Ambulance System (NEMSAS)",
        "verification_status": "officially_confirmed_routing_number"
    }
]

contacts_csv_path = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/03_Emergency_Rules/emergency_contacts.csv")
with open(contacts_csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(contacts[0].keys()))
    writer.writeheader()
    writer.writerows(contacts)

print("Emergency rules, traceability, and contacts written successfully.")

