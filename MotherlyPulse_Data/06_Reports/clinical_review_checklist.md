# MotherlyPulse Clinical Review Checklist

**Reviewer Name:** ___________________________  
**Professional Qualification / Role:** ___________________________ (e.g., Midwife, Obstetrician, Medical Officer)  
**Institution:** ___________________________  
**Review Date:** ___________________________  
**Review Status Endorsement:** [ ] Approved without changes | [ ] Approved with minor amendments | [ ] Major revisions required  

---

### Instructions for Clinical Reviewer
Please examine the items below extracted from the MotherlyPulse Data Package (`MotherlyPulse_Data`). Indicate whether each item meets clinical safety standards for community-level maternal guidance in Nigeria. If any recommendation contradicts current local clinical protocol or poses clinical risk, note the correction in the remarks column.

---

### 1. Danger Signs & Emergency Rules Audit (`03_Emergency_Rules/emergency_rules.csv`)

| Rule ID | Danger Sign & Stated Action | Clinical Accuracy (Pass/Fail) | Triage Level Appropriate? | Clinical Reviewer Remarks & Signature |
| :--- | :--- | :--- | :--- | :--- |
| **RUL-EMG-001** | Vaginal bleeding in pregnancy -> Immediate hospital evaluation; no vaginal insertion. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-002** | Severe postpartum bleeding (soaking 2+ pads/hr) -> Emergency hospital transfer for uterotonics. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-003** | Convulsions / fits -> Airway clearance, left lateral position, urgent transfer for MgSO4. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-004** | Severe headache + blurred vision -> Immediate hospital evaluation for severe preeclampsia. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-005** | Severe epigastric / upper abdominal pain -> Urgent obstetric workup for imminent eclampsia. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-006** | Reduced or absent baby movements -> Urgent fetal heart rate / CTG monitoring. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-007** | Sudden shortness of breath / chest pain -> Immediate oxygen support and pulmonary evaluation. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-008** | Severe constant abdominal pain -> Emergency transfer for placental abruption / uterine rupture. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-009** | Postpartum fever + foul lochia -> Immediate IV antibiotics for puerperal sepsis. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-010** | Thoughts of self-harm / infanticide -> Immediate crisis intervention; do not leave mother alone. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-011** | Rupture of membranes before term / green fluid -> Immediate hospital labor ward transfer. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-012** | Umbilical cord prolapse -> Knee-chest position, elevate hips, emergency Caesarean transfer. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-014** | Newborn inability to suckle -> Urgent hospital evaluation for neonatal sepsis / hypoglycemia. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-015** | Newborn convulsions / spasms -> Urgent airway, anticonvulsant, and sepsis workup. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-016** | Newborn fast breathing (>=60 bpm) / chest indrawing -> Emergency oxygen & antibiotic therapy. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-017** | Newborn hypothermia (<36.5C) or fever (>37.5C) -> Immediate warming / medical assessment. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-018** | Newborn extreme lethargy / floppiness -> Immediate hospital resuscitation. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-019** | Severe newborn jaundice (palms/soles yellow or Day 1) -> Phototherapy / exchange transfusion. | [ ] Pass [ ] Fail | [ ] Emergency | |
| **RUL-EMG-020** | Newborn omphalitis (cord red, swollen, draining pus) -> Urgent parenteral antibiotics. | [ ] Pass [ ] Fail | [ ] Emergency | |

---

### 2. Medication Safety & Clinical Boundaries Audit

| Safety Principle | Standard in Dataset | Clinically Endorsed? | Remarks |
| :--- | :--- | :--- | :--- |
| **Zero Diagnosis Principle** | Assistant refuses to provide medical diagnoses based on user text. | [ ] Yes [ ] No | |
| **Zero Prescription Principle**| Assistant declines all requests to prescribe drugs or state clinical dosages. | [ ] Yes [ ] No | |
| **Herbal Concoctions Warning** | Warning against unverified traditional concoctions (agbo), potash, or unprescribed teas. | [ ] Yes [ ] No | |
| **Routine Supplements Guidance**| Advises taking iron, folic acid, and malaria IPTp strictly as prescribed at ANC clinic. | [ ] Yes [ ] No | |
| **Immediate Triage Precedence**| Rule-based emergency escalation takes precedence over open-ended LLM conversation. | [ ] Yes [ ] No | |

---

### 3. Reviewer Final Endorsement

**Sign-off Statement:**  
*I have reviewed the clinical content, danger signs, triage levels, and safety constraints of the MotherlyPulse data package. With the notations indicated above, I confirm that the recommendations are safe and appropriate for lay community-level guidance.*

**Signature:** ______________________________________ **Date:** ________________________

