import pathlib
import csv
import json

pairs = [
    # --- 8 TEST PAIRS (6 routine questions, 1 decline, 1 informal) ---
    {
        "pair_id": "PAIR-TST-001",
        "intended_split": "test",
        "user_message": "How many antenatal clinic visits do I really need during my pregnancy?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Official health guidelines recommend having at least eight scheduled antenatal visits with a qualified healthcare worker. Your first visit should ideally happen in the first three months of pregnancy. Regular visits help your doctor or midwife monitor your health and ensure your baby is growing well.",
        "passage_id": "PAS-ANC-001",
        "notes": "Test pair: Routine ANC visit schedule question."
    },
    {
        "pair_id": "PAIR-TST-002",
        "intended_split": "test",
        "user_message": "Why do I need to take folic acid and iron tablets every day?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Folic acid helps protect your unborn baby against serious birth defects of the brain and spine, while iron keeps your blood strong and prevents anaemia. Taking these routine supplements daily helps your baby develop properly and supports your body throughout pregnancy. For the best absorption, take them with clean water or fresh fruit juice.",
        "passage_id": "PAS-NUT-001",
        "notes": "Test pair: Routine supplement inquiry."
    },
    {
        "pair_id": "PAIR-TST-003",
        "intended_split": "test",
        "user_message": "Can I give my newborn baby a little warm water to drink when the weather is very hot?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "No, your baby does not need any water. Breast milk is over eighty percent water and satisfies all your baby's thirst and hunger, even during hot days. Giving water or other liquids can introduce dangerous germs that cause serious diarrhoea and sickness.",
        "passage_id": "PAS-BRS-002",
        "notes": "Test pair: Exclusive breastfeeding standard question."
    },
    {
        "pair_id": "PAIR-TST-004",
        "intended_split": "test",
        "user_message": "What should I pack or prepare before my delivery date arrives?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Preparing ahead of time ensures a safe and calm delivery. Choose a registered health facility with qualified midwives, save money for delivery expenses, and arrange emergency transport that is ready day or night. It is also important to pack clean baby clothes, maternity pads, and pick a trusted companion to support you.",
        "passage_id": "PAS-LAB-001",
        "notes": "Test pair: Routine birth preparedness plan."
    },
    {
        "pair_id": "PAIR-TST-005",
        "intended_split": "test",
        "user_message": "I am feeling mild nausea in the morning. How can I manage it without drugs?",
        "intent": "Non_Emergency_Symptom",
        "triage_level": "Routine",
        "reply": "Morning sickness is very common in early pregnancy due to shifting hormones. You can ease nausea by eating small, frequent meals and keeping dry biscuits or plain crackers nearby to nibble before getting out of bed. Sipping cool water or ginger tea also helps settle your stomach.",
        "passage_id": "PAS-SYM-001",
        "notes": "Test pair: Non-emergency mild symptom management."
    },
    {
        "pair_id": "PAIR-TST-006",
        "intended_split": "test",
        "user_message": "How many checkups should a mother and baby have after birth?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Health guidelines recommend at least four postnatal visits for both mother and newborn. These should take place within the first 24 hours, on day 3, between days 7 and 14, and at 6 weeks after delivery. These visits allow health workers to monitor healing, check your baby's growth, and support your recovery.",
        "passage_id": "PAS-PST-001",
        "notes": "Test pair: Routine postnatal care schedule."
    },
    {
        "pair_id": "PAIR-TST-007",
        "intended_split": "test",
        "user_message": "What dosage of ampicillin should I take for pelvic pain while pregnant?",
        "intent": "Medication_Query",
        "triage_level": "Routine",
        "reply": "I cannot prescribe antibiotics or recommend medication doses. Taking unprescribed medicines during pregnancy can be dangerous for you and your baby. Please visit your healthcare provider or clinic so they can examine you and provide the correct safe treatment.",
        "passage_id": "PAS-MED-001",
        "notes": "Test pair: Decline case for medication query."
    },
    {
        "pair_id": "PAIR-TST-008",
        "intended_split": "test",
        "user_message": "my body just dey do me somehow for evening my leg dey swell small wetin i fit do",
        "intent": "Non_Emergency_Symptom",
        "triage_level": "Routine",
        "reply": "Mild swelling in your feet and ankles in the evening is common during late pregnancy. Resting with your feet raised on pillows and drinking plenty of water can help reduce the puffiness. If you notice sudden swelling in your face or hands with a bad headache, see a health worker immediately.",
        "passage_id": "PAS-SYM-003",
        "notes": "Test pair: Informal low-literacy / Pidgin style query."
    },

    # --- 32 TRAINING PAIRS ---
    # Decline cases (3 more to reach 4 total decline cases)
    {
        "pair_id": "PAIR-TRN-001",
        "intended_split": "train",
        "user_message": "Can I drink herbal agbo to make my labour faster and clean my womb?",
        "intent": "Medication_Query",
        "triage_level": "Routine",
        "reply": "Please avoid drinking herbal concoctions or agbo during pregnancy. Traditional herbal mixtures have unmeasured strengths and can cause harmful womb spasms, heavy bleeding, or damage your baby's organs. Always rely on safe, qualified medical care provided at your maternity clinic.",
        "passage_id": "PAS-MED-003",
        "notes": "Train pair: Decline case (herbal remedies)."
    },
    {
        "pair_id": "PAIR-TRN-002",
        "intended_split": "train",
        "user_message": "Can you tell me what disease is causing my vaginal itching and prescribe ointment?",
        "intent": "Medication_Query",
        "triage_level": "Routine",
        "reply": "I cannot diagnose medical conditions or prescribe medicated creams. Itching can arise from several causes that require an examination by a midwife or doctor. Please visit your primary health centre so a health worker can evaluate you safely.",
        "passage_id": "PAS-MED-001",
        "notes": "Train pair: Decline case (diagnosis and prescription request)."
    },
    {
        "pair_id": "PAIR-TRN-003",
        "intended_split": "train",
        "user_message": "I have headache, can I take ibuprofen tablets?",
        "intent": "Medication_Query",
        "triage_level": "Routine",
        "reply": "You should not take ibuprofen during pregnancy unless specifically directed by a medical doctor, as it can cause complications for your unborn baby. If your headache is mild, try resting in a quiet room and staying hydrated. If it is severe, persistent, or paired with blurry vision, seek emergency hospital care right away.",
        "passage_id": "PAS-MED-001",
        "notes": "Train pair: Decline case (contraindicated medication)."
    },

    # Reminder Acknowledgements (4 cases)
    {
        "pair_id": "PAIR-TRN-004",
        "intended_split": "train",
        "user_message": "Yes, I got the reminder. I will go to my antenatal clinic appointment tomorrow morning.",
        "intent": "Routine_Reminder_Ack",
        "triage_level": "Routine",
        "reply": "Thank you for confirming! Attending your antenatal appointment tomorrow is a wonderful step for you and your baby's health. Remember to bring your clinic card and note down any questions you have for the nurse.",
        "passage_id": "PAS-ANC-001",
        "notes": "Train pair: Reminder acknowledgement."
    },
    {
        "pair_id": "PAIR-TRN-005",
        "intended_split": "train",
        "user_message": "Reminder received, just took my iron and folic acid tablet after lunch.",
        "intent": "Routine_Reminder_Ack",
        "triage_level": "Routine",
        "reply": "Well done! Taking your supplements daily keeps your blood strong and supports your baby's growth. Keep up this healthy routine every day.",
        "passage_id": "PAS-NUT-001",
        "notes": "Train pair: Medication reminder acknowledgement."
    },
    {
        "pair_id": "PAIR-TRN-006",
        "intended_split": "train",
        "user_message": "ok i see am i go carry pikin go clinic for immunization next week wednesday",
        "intent": "Routine_Reminder_Ack",
        "triage_level": "Routine",
        "reply": "Noted! Taking your baby for scheduled clinic checkups and immunizations protects them against serious childhood diseases. We will send you another quick prompt the day before your visit.",
        "passage_id": "PAS-PST-001",
        "notes": "Train pair: Reminder acknowledgement (informal phrasing)."
    },
    {
        "pair_id": "PAIR-TRN-007",
        "intended_split": "train",
        "user_message": "Please change my antenatal clinic reminder time from 8 AM to 10 AM.",
        "intent": "Routine_Reminder_Ack",
        "triage_level": "Routine",
        "reply": "Your reminder time has been successfully updated to 10 AM. We will notify you at this new time before your clinic appointment.",
        "passage_id": "PAS-ANC-001",
        "notes": "Train pair: Reminder schedule adjustment acknowledgement."
    },

    # Informal / Low-literacy style messages (3 more to reach 4 total)
    {
        "pair_id": "PAIR-TRN-008",
        "intended_split": "train",
        "user_message": "abeg why belly dey burn me like say fire dey inside my chest after i chop",
        "intent": "Non_Emergency_Symptom",
        "triage_level": "Routine",
        "reply": "That burning feeling in your chest is heartburn, which is very common during pregnancy as the baby pushes against your stomach. Eating smaller food portions more frequently and staying sitting up after meals can give you relief. Try to avoid greasy or heavily peppered soups before bedtime.",
        "passage_id": "PAS-SYM-002",
        "notes": "Train pair: Informal Pidgin query on heartburn."
    },
    {
        "pair_id": "PAIR-TRN-009",
        "intended_split": "train",
        "user_message": "i like to dey chop white chalk calabash nzu every day e dey sweet me well well",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Craving calabash chalk or nzu often happens when your body is low on important nutrients like iron. However, eating chalk is harmful because it can carry poisonous heavy metals and parasites that hurt your baby. Please tell your clinic nurse so they can check your blood levels and give you safe iron supplements.",
        "passage_id": "PAS-NUT-003",
        "notes": "Train pair: Informal query regarding pica / nzu."
    },
    {
        "pair_id": "PAIR-TRN-010",
        "intended_split": "train",
        "user_message": "wetin make pikin navel dey swell and come out small after cord cut",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Keep your baby's cord stump completely clean and dry until it heals and separates naturally. Do not apply hot ash, cow dung, or traditional concoctions, as these cause deadly infections. If the navel becomes red, hot, swollen, or smells bad, have a health worker examine it immediately.",
        "passage_id": "PAS-NEW-001",
        "notes": "Train pair: Informal newborn cord hygiene inquiry."
    },

    # Non-Emergency Symptom Cases (2 more to reach 3 total non-emergency symptom train pairs)
    {
        "pair_id": "PAIR-TRN-011",
        "intended_split": "train",
        "user_message": "I am having very hard stools and difficulty using the toilet since becoming pregnant.",
        "intent": "Non_Emergency_Symptom",
        "triage_level": "Routine",
        "reply": "Constipation is very common during pregnancy because hormones slow down bowel digestion, and iron supplements can also firm your stools. Eating foods rich in fibre like beans, oatmeal, green vegetables, and fruits like pawpaw can help soften your stool. Be sure to drink plenty of water every day and take gentle walks.",
        "passage_id": "PAS-SYM-004",
        "notes": "Train pair: Non-emergency constipation advice."
    },
    {
        "pair_id": "PAIR-TRN-012",
        "intended_split": "train",
        "user_message": "My nipples are feeling very sore and tender when my newborn starts to suckle.",
        "intent": "Non_Emergency_Symptom",
        "triage_level": "Routine",
        "reply": "Sore nipples are usually caused when the baby is not latching deeply onto your breast. Make sure your baby takes a wide mouthful covering most of the dark area around your nipple, with their chin touching your breast. A midwife can guide your positioning to help your nipples heal comfortably.",
        "passage_id": "PAS-BRS-003",
        "notes": "Train pair: Non-emergency latching and sore nipple advice."
    },

    # Emergency Cases (3 cases in train split)
    {
        "pair_id": "PAIR-TRN-013",
        "intended_split": "train",
        "user_message": "I am 7 months pregnant and bleeding heavily from my vagina with bad cramps.",
        "intent": "CRITICAL_EMERGENCY_RED_FLAG",
        "triage_level": "Emergency",
        "reply": "EMERGENCY ALERT: Vaginal bleeding during pregnancy is a critical medical warning sign. Please do not wait at home. Go immediately to the nearest hospital or emergency maternity centre, or call national emergency 112.",
        "passage_id": "PAS-DNG-001",
        "notes": "Train pair: Critical emergency antepartum bleeding escalation."
    },
    {
        "pair_id": "PAIR-TRN-014",
        "intended_split": "train",
        "user_message": "My head is pounding terribly, my vision is blurry with flashes, and my face is swollen.",
        "intent": "CRITICAL_EMERGENCY_RED_FLAG",
        "triage_level": "Emergency",
        "reply": "EMERGENCY ALERT: A severe headache with blurry vision and facial swelling is a serious sign of dangerously high blood pressure (preeclampsia). Seek emergency hospital medical attention immediately to protect you and your baby.",
        "passage_id": "PAS-DNG-002",
        "notes": "Train pair: Critical emergency preeclampsia escalation."
    },
    {
        "pair_id": "PAIR-TRN-015",
        "intended_split": "train",
        "user_message": "My one-week-old baby is burning hot with high fever and refusing to suck breast at all.",
        "intent": "CRITICAL_EMERGENCY_RED_FLAG",
        "triage_level": "Emergency",
        "reply": "EMERGENCY ALERT: A newborn baby who has a high fever and cannot feed is critically ill. Please take your baby to the nearest hospital or pediatric emergency centre right now without delay.",
        "passage_id": "PAS-NEW-002",
        "notes": "Train pair: Critical emergency newborn danger sign escalation."
    },

    # Additional General Maternal Edu / Grounded Educational Pairs (17 more to reach 32 train pairs)
    {
        "pair_id": "PAIR-TRN-016",
        "intended_split": "train",
        "user_message": "What kind of tests will they do during my first clinic visit?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "At your first antenatal visit, health workers routinely check your blood pressure, test your urine for protein or infection, and check your blood levels. They also screen for conditions like HIV, hepatitis, and syphilis, and determine your blood group and genotype. These standard tests protect both you and your developing baby.",
        "passage_id": "PAS-ANC-002",
        "notes": "Train pair: Routine antenatal lab tests."
    },
    {
        "pair_id": "PAIR-TRN-017",
        "intended_split": "train",
        "user_message": "What is the yellow milk that comes out of my breast immediately after delivery?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "That yellow first milk is called colostrum, and it is the best gift you can give your newborn. It contains powerful antibodies and nutrients that protect your baby from dangerous infections. Always feed colostrum to your baby and do not throw it away.",
        "passage_id": "PAS-BRS-001",
        "notes": "Train pair: Breastfeeding colostrum education."
    },
    {
        "pair_id": "PAIR-TRN-018",
        "intended_split": "train",
        "user_message": "How do I know when real labour has started?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "True labour pains feel like regular cramps or tightening in your belly and lower back that get stronger, last longer, and come closer together over time. Walking will not stop them, and you may notice a pink mucus show or your water breaking. When contractions occur every five minutes, head to your maternity facility.",
        "passage_id": "PAS-LAB-002",
        "notes": "Train pair: Labour onset signs."
    },
    {
        "pair_id": "PAIR-TRN-019",
        "intended_split": "train",
        "user_message": "Why is it safer to give birth in a hospital rather than at home?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Delivering in a registered health facility means qualified doctors and midwives are there to assist you safely. They have sterile tools, emergency medicines to stop sudden bleeding, and skills to help your baby breathe if needed. Home births lack this emergency support if unexpected complications occur.",
        "passage_id": "PAS-LAB-003",
        "notes": "Train pair: Skilled birth attendance rationale."
    },
    {
        "pair_id": "PAIR-TRN-020",
        "intended_split": "train",
        "user_message": "I gave birth two weeks ago and I am bleeding heavily and soaking my pads very quickly. Is that normal?",
        "intent": "CRITICAL_EMERGENCY_RED_FLAG",
        "triage_level": "Emergency",
        "reply": "EMERGENCY ALERT: Soaking through pads quickly or passing large blood clots after delivery is a medical emergency known as postpartum haemorrhage. Please go to the nearest emergency health facility right away for urgent care.",
        "passage_id": "PAS-PST-002",
        "notes": "Train pair: Postpartum haemorrhage warning."
    },
    {
        "pair_id": "PAIR-TRN-021",
        "intended_split": "train",
        "user_message": "I had a c-section 10 days ago and the scar is very red, hot, and oozing yellow liquid.",
        "intent": "CRITICAL_EMERGENCY_RED_FLAG",
        "triage_level": "Emergency",
        "reply": "EMERGENCY ALERT: Redness, heat, pain, and pus draining from a surgical scar indicate a serious wound infection. Go to your hospital or maternity surgical clinic immediately so a doctor can treat the infection safely.",
        "passage_id": "PAS-PST-004",
        "notes": "Train pair: Postpartum surgical wound infection."
    },
    {
        "pair_id": "PAIR-TRN-022",
        "intended_split": "train",
        "user_message": "Ever since I gave birth a month ago, I feel constantly sad, crying, and I cannot sleep.",
        "intent": "General_Maternal_Edu",
        "triage_level": "Priority",
        "reply": "Feeling persistent deep sadness, hopelessness, or severe exhaustion beyond two weeks after birth can be signs of postpartum depression. This is a common medical condition, not your fault or a sign of weakness. Please speak openly with your clinic doctor or midwife so they can offer kind, professional support.",
        "passage_id": "PAS-MEN-001",
        "notes": "Train pair: Postpartum depression guidance."
    },
    {
        "pair_id": "PAIR-TRN-023",
        "intended_split": "train",
        "user_message": "Why do pregnant women receive malaria prevention medicine during clinic visits?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Malaria during pregnancy can cause severe blood loss, miscarriage, or low birth weight in newborn babies. Taking preventive malaria medicine (IPTp) directly from your clinic health worker from the fourth month onwards protects you and your growing baby. Always remember to sleep under an insecticide-treated net every night.",
        "passage_id": "PAS-ANC-003",
        "notes": "Train pair: Malaria prevention (IPTp) in pregnancy."
    },
    {
        "pair_id": "PAIR-TRN-024",
        "intended_split": "train",
        "user_message": "What nutritious Nigerian foods should I eat to keep my baby healthy?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "You can get complete nutrition from affordable local foods. Include proteins like beans, eggs, fish, and groundnuts; energy foods such as sweet potatoes, yam, and plantain; and leafy green vegetables like ugwu and spinach with fresh fruits. Remember to drink plenty of clean drinking water every day.",
        "passage_id": "PAS-NUT-002",
        "notes": "Train pair: Maternal nutrition with Nigerian staples."
    },
    {
        "pair_id": "PAIR-TRN-025",
        "intended_split": "train",
        "user_message": "What should I apply to my newborn baby's umbilical cord stump?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Health workers recommend keeping the umbilical cord stump clean and dry, or applying chlorhexidine gel as instructed at your delivery facility. Never apply dung, ashes, charcoal, or unprescribed oils, as these introduce deadly germs into the baby's body. Let the cord fall off naturally on its own.",
        "passage_id": "PAS-NEW-001",
        "notes": "Train pair: Cord care instructions."
    },
    {
        "pair_id": "PAIR-TRN-026",
        "intended_split": "train",
        "user_message": "Why does the baby need to wait two years before another pregnancy?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Waiting at least two years between giving birth and getting pregnant again gives your body time to heal and rebuild its blood and nutrient stores. It also allows you to give your baby dedicated care, affection, and breast milk. You can discuss modern family planning options with your clinic nurse at your six-week visit.",
        "passage_id": "PAS-FMP-001",
        "notes": "Train pair: Healthy pregnancy spacing."
    },
    {
        "pair_id": "PAIR-TRN-027",
        "intended_split": "train",
        "user_message": "Can exclusive breastfeeding stop me from getting pregnant right away?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Exclusive breastfeeding can naturally delay pregnancy only if your monthly period has not returned, your baby is under six months old, and you breastfeed exclusively day and night. If any of these conditions changes, you can become pregnant again. Talk to your clinic nurse about modern family planning for added peace of mind.",
        "passage_id": "PAS-FMP-002",
        "notes": "Train pair: Lactational amenorrhea method."
    },
    {
        "pair_id": "PAIR-TRN-028",
        "intended_split": "train",
        "user_message": "What should I do if my iron tablets make my stool dark or upset my stomach?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Dark stools are a harmless and normal side effect of taking iron tablets. To reduce stomach upset, try taking your iron tablet with meals or just before sleeping, accompanied by a glass of water or fresh orange juice. Never stop taking your prescribed supplements without talking to your clinic nurse first.",
        "passage_id": "PAS-MED-002",
        "notes": "Train pair: Routine supplement adherence & side effects."
    },
    {
        "pair_id": "PAIR-TRN-029",
        "intended_split": "train",
        "user_message": "I am 8 months pregnant and my baby has not moved at all since morning.",
        "intent": "CRITICAL_EMERGENCY_RED_FLAG",
        "triage_level": "Emergency",
        "reply": "EMERGENCY ALERT: A sudden reduction or complete stop in your baby's movements is a serious warning sign of fetal distress. Please go to your maternity hospital immediately so health workers can check your baby's heartbeat.",
        "passage_id": "PAS-DNG-003",
        "notes": "Train pair: Decreased fetal movement emergency."
    },
    {
        "pair_id": "PAIR-TRN-030",
        "intended_split": "train",
        "user_message": "My baby was born 3 days ago and the whites of his eyes and body look yellow.",
        "intent": "CRITICAL_EMERGENCY_RED_FLAG",
        "triage_level": "Emergency",
        "reply": "EMERGENCY ALERT: Yellow eyes and yellow skin in a newborn can be a sign of severe neonatal jaundice. Severe jaundice requires urgent medical treatment under hospital phototherapy lamps to protect your baby's brain. Take your baby to a health facility right away.",
        "passage_id": "PAS-NEW-003",
        "notes": "Train pair: Newborn jaundice emergency."
    },
    {
        "pair_id": "PAIR-TRN-031",
        "intended_split": "train",
        "user_message": "Clear water started leaking from my private part but I am not due for another month and have no pain.",
        "intent": "CRITICAL_EMERGENCY_RED_FLAG",
        "triage_level": "Emergency",
        "reply": "EMERGENCY ALERT: Leaking or gushing water before your due date means your membranes have ruptured early. This exposes your baby to serious infection risks even if you feel no pain. Put on a clean pad and go directly to your maternity hospital.",
        "passage_id": "PAS-DNG-004",
        "notes": "Train pair: Premature rupture of membranes emergency."
    },
    {
        "pair_id": "PAIR-TRN-032",
        "intended_split": "train",
        "user_message": "Why do they give tetanus injection to pregnant women?",
        "intent": "General_Maternal_Edu",
        "triage_level": "Routine",
        "reply": "Tetanus injections protect both you and your newborn baby against tetanus, a life-threatening infection. The vaccine builds strong immunity in your body that passes to your baby, keeping them safe during and after delivery. Make sure your tetanus immunization card is kept up to date at your clinic visits.",
        "passage_id": "PAS-ANC-004",
        "notes": "Train pair: Maternal tetanus immunization."
    }
]

print(f"Total conversation pairs: {len(pairs)}")
test_count = sum(1 for p in pairs if p["intended_split"] == "test")
train_count = sum(1 for p in pairs if p["intended_split"] == "train")
print(f"Split counts: Train={train_count}, Test={test_count}")

# Write JSONL
jsonl_path = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/04_Conversation_Data/english_pairs.jsonl")
with open(jsonl_path, mode="w", encoding="utf-8") as f:
    for p in pairs:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

# Write CSV
csv_path = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/04_Conversation_Data/english_pairs.csv")
fieldnames = list(pairs[0].keys())
with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(pairs)

# Adaptation template CSV
adaptation_rows = []
for p in pairs:
    adaptation_rows.append({
        "pair_id": p["pair_id"],
        "intended_split": p["intended_split"],
        "user_message_en": p["user_message"],
        "reply_en": p["reply"],
        "user_message_yo": "",
        "reply_yo": "",
        "user_message_ha": "",
        "reply_ha": "",
        "user_message_ig": "",
        "reply_ig": "",
        "user_message_pcm": "",
        "reply_pcm": "",
        "reviewer_name": "",
        "review_status": "pending_adaptation"
    })

adapt_csv_path = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data/04_Conversation_Data/adaptation_template.csv")
with open(adapt_csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(adaptation_rows[0].keys()))
    writer.writeheader()
    writer.writerows(adaptation_rows)

print("Conversation pairs and adaptation template written successfully.")

