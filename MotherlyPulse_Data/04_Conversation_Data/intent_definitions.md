# MotherlyPulse Intent Definitions & Boundary Guidelines

**Project:** MotherlyPulse Maternal Health Assistant  
**Classification System:** 5 Intent Classes & 3 Provisional Triage Levels  
**Scope:** Two-Week Initial Architecture  

---

## 1. Intent Definitions & Routing Logic

### 1. `CRITICAL_EMERGENCY_RED_FLAG`
* **Definition:** Any message describing an acute, life-threatening obstetric, postpartum, or neonatal danger sign that requires immediate clinical care.
* **Triage Level:** `Emergency`
* **Execution Pathway:** Rule-based override. Never routed to LLM generation.
* **Key Symptoms Included:** Vaginal bleeding in pregnancy or severe bleeding postpartum, convulsions, severe headache with blurred vision, reduced or absent fetal movements, difficulty breathing, severe abdominal pain, thoughts of self-harm, cord prolapse, or newborn danger signs (inability to suckle, seizures, severe chest indrawing, severe jaundice).
* **Expected System Response:** Fixed urgent-care referral message with emergency contact numbers.

### 2. `Non_Emergency_Symptom`
* **Definition:** Common, physiological, mild, or moderate pregnancy or postpartum symptoms that are uncomfortable but not acutely life-threatening, or symptoms requiring prompt scheduled primary care evaluation rather than emergency ambulance dispatch.
* **Triage Level:** `Routine` (for mild physiological symptoms) or `Priority` (for symptoms needing same-day clinic visits like suspected UTI or mild mastitis).
* **Execution Pathway:** Grounded passage lookup + Gemma-2-2B model response.
* **Key Symptoms Included:** Mild morning sickness / nausea, heartburn, constipation, mild evening foot swelling, mild backache, or routine breast fullness.
* **Expected System Response:** Kind, reassuring 2–4 sentence reply based directly on verified passages, offering non-pharmacological comfort tips and advising the user to mention it at their next antenatal checkup.

### 3. `Medication_Query`
* **Definition:** Inquiries specifically requesting drug names, dosages, prescriptions, self-medication advice, home concoctions (agbo), or requests to validate unprescribed medicines.
* **Triage Level:** `Routine`
* **Execution Pathway:** Fixed decline response or strict grounded safety passage.
* **Boundary Principle:** The assistant never provides a dosage, prescribes a drug, or diagnoses an illness.
* **Expected System Response:** Fixed decline: *"I cannot prescribe medicines, recommend doses, or diagnose conditions. Please speak with your doctor, midwife, or pharmacist before taking any medication."*

### 4. `General_Maternal_Edu`
* **Definition:** Informational questions regarding pregnancy stages, recommended antenatal schedules, balanced local nutrition, labour preparation, exclusive breastfeeding, baby hygiene, or postpartum family planning.
* **Triage Level:** `Routine`
* **Execution Pathway:** Grounded passage lookup + Gemma-2-2B model response.
* **Expected System Response:** Simple, supportive, 2–4 sentence informational response grounded entirely within checked health passages.

### 5. `Routine_Reminder_Ack`
* **Definition:** User responses confirming, rescheduling, or acknowledging automated clinic appointment reminders or user-entered medication prompts.
* **Triage Level:** `Routine`
* **Execution Pathway:** Bot workflow handler / Confirmation state machine.
* **Expected System Response:** Polite acknowledgement (e.g., *"Noted! Your reminder has been set/confirmed. We wish you a safe and healthy day."*).

---

## 2. Disambiguation Rules: Telling Similar Intents Apart

### Rule A: `Non_Emergency_Symptom` vs. `CRITICAL_EMERGENCY_RED_FLAG`
* **The Threshold Test:** Does the symptom represent potential organ dysfunction, severe haemorrhage, imminent eclampsia, fetal distress, or neonatal collapse?
  * *Example 1:* "My feet are slightly puffy in the evening after walking." -> **Non_Emergency_Symptom** (Physiological leg swelling).
  * *Example 2:* "My face and hands are swollen, and my head hurts badly." -> **CRITICAL_EMERGENCY_RED_FLAG** (Preeclampsia warning).
  * *Example 3:* "I threw up this morning after waking up." -> **Non_Emergency_Symptom** (Morning sickness).
  * *Example 4:* "I have been vomiting non-stop for two days and cannot keep water down." -> **CRITICAL_EMERGENCY_RED_FLAG** / `Priority` (Hyperemesis with dehydration risk).
* **Golden Decision:** When uncertain, or if a user describes an ambiguous overlap, the classifier **MUST** escalate to `CRITICAL_EMERGENCY_RED_FLAG`. False alarms are clinically harmless; delayed emergencies can be fatal.

### Rule B: `Medication_Query` vs. `General_Maternal_Edu`
* *General Maternal Edu:* "Why does the clinic give folic acid?" -> Educational inquiry regarding the purpose of routine vitamins. Can be answered using passage `PAS-NUT-001`.
* *Medication Query:* "How many milligrams of paracetamol can I swallow for my toothache?" -> Explicit dose/drug request. Must trigger the decline reply.

---

## 3. Labeling and Tone Requirements
* All constructed training pairs and test examples must be labelled with one of the five intents.
* All generated model replies must maintain a tone that is **simple, kind, and careful**.
* No reply may exceed 4 sentences.
* Replies must never promise clinical cure or offer definitive diagnostic statements.

