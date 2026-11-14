"""
MotherlyPulse Automated Health Reminders Engine
Supports:
1. Appointment reminders (Antenatal clinic & pediatric checks).
2. Medication reminders (Faithfully repeats the user's own stated medication guidance).
3. Infant vaccination schedule generator based on the official National Immunization Schedule
   (National Primary Health Care Development Agency - NPHCDA Nigeria).
"""

import datetime
from typing import Dict, Any, List, Optional
from .user_store import UserStore, get_wat_timezone

# Official Nigerian Routine Immunization Schedule (NPHCDA)
# Clarification: Milestone 7 (15 Months) is retained as supported by project source SRC-NPHCDA-RI-2023.
# This milestone is scheduled as a prospective FUTURE reminder for an already registered infant
# (who must be <= 1 year old at initial registration). This is NOT permission to onboard children older than one year.
NATIONAL_IMMUNIZATION_SCHEDULE = [
    {
        "milestone": "At Birth",
        "days_from_birth": 0,
        "vaccines": ["BCG", "OPV 0", "Hepatitis B birth dose"],
        "description": "Protection against severe tuberculosis, polio, and hepatitis B infection."
    },
    {
        "milestone": "6 Weeks",
        "days_from_birth": 42,
        "vaccines": ["Pentavalent 1", "OPV 1", "PCV 1", "Rotavirus 1"],
        "description": "Protection against diphtheria, tetanus, whooping cough, hepatitis B, Hib, pneumonia, and severe rotavirus diarrhea."
    },
    {
        "milestone": "10 Weeks",
        "days_from_birth": 70,
        "vaccines": ["Pentavalent 2", "OPV 2", "PCV 2", "Rotavirus 2"],
        "description": "Second dose protection for pentavalent, polio, pneumonia, and rotavirus."
    },
    {
        "milestone": "14 Weeks",
        "days_from_birth": 98,
        "vaccines": ["Pentavalent 3", "OPV 3", "PCV 3", "Inactivated Polio Vaccine (IPV)"],
        "description": "Third round completing primary infant immunization series."
    },
    {
        "milestone": "6 Months",
        "days_from_birth": 180,
        "vaccines": ["Vitamin A (First Dose)"],
        "description": "Supports eye health, immune system protection, and overall growth."
    },
    {
        "milestone": "9 Months",
        "days_from_birth": 270,
        "vaccines": ["Measles 1", "Yellow Fever", "Meningitis A"],
        "description": "Critical protection against measles outbreaks, yellow fever, and meningitis."
    },
    {
        "milestone": "15 Months",
        "days_from_birth": 450,
        "vaccines": ["Measles 2"],
        "description": "Second dose booster to ensure lasting protection against measles."
    }
]


class ReminderEngine:
    def __init__(self, user_store: Optional[UserStore] = None):
        self.user_store = user_store or UserStore()
        self.tz = get_wat_timezone()

    def schedule_appointment_reminder(
        self,
        user_id: str,
        appointment_date: str,
        clinic_name: str = "your primary health clinic",
        time_slot: str = "08:00 AM",
        remind_days_before: int = 1
    ) -> int:
        """
        Schedules an antenatal or infant clinic visit reminder (default 24h prior).
        """
        apt_dt = datetime.date.fromisoformat(appointment_date)
        remind_dt = apt_dt - datetime.timedelta(days=remind_days_before)
        scheduled_iso = f"{remind_dt.isoformat()}T08:00:00"
        
        text = (
            f"Upcoming clinic appointment tomorrow ({appointment_date}) "
            f"at {clinic_name} ({time_slot}). Remember to bring your antenatal or child health card."
        )
        return self.user_store.add_reminder(user_id, "appointment", text, scheduled_iso, frequency="once")

    def schedule_medication_reminder(
        self,
        user_id: str,
        user_medication_text: str,
        scheduled_time_iso: str,
        frequency: str = "daily"
    ) -> int:
        """
        Schedules a medication reminder by faithfully repeating the user's own stated text.
        Guarantees: Zero clinical mutation or independent drug generation.
        """
        text = f"Medication reminder (as scheduled by you): {user_medication_text.strip()}"
        return self.user_store.add_reminder(user_id, "medication", text, scheduled_time_iso, frequency=frequency)

    def schedule_single_vaccination_reminder(
        self,
        user_id: str,
        vaccine_name: str,
        due_date: str,
        clinic_name: str = "your primary health clinic"
    ) -> int:
        """
        Schedules a single vaccination milestone reminder 2 days prior.
        """
        vax_dt = datetime.date.fromisoformat(due_date)
        remind_dt = vax_dt - datetime.timedelta(days=2)
        scheduled_iso = f"{remind_dt.isoformat()}T08:00:00"
        text = (
            f"Vaccination reminder: Baby is scheduled for {vaccine_name} on {due_date} "
            f"at {clinic_name}. Session days may have changed; contact clinic before travelling."
        )
        return self.user_store.add_reminder(user_id, "vaccination", text, scheduled_iso, frequency="once")

    def schedule_infant_vaccination_series(
        self,
        user_id: str,
        baby_birth_date: str
    ) -> List[int]:
        """
        Calculates all infant routine vaccination dates from baby's birth date and schedules reminders.
        """
        birth_dt = datetime.date.fromisoformat(baby_birth_date)
        scheduled_ids = []

        for item in NATIONAL_IMMUNIZATION_SCHEDULE:
            due_date = birth_dt + datetime.timedelta(days=item["days_from_birth"])
            # Schedule reminder 2 days before clinic
            remind_dt = max(birth_dt, due_date - datetime.timedelta(days=2))
            scheduled_iso = f"{remind_dt.isoformat()}T08:00:00"

            vaccines_str = ", ".join(item["vaccines"])
            text = (
                f"Vaccination Milestone ({item['milestone']}): Baby is due for {vaccines_str} "
                f"on or around {due_date.isoformat()}. {item['description']} "
                "Session days may have changed; contact the clinic before travelling."
            )
            r_id = self.user_store.add_reminder(user_id, "vaccination", text, scheduled_iso, frequency="once")
            scheduled_ids.append(r_id)

        return scheduled_ids

    def cancel_reminder(self, user_id: str, reminder_id: int) -> bool:
        """Cancels an active reminder."""
        return self.user_store.cancel_reminder(user_id, reminder_id)

    def edit_reminder(
        self,
        user_id: str,
        reminder_id: int,
        reminder_text: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        frequency: Optional[str] = None
    ) -> bool:
        """Edits an active reminder."""
        return self.user_store.update_reminder(user_id, reminder_id, reminder_text, scheduled_time, frequency)

    def process_due_reminders(self, current_time_iso: str = None) -> List[Dict[str, Any]]:
        """
        Polls for due reminders, marks them delivered in SQLite to prevent duplicate
        delivery across application restarts, and returns them for channel dispatch.
        """
        due = self.user_store.get_due_reminders(current_time_iso)
        delivered_list = []
        for r in due:
            self.user_store.mark_reminder_delivered(r["reminder_id"])
            delivered_list.append(r)
        return delivered_list

    def format_reminder_notification(self, reminder: Dict[str, Any], language: str = "English") -> str:
        """Formats a dispatched reminder notification in the user's preferred language."""
        r_type = reminder.get("reminder_type", "").title()
        text = reminder.get("reminder_text", "")
        freq = reminder.get("frequency", "once")
        freq_str = f" [Frequency: {freq}]" if freq and freq != "once" else ""

        if language == "Yoruba":
            type_yo = {"Appointment": "Abẹwo Ile-iwosan", "Medication": "Oogun", "Vaccination": "Ajesara"}.get(r_type, r_type)
            return (
                f"🔔 IRANTI MOTHERLYPULSE ({type_yo}){freq_str}\n\n"
                f"{text}\n\n"
                f"Ti pajawiri ba wa, pe 112 lẹsẹkẹsẹ."
            )
        elif language == "Nigerian Pidgin":
            type_pcm = {"Appointment": "Clinic Visit", "Medication": "Medicine", "Vaccination": "Vaccine"}.get(r_type, r_type)
            return (
                f"🔔 MOTHERLYPULSE REMINDER ({type_pcm}){freq_str}\n\n"
                f"{text}\n\n"
                f"If any emergency happen, call 112 quick-quick."
            )
        else:
            return (
                f"🔔 MOTHERLYPULSE REMINDER ({r_type}){freq_str}\n\n"
                f"{text}\n\n"
                f"In any medical emergency, call 112 immediately."
            )
