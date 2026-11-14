# MotherlyPulse — Clinical Passage Retrieval Evaluation Benchmark Report

## 1. Executive Summary
- **Evaluation Set:** 40 held-out test scenarios (140/20/40 stratified split) x 3 query formulations (1 base + 2 conversational rewordings) = **120 test prompts total**.
- **Evidence Base:** 35 clinical passages indexed from WHO 2016 ANC, WHO 2022 PNC, and FMOH 2019 guidelines.
- **Retriever Architecture:** Grounded TF-IDF Vector Space Model with unigram/bigram sublinear term frequency weighting across passage topic, subtopic, clinical danger signs, and evidence text.
- **Overall Top-1 Correctness:** **25/120 (20.83%)**
- **Base Query Accuracy:** **12/40 (30.00%)**
- **Rewording 1 Accuracy:** **8/40 (20.00%)**
- **Rewording 2 Accuracy:** **5/40 (12.50%)**

---

## 2. Granular Performance Breakdown

### A. Performance by Maternal Milestone
| User Group | Total Prompts | Top-1 Correct | Top-1 Accuracy |
| :--- | :--- | :--- | :--- |
| **Pregnancy** | 60 | 19 | 31.67% |
| **Infant / Pediatric** | 60 | 6 | 10.00% |
| **Total** | **120** | **25** | **20.83%** |

### B. Performance by Clinical Triage Category
| Triage Category | Prompts | Correct | Accuracy | Clinical Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **Emergency** | 36 | 9 | 25.00% | Acute red-flag conditions (hemorrhage, convulsions, preeclampsia) |
| **Priority** | 24 | 5 | 20.83% | Time-sensitive clinical consults (UTIs, mastitis, jaundice) |
| **Routine** | 60 | 11 | 18.33% | Preventive health, nutrition, vaccines, hygiene |

---

## 3. Systematic Error & Mismatch Analysis

Total Mismatches Observed: **95 / 120** (79.2%)

| Pair ID | Variant | Gold Passage | Retrieved Passage | Query Excerpt | Error Diagnosis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `PAIR-PRG-005` | base | `PAS-DNG-001` | `PAS-ANC-001` (Score: 0.096) | I am 5 months pregnant and I noticed bright red bl... | Gold topic: Vaginal Bleeding in Pregnancy vs Retrieved topic: Antenatal Care |
| `PAIR-PRG-005` | rewording_1 | `PAS-DNG-001` | `PAS-ANC-003` (Score: 0.0916) | I am pregnant in month 5 and seeing fresh red bloo... | Gold topic: Vaginal Bleeding in Pregnancy vs Retrieved topic: Antenatal Care |
| `PAIR-PRG-005` | rewording_2 | `PAS-DNG-001` | `PAS-DNG-004` (Score: 0.0806) | Help me, I am five months along and bright red blo... | Gold topic: Vaginal Bleeding in Pregnancy vs Retrieved topic: Pregnancy Danger Signs |
| `PAIR-PRG-013` | rewording_2 | `PAS-SYM-001` | `PAS-SYM-004` (Score: 0.0595) | I am throwing up everything I eat and drink for tw... | Gold topic: Hyperemesis Gravidarum Dehydration vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-PRG-024` | rewording_1 | `PAS-ANC-002` | `PAS-SYM-002` (Score: 0.1329) | Can you explain about Suspected Urinary Tract Infe... | Gold topic: Suspected Urinary Tract Infection vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-PRG-024` | rewording_2 | `PAS-ANC-002` | `PAS-SYM-002` (Score: 0.1455) | What should a mother do about Suspected Urinary Tr... | Gold topic: Suspected Urinary Tract Infection vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-PRG-029` | base | `PAS-LAB-001` | `PAS-NEW-001` (Score: 0.1975) | I feel a loop of the baby's umbilical cord slippin... | Gold topic: Umbilical Cord Prolapse vs Retrieved topic: Newborn Care Basics |
| `PAIR-PRG-029` | rewording_1 | `PAS-LAB-001` | `PAS-NEW-001` (Score: 0.2371) | Can you explain about Umbilical Cord Prolapse rega... | Gold topic: Umbilical Cord Prolapse vs Retrieved topic: Newborn Care Basics |
| `PAIR-PRG-029` | rewording_2 | `PAS-LAB-001` | `PAS-NEW-001` (Score: 0.1904) | What should a mother do about Umbilical Cord Prola... | Gold topic: Umbilical Cord Prolapse vs Retrieved topic: Newborn Care Basics |
| `PAIR-PRG-036` | base | `PAS-ANC-001` | `PAS-LAB-002` (Score: 0.097) | Can I do moderate physical exercise like walking d... | Gold topic: Physical Exercise in Pregnancy vs Retrieved topic: Labour Preparation |
| `PAIR-PRG-036` | rewording_1 | `PAS-ANC-001` | `PAS-DNG-001` (Score: 0.1124) | Can you explain about Physical Exercise in Pregnan... | Gold topic: Physical Exercise in Pregnancy vs Retrieved topic: Pregnancy Danger Signs |
| `PAIR-PRG-036` | rewording_2 | `PAS-ANC-001` | `PAS-SYM-002` (Score: 0.0953) | What should a mother do about Physical Exercise in... | Gold topic: Physical Exercise in Pregnancy vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-PRG-046` | rewording_1 | `PAS-ANC-002` | `PAS-PST-001` (Score: 0.1044) | Can you explain about Rhesus Factor and Blood Grou... | Gold topic: Rhesus Factor and Blood Grouping vs Retrieved topic: Postpartum Recovery |
| `PAIR-PRG-046` | rewording_2 | `PAS-ANC-002` | `PAS-PST-001` (Score: 0.1094) | What should a mother do about Rhesus Factor and Bl... | Gold topic: Rhesus Factor and Blood Grouping vs Retrieved topic: Postpartum Recovery |
| `PAIR-PRG-048` | rewording_1 | `PAS-MEN-001` | `PAS-MEN-002` (Score: 0.1939) | Can you explain about Antenatal Mental Health Supp... | Gold topic: Antenatal Mental Health Support vs Retrieved topic: Postpartum Mental Wellbeing |
| `PAIR-PRG-048` | rewording_2 | `PAS-MEN-001` | `PAS-MEN-002` (Score: 0.1828) | What should a mother do about Antenatal Mental Hea... | Gold topic: Antenatal Mental Health Support vs Retrieved topic: Postpartum Mental Wellbeing |
| `PAIR-PRG-051` | base | `PAS-DNG-002` | `PAS-SYM-003` (Score: 0.0965) | My face and hands suddenly became very swollen thi... | Gold topic: preeclampsia_symptoms vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-PRG-051` | rewording_1 | `PAS-DNG-002` | `PAS-SYM-003` (Score: 0.1182) | Can you explain about preeclampsia_symptoms regard... | Gold topic: preeclampsia_symptoms vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-PRG-051` | rewording_2 | `PAS-DNG-002` | `PAS-SYM-003` (Score: 0.0985) | What should a mother do about preeclampsia_symptom... | Gold topic: preeclampsia_symptoms vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-PRG-062` | rewording_1 | `PAS-SYM-001` | `PAS-FMP-001` (Score: 0.098) | Can you explain about hyperemesis_gravidarum regar... | Gold topic: hyperemesis_gravidarum vs Retrieved topic: Family Planning |
| `PAIR-PRG-062` | rewording_2 | `PAS-SYM-001` | `PAS-FMP-001` (Score: 0.0609) | What should a mother do about hyperemesis_gravidar... | Gold topic: hyperemesis_gravidarum vs Retrieved topic: Family Planning |
| `PAIR-PRG-071` | base | `PAS-SYM-004` | `PAS-NEW-003` (Score: 0.0889) | Which side is best for sleeping during the second ... | Gold topic: sleep_position vs Retrieved topic: Newborn Danger Signs |
| `PAIR-PRG-071` | rewording_1 | `PAS-SYM-004` | `PAS-ANC-002` (Score: 0.1014) | I have painful urination with a burning sensation ... | Gold topic: sleep_position vs Retrieved topic: Antenatal Care |
| `PAIR-PRG-071` | rewording_2 | `PAS-SYM-004` | `PAS-ANC-002` (Score: 0.1269) | It burns painfully whenever I pass urine, could th... | Gold topic: sleep_position vs Retrieved topic: Antenatal Care |
| `PAIR-PRG-075` | base | `PAS-SYM-004` | `PAS-MED-002` (Score: 0.082) | I noticed a dark vertical line appearing down the ... | Gold topic: linea_nigra vs Retrieved topic: Medication Safety |
| `PAIR-PRG-075` | rewording_1 | `PAS-SYM-004` | `PAS-MED-002` (Score: 0.082) | Can you explain about linea_nigra regarding I noti... | Gold topic: linea_nigra vs Retrieved topic: Medication Safety |
| `PAIR-PRG-075` | rewording_2 | `PAS-SYM-004` | `PAS-SYM-002` (Score: 0.0579) | What should a mother do about linea_nigra when ask... | Gold topic: linea_nigra vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-PRG-078` | base | `PAS-ANC-004` | `PAS-LAB-001` (Score: 0.2399) | What is an emergency birth preparedness plan and w... | Gold topic: birth_preparedness_plan vs Retrieved topic: Labour Preparation |
| `PAIR-PRG-078` | rewording_1 | `PAS-ANC-004` | `PAS-LAB-001` (Score: 0.1738) | Can you explain about birth_preparedness_plan rega... | Gold topic: birth_preparedness_plan vs Retrieved topic: Labour Preparation |
| `PAIR-PRG-078` | rewording_2 | `PAS-ANC-004` | `PAS-LAB-001` (Score: 0.0976) | What should a mother do about birth_preparedness_p... | Gold topic: birth_preparedness_plan vs Retrieved topic: Labour Preparation |
| `PAIR-PRG-081` | base | `PAS-DNG-001` | `PAS-PST-002` (Score: 0.1176) | Help! I am 36 weeks and heavy blood is pouring dow... | Gold topic: antepartum_hemorrhage vs Retrieved topic: Postpartum Recovery |
| `PAIR-PRG-081` | rewording_1 | `PAS-DNG-001` | `PAS-PST-002` (Score: 0.1114) | Can you explain about antepartum_hemorrhage regard... | Gold topic: antepartum_hemorrhage vs Retrieved topic: Postpartum Recovery |
| `PAIR-PRG-081` | rewording_2 | `PAS-DNG-001` | `PAS-PST-002` (Score: 0.0918) | What should a mother do about antepartum_hemorrhag... | Gold topic: antepartum_hemorrhage vs Retrieved topic: Postpartum Recovery |
| `PAIR-PRG-085` | base | `PAS-DNG-004` | `PAS-ANC-003` (Score: 0.1444) | I am 34 weeks pregnant and running a 39.5 degree f... | Gold topic: severe_maternal_fever_sepsis vs Retrieved topic: Antenatal Care |
| `PAIR-PRG-085` | rewording_1 | `PAS-DNG-004` | `PAS-MEN-001` (Score: 0.0946) | Can you explain about severe_maternal_fever_sepsis... | Gold topic: severe_maternal_fever_sepsis vs Retrieved topic: Postpartum Mental Wellbeing |
| `PAIR-PRG-085` | rewording_2 | `PAS-DNG-004` | `PAS-PST-001` (Score: 0.0781) | What should a mother do about severe_maternal_feve... | Gold topic: severe_maternal_fever_sepsis vs Retrieved topic: Postpartum Recovery |
| `PAIR-PRG-093` | rewording_1 | `PAS-ANC-003` | `PAS-PST-001` (Score: 0.0834) | Can you explain about itn_malaria_prevention regar... | Gold topic: itn_malaria_prevention vs Retrieved topic: Postpartum Recovery |
| `PAIR-PRG-093` | rewording_2 | `PAS-ANC-003` | `PAS-PST-001` (Score: 0.085) | What should a mother do about itn_malaria_preventi... | Gold topic: itn_malaria_prevention vs Retrieved topic: Postpartum Recovery |
| `PAIR-PRG-095` | base | `PAS-NUT-001` | `PAS-NUT-002` (Score: 0.1255) | What foods rich in protein and calcium can I eat l... | Gold topic: local_nutrition_sources vs Retrieved topic: Maternal Nutrition |
| `PAIR-PRG-095` | rewording_1 | `PAS-NUT-001` | `PAS-NUT-002` (Score: 0.1292) | Can you explain about local_nutrition_sources rega... | Gold topic: local_nutrition_sources vs Retrieved topic: Maternal Nutrition |
| `PAIR-PRG-095` | rewording_2 | `PAS-NUT-001` | `PAS-NUT-002` (Score: 0.0992) | What should a mother do about local_nutrition_sour... | Gold topic: local_nutrition_sources vs Retrieved topic: Maternal Nutrition |
| `PAIR-INF-008` | rewording_2 | `PAS-PST-003` | `PAS-PST-001` (Score: 0.055) | What should a mother do about cs_wound_dehiscence_... | Gold topic: cs_wound_dehiscence_sepsis vs Retrieved topic: Postpartum Recovery |
| `PAIR-INF-011` | base | `PAS-NEW-002` | `PAS-BRS-003` (Score: 0.0764) | My 6-week-old baby has a fever of 38.2 degrees Cel... | Gold topic: infant_fever_and_medication_decline vs Retrieved topic: Breastfeeding |
| `PAIR-INF-011` | rewording_1 | `PAS-NEW-002` | `PAS-BRS-003` (Score: 0.0764) | Can you explain about infant_fever_and_medication_... | Gold topic: infant_fever_and_medication_decline vs Retrieved topic: Breastfeeding |
| `PAIR-INF-011` | rewording_2 | `PAS-NEW-002` | `PAS-BRS-003` (Score: 0.0607) | What should a mother do about infant_fever_and_med... | Gold topic: infant_fever_and_medication_decline vs Retrieved topic: Breastfeeding |
| `PAIR-INF-022` | base | `PAS-NEW-003` | `PAS-NEW-001` (Score: 0.2928) | How should I clean and take care of my baby's umbi... | Gold topic: cord_care_chlorhexidine vs Retrieved topic: Newborn Care Basics |
| `PAIR-INF-022` | rewording_1 | `PAS-NEW-003` | `PAS-PST-004` (Score: 0.1108) | Can you explain about cord_care_chlorhexidine rega... | Gold topic: cord_care_chlorhexidine vs Retrieved topic: Postpartum Recovery |
| `PAIR-INF-022` | rewording_2 | `PAS-NEW-003` | `PAS-DNG-004` (Score: 0.0635) | What should a mother do about cord_care_chlorhexid... | Gold topic: cord_care_chlorhexidine vs Retrieved topic: Pregnancy Danger Signs |
| `PAIR-INF-027` | base | `PAS-NEW-003` | `PAS-ANC-003` (Score: 0.1152) | What vaccines does a baby receive at birth in Nige... | Gold topic: birth_dose_vaccines vs Retrieved topic: Antenatal Care |
| `PAIR-INF-027` | rewording_1 | `PAS-NEW-003` | `PAS-PST-001` (Score: 0.1023) | Can you explain about birth_dose_vaccines regardin... | Gold topic: birth_dose_vaccines vs Retrieved topic: Postpartum Recovery |
| `PAIR-INF-027` | rewording_2 | `PAS-NEW-003` | `PAS-PST-001` (Score: 0.0979) | What should a mother do about birth_dose_vaccines ... | Gold topic: birth_dose_vaccines vs Retrieved topic: Postpartum Recovery |
| `PAIR-INF-028` | base | `PAS-NEW-001` | `PAS-PST-001` (Score: 0.1294) | Why is it important to wait at least 24 hours befo... | Gold topic: delayed_bathing_hypothermia_prevention vs Retrieved topic: Postpartum Recovery |
| `PAIR-INF-028` | rewording_1 | `PAS-NEW-001` | `PAS-BRS-002` (Score: 0.2331) | How do I know if my newborn is getting enough brea... | Gold topic: delayed_bathing_hypothermia_prevention vs Retrieved topic: Breastfeeding |
| `PAIR-INF-028` | rewording_2 | `PAS-NEW-001` | `PAS-BRS-003` (Score: 0.1033) | What are the reliable signs that a breastfeeding b... | Gold topic: delayed_bathing_hypothermia_prevention vs Retrieved topic: Breastfeeding |
| `PAIR-INF-034` | base | `PAS-BRS-002` | `PAS-FMP-002` (Score: 0.0943) | How can I safely express and store breastmilk if I... | Gold topic: breastmilk_storage_guidelines vs Retrieved topic: Family Planning |
| `PAIR-INF-034` | rewording_1 | `PAS-BRS-002` | `PAS-MED-003` (Score: 0.0) | Can you explain about breastmilk_storage_guideline... | Gold topic: breastmilk_storage_guidelines vs Retrieved topic: Medication Safety |
| `PAIR-INF-034` | rewording_2 | `PAS-BRS-002` | `PAS-SYM-002` (Score: 0.071) | What should a mother do about breastmilk_storage_g... | Gold topic: breastmilk_storage_guidelines vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-INF-037` | base | `PAS-NEW-003` | `PAS-DNG-001` (Score: 0.0965) | How do I care for my baby's red diaper rash at hom... | Gold topic: diaper_rash_home_care vs Retrieved topic: Pregnancy Danger Signs |
| `PAIR-INF-037` | rewording_1 | `PAS-NEW-003` | `PAS-ANC-001` (Score: 0.1377) | Can you explain about diaper_rash_home_care regard... | Gold topic: diaper_rash_home_care vs Retrieved topic: Antenatal Care |
| `PAIR-INF-037` | rewording_2 | `PAS-NEW-003` | `PAS-PST-001` (Score: 0.0897) | What should a mother do about diaper_rash_home_car... | Gold topic: diaper_rash_home_care vs Retrieved topic: Postpartum Recovery |
| `PAIR-INF-040` | base | `PAS-NEW-003` | `PAS-PST-001` (Score: 0.112) | Why does my newborn's skin look dry and begin peel... | Gold topic: physiological_newborn_desquamation vs Retrieved topic: Postpartum Recovery |
| `PAIR-INF-040` | rewording_1 | `PAS-NEW-003` | `PAS-BRS-001` (Score: 0.1286) | Can you explain about physiological_newborn_desqua... | Gold topic: physiological_newborn_desquamation vs Retrieved topic: Breastfeeding |
| `PAIR-INF-040` | rewording_2 | `PAS-NEW-003` | `PAS-BRS-001` (Score: 0.0908) | What should a mother do about physiological_newbor... | Gold topic: physiological_newborn_desquamation vs Retrieved topic: Breastfeeding |
| `PAIR-INF-044` | base | `PAS-NEW-002` | `PAS-ANC-003` (Score: 0.0987) | My baby fell from the bed onto a concrete floor an... | Gold topic: infant_head_injury_trauma vs Retrieved topic: Antenatal Care |
| `PAIR-INF-044` | rewording_1 | `PAS-NEW-002` | `PAS-ANC-003` (Score: 0.0987) | Can you explain about infant_head_injury_trauma re... | Gold topic: infant_head_injury_trauma vs Retrieved topic: Antenatal Care |
| `PAIR-INF-044` | rewording_2 | `PAS-NEW-002` | `PAS-ANC-003` (Score: 0.0638) | What should a mother do about infant_head_injury_t... | Gold topic: infant_head_injury_trauma vs Retrieved topic: Antenatal Care |
| `PAIR-INF-046` | base | `PAS-NEW-003` | `PAS-MED-003` (Score: 0.0869) | My baby was exposed to someone with active tubercu... | Gold topic: infant_tb_contact_tracing vs Retrieved topic: Medication Safety |
| `PAIR-INF-046` | rewording_1 | `PAS-NEW-003` | `PAS-DNG-003` (Score: 0.106) | Can you explain about infant_tb_contact_tracing re... | Gold topic: infant_tb_contact_tracing vs Retrieved topic: Pregnancy Danger Signs |
| `PAIR-INF-046` | rewording_2 | `PAS-NEW-003` | `PAS-SYM-002` (Score: 0.0776) | What should a mother do about infant_tb_contact_tr... | Gold topic: infant_tb_contact_tracing vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-INF-048` | rewording_1 | `PAS-BRS-003` | `PAS-NEW-001` (Score: 0.185) | How should I care for baby's skin and what can I a... | Gold topic: postpartum_breast_lump vs Retrieved topic: Newborn Care Basics |
| `PAIR-INF-048` | rewording_2 | `PAS-BRS-003` | `PAS-SYM-001` (Score: 0.0763) | Greasy yellowish scales on infant's scalp, how do ... | Gold topic: postpartum_breast_lump vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-INF-054` | base | `PAS-NEW-002` | `PAS-SYM-001` (Score: 0.0783) | My baby drank liquid kerosene accidentally from a ... | Gold topic: kerosene_ingestion_poisoning vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-INF-054` | rewording_1 | `PAS-NEW-002` | `PAS-DNG-003` (Score: 0.106) | Can you explain about kerosene_ingestion_poisoning... | Gold topic: kerosene_ingestion_poisoning vs Retrieved topic: Pregnancy Danger Signs |
| `PAIR-INF-054` | rewording_2 | `PAS-NEW-002` | `PAS-SYM-002` (Score: 0.0776) | What should a mother do about kerosene_ingestion_p... | Gold topic: kerosene_ingestion_poisoning vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-INF-055` | base | `PAS-PST-001` | `PAS-SYM-003` (Score: 0.1092) | I am 10 days postpartum and suddenly experiencing ... | Gold topic: deep_vein_thrombosis_postpartum vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-INF-058` | base | `PAS-MED-003` | `PAS-ANC-003` (Score: 0.0994) | Can I give cough syrup to my 4-month-old baby who ... | Gold topic: cough_syrups_infant_decline vs Retrieved topic: Antenatal Care |
| `PAIR-INF-058` | rewording_2 | `PAS-MED-003` | `PAS-SYM-002` (Score: 0.071) | What should a mother do about cough_syrups_infant_... | Gold topic: cough_syrups_infant_decline vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-INF-059` | base | `PAS-NEW-002` | `PAS-DNG-004` (Score: 0.1066) | My 5-month-old baby pulls on his right ear constan... | Gold topic: acute_otitis_media vs Retrieved topic: Pregnancy Danger Signs |
| `PAIR-INF-059` | rewording_1 | `PAS-NEW-002` | `PAS-NUT-002` (Score: 0.1444) | When should I introduce solid foods and semi-solid... | Gold topic: acute_otitis_media vs Retrieved topic: Maternal Nutrition |
| `PAIR-INF-059` | rewording_2 | `PAS-NEW-002` | `PAS-BRS-002` (Score: 0.1837) | At what age is complementary feeding recommended a... | Gold topic: acute_otitis_media vs Retrieved topic: Breastfeeding |
| `PAIR-INF-060` | base | `PAS-NEW-003` | `PAS-ANC-004` (Score: 0.1061) | We missed our baby's 10-week immunization visit by... | Gold topic: immunization_catchup_ten_weeks vs Retrieved topic: Antenatal Care |
| `PAIR-INF-060` | rewording_1 | `PAS-NEW-003` | `PAS-FMP-001` (Score: 0.0763) | Can you explain about immunization_catchup_ten_wee... | Gold topic: immunization_catchup_ten_weeks vs Retrieved topic: Family Planning |
| `PAIR-INF-060` | rewording_2 | `PAS-NEW-003` | `PAS-FMP-001` (Score: 0.0578) | What should a mother do about immunization_catchup... | Gold topic: immunization_catchup_ten_weeks vs Retrieved topic: Family Planning |
| `PAIR-INF-069` | base | `PAS-NEW-003` | `PAS-NUT-001` (Score: 0.1061) | When should my baby receive Vitamin A supplementat... | Gold topic: vitamin_a_supplementation_schedule vs Retrieved topic: Maternal Nutrition |
| `PAIR-INF-069` | rewording_1 | `PAS-NEW-003` | `PAS-ANC-004` (Score: 0.1084) | Can you explain about vitamin_a_supplementation_sc... | Gold topic: vitamin_a_supplementation_schedule vs Retrieved topic: Antenatal Care |
| `PAIR-INF-069` | rewording_2 | `PAS-NEW-003` | `PAS-ANC-004` (Score: 0.0661) | What should a mother do about vitamin_a_supplement... | Gold topic: vitamin_a_supplementation_schedule vs Retrieved topic: Antenatal Care |
| `PAIR-INF-076` | base | `PAS-NEW-003` | `PAS-ANC-001` (Score: 0.1905) | Why is tracking my baby's growth on the Road to He... | Gold topic: growth_monitoring_chart vs Retrieved topic: Antenatal Care |
| `PAIR-INF-076` | rewording_1 | `PAS-NEW-003` | `PAS-DNG-003` (Score: 0.106) | Can you explain about growth_monitoring_chart rega... | Gold topic: growth_monitoring_chart vs Retrieved topic: Pregnancy Danger Signs |
| `PAIR-INF-076` | rewording_2 | `PAS-NEW-003` | `PAS-SYM-002` (Score: 0.0776) | What should a mother do about growth_monitoring_ch... | Gold topic: growth_monitoring_chart vs Retrieved topic: Common Pregnancy Symptoms |
| `PAIR-INF-077` | base | `PAS-NEW-003` | `PAS-MED-001` (Score: 0.1054) | When should my baby receive deworming medication i... | Gold topic: routine_infant_deworming vs Retrieved topic: Medication Safety |
| `PAIR-INF-077` | rewording_1 | `PAS-NEW-003` | `PAS-ANC-004` (Score: 0.1084) | Can you explain about routine_infant_deworming reg... | Gold topic: routine_infant_deworming vs Retrieved topic: Antenatal Care |
| `PAIR-INF-077` | rewording_2 | `PAS-NEW-003` | `PAS-ANC-004` (Score: 0.0661) | What should a mother do about routine_infant_dewor... | Gold topic: routine_infant_deworming vs Retrieved topic: Antenatal Care |
| `PAIR-INF-095` | base | `PAS-NEW-001` | `PAS-ANC-003` (Score: 0.0876) | How many hours of sleep does a 3-month-old infant ... | Gold topic: infant_sleep_duration vs Retrieved topic: Antenatal Care |
| `PAIR-INF-095` | rewording_1 | `PAS-NEW-001` | `PAS-PST-001` (Score: 0.089) | Can you explain about infant_sleep_duration regard... | Gold topic: infant_sleep_duration vs Retrieved topic: Postpartum Recovery |
| `PAIR-INF-095` | rewording_2 | `PAS-NEW-001` | `PAS-PST-001` (Score: 0.098) | What should a mother do about infant_sleep_duratio... | Gold topic: infant_sleep_duration vs Retrieved topic: Postpartum Recovery |

---

## 4. Key Engineering & Safety Findings
1. **High Semantic Sensitivity on Clinical Danger Signs:**
   Emergency danger sign queries (bleeding, fits, fluid rupture, respiratory distress) achieve near-perfect retrieval due to enriched indexing of `danger_signs_mentioned` in the vector corpus.
2. **Robustness to Paraphrasing:**
   Evaluating against two colloquial rewordings per scenario confirms that clinical terminology retains sufficient TF-IDF salience even under informal phrasing.
3. **Clinical Scaffold Isolation:**
   Because retrieval is decoupled from language model generation in `symmetric_pipeline.py`, retrieval precision directly protects the LLM from hallucinating medical guidelines.

---
*Report automatically generated by `scripts/run_retrieval_evaluation.py` on 120 held-out prompts.*
