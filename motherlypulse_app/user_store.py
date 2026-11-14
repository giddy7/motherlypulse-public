"""
MotherlyPulse User & Session Persistence Store
Lightweight SQLite-backed storage for user registration, language preferences,
consent tracking, maternal milestones, and scheduled reminders.
"""

import sqlite3
import os
import json
import re
import datetime
from typing import Dict, Any, List, Optional, Tuple

def get_wat_timezone():
    """Returns Africa/Lagos (UTC+1) timezone."""
    try:
        import zoneinfo
        return zoneinfo.ZoneInfo("Africa/Lagos")
    except Exception:
        return datetime.timezone(datetime.timedelta(hours=1), name="WAT")

def get_default_db_path() -> str:
    """
    Determines the database path according to environment and persistence tier:
    1. MOTHERLYPULSE_DB_PATH environment variable (explicit administrator override).
    2. /var/lib/motherlypulse/motherlypulse_user_store.db (persistent location outside Git on Linux).
    3. Local directory motherlypulse_app/motherlypulse_user_store.db (development/test fallback).
    """
    env_path = os.environ.get("MOTHERLYPULSE_DB_PATH")
    if env_path:
        return env_path

    prod_dir = "/var/lib/motherlypulse"
    if os.path.exists(prod_dir) and os.access(prod_dir, os.W_OK):
        return os.path.join(prod_dir, "motherlypulse_user_store.db")

    return os.path.join(os.path.dirname(__file__), "motherlypulse_user_store.db")

DB_PATH = get_default_db_path()

def get_db_connection(db_path: str = None) -> sqlite3.Connection:
    target_path = db_path or get_default_db_path()
    parent_dir = os.path.dirname(target_path)
    if parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except OSError:
            pass

    conn = sqlite3.connect(target_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    # Enable Write-Ahead Logging (WAL) for safe non-blocking concurrent backups & reads
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except sqlite3.DatabaseError:
        pass
    conn.row_factory = sqlite3.Row
    return conn

def parse_and_validate_date(
    date_str: str,
    user_group: str,
    ref_date: Optional[datetime.date] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Parses and clinically validates dates for pregnancy or infant milestones.
    Supports formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY.
    
    Validation invariants:
    - Pregnant woman: Expected Delivery Date (EDD) must be plausible gestation.
      Allowed range: [ref_date - 14 days, ref_date + 294 days (42 weeks)].
      Rejects dates outside this gestational boundary.
    - Mother/caregiver: Baby's Date of Birth (DOB) must be:
      Allowed range: [ref_date - 1825 days (5 years), ref_date].
      Rejects future dates or children older than 5 years.
      
    Returns: (is_valid, normalized_iso_date, error_code_or_message)
    """
    if not date_str or not isinstance(date_str, str):
        return False, None, "empty_date"

    cleaned = date_str.strip()
    parsed_date = None

    # Try ISO format YYYY-MM-DD
    try:
        parsed_date = datetime.date.fromisoformat(cleaned)
    except ValueError:
        pass

    # Try common formats DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    if not parsed_date:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d"):
            try:
                parsed_date = datetime.datetime.strptime(cleaned, fmt).date()
                break
            except ValueError:
                continue

    if not parsed_date:
        return False, None, "invalid_format"

    ref = ref_date or datetime.date.today()
    iso_str = parsed_date.isoformat()

    if user_group == "pregnant_woman":
        # Gestational sanity check: 42 weeks (294 days) maximum gestation
        min_edd = ref - datetime.timedelta(days=14)   # Slightly overdue allowed directly
        max_edd = ref + datetime.timedelta(days=294)  # 42 weeks maximum gestation
        if parsed_date < min_edd:
            # Overdue by > 14 days: returns iso_str so the bot can ask if baby is born or retain pregnancy profile
            return False, iso_str, "edd_in_past"
        if parsed_date > max_edd:
            return False, None, "edd_too_far_future"
        return True, iso_str, None

    elif user_group == "mother_infant":
        if parsed_date > ref:
            return False, None, "dob_in_future"
        # Project registration boundary: Mothers and infants up to one year after birth (365 days).
        # Note: The 15-month NPHCDA routine measles booster is scheduled as a future reminder
        # for an already registered infant, NOT permission to onboard children older than one year.
        min_dob = ref - datetime.timedelta(days=365)
        if parsed_date < min_dob:
            return False, None, "dob_too_old"
        return True, iso_str, None

    else:
        # Generic date validation
        return True, iso_str, None

def init_db(db_path: str = None):
    target_path = db_path or get_default_db_path()
    conn = get_db_connection(target_path)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        channel TEXT NOT NULL,
        language TEXT NOT NULL DEFAULT 'English',
        consent_given INTEGER NOT NULL DEFAULT 0,
        consent_date TEXT,
        alias TEXT,
        user_group TEXT CHECK(user_group IN ('pregnant_woman', 'mother_infant')),
        expected_delivery_date TEXT,
        baby_birth_date TEXT,
        registration_step TEXT DEFAULT 'completed',
        registration_data TEXT DEFAULT '{}',
        timezone TEXT DEFAULT 'Africa/Lagos',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    # Reminders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        reminder_type TEXT NOT NULL CHECK(reminder_type IN ('appointment', 'medication', 'vaccination')),
        reminder_text TEXT NOT NULL,
        scheduled_time TEXT NOT NULL,
        frequency TEXT DEFAULT 'once',
        status TEXT DEFAULT 'active',
        delivered INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
    )
    """)

    # Check and apply backward-compatible schema migrations
    cursor.execute("PRAGMA table_info(users)")
    existing_user_cols = {row["name"] for row in cursor.fetchall()}
    if "consent_date" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN consent_date TEXT")
    if "registration_step" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN registration_step TEXT DEFAULT 'completed'")
    if "registration_data" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN registration_data TEXT DEFAULT '{}'")
    if "timezone" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'Africa/Lagos'")

    cursor.execute("PRAGMA table_info(reminders)")
    existing_rem_cols = {row["name"] for row in cursor.fetchall()}
    if "frequency" not in existing_rem_cols:
        cursor.execute("ALTER TABLE reminders ADD COLUMN frequency TEXT DEFAULT 'once'")
    if "status" not in existing_rem_cols:
        cursor.execute("ALTER TABLE reminders ADD COLUMN status TEXT DEFAULT 'active'")

    conn.commit()
    conn.close()

class UserStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()
        init_db(self.db_path)

    def register_user(
        self,
        user_id: str,
        channel: str,
        language: str = "English",
        consent_given: bool = True,
        alias: str = None,
        user_group: str = None,
        expected_delivery_date: str = None,
        baby_birth_date: str = None,
        consent_date: str = None,
        registration_step: str = "completed",
        timezone: str = "Africa/Lagos"
    ) -> bool:
        """
        Registers or updates a user profile with date validation.
        Dates must be ISO format: YYYY-MM-DD.
        """
        # Validate dates if provided
        for d_str in [expected_delivery_date, baby_birth_date]:
            if d_str:
                try:
                    datetime.date.fromisoformat(d_str)
                except ValueError:
                    raise ValueError(f"Invalid date format '{d_str}'. Must be YYYY-MM-DD.")
                    
        now_iso = datetime.datetime.utcnow().isoformat()
        if consent_given and not consent_date:
            consent_date = now_iso

        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO users (
            user_id, channel, language, consent_given, consent_date, alias,
            user_group, expected_delivery_date, baby_birth_date, registration_step,
            registration_data, timezone, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            channel = excluded.channel,
            language = excluded.language,
            consent_given = excluded.consent_given,
            consent_date = coalesce(excluded.consent_date, users.consent_date),
            alias = coalesce(excluded.alias, users.alias),
            user_group = coalesce(excluded.user_group, users.user_group),
            expected_delivery_date = coalesce(excluded.expected_delivery_date, users.expected_delivery_date),
            baby_birth_date = coalesce(excluded.baby_birth_date, users.baby_birth_date),
            registration_step = excluded.registration_step,
            timezone = excluded.timezone,
            updated_at = excluded.updated_at
        """, (
            user_id, channel, language, 1 if consent_given else 0, consent_date, alias,
            user_group, expected_delivery_date, baby_birth_date, registration_step,
            "{}", timezone, now_iso, now_iso
        ))
        conn.commit()
        conn.close()
        return True

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def is_user_registered(self, user_id: str) -> bool:
        """Checks whether the user has completed full registration and given consent."""
        user = self.get_user(user_id)
        if not user:
            return False
        return bool(user.get("consent_given")) and user.get("registration_step") == "completed"

    def set_registration_step(
        self,
        user_id: str,
        step: str,
        partial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Saves current registration step and partial inputs to allow resumption."""
        now_iso = datetime.datetime.utcnow().isoformat()
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        # Check existing user
        cursor.execute("SELECT registration_data FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        existing_data = {}
        if row and row["registration_data"]:
            try:
                existing_data = json.loads(row["registration_data"])
            except Exception:
                existing_data = {}

        if partial_data:
            existing_data.update(partial_data)

        data_json = json.dumps(existing_data)

        if row:
            cursor.execute("""
            UPDATE users SET registration_step = ?, registration_data = ?, updated_at = ?
            WHERE user_id = ?
            """, (step, data_json, now_iso, user_id))
        else:
            cursor.execute("""
            INSERT INTO users (
                user_id, channel, language, consent_given, registration_step,
                registration_data, timezone, created_at, updated_at
            ) VALUES (?, 'telegram', 'English', 0, ?, ?, 'Africa/Lagos', ?, ?)
            """, (user_id, step, data_json, now_iso, now_iso))

        conn.commit()
        conn.close()
        return True

    def get_registration_state(self, user_id: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Retrieves the registration step and pending partial data."""
        user = self.get_user(user_id)
        if not user:
            return None, {}
        step = user.get("registration_step")
        data_str = user.get("registration_data") or "{}"
        try:
            data = json.loads(data_str)
        except Exception:
            data = {}
        return step, data

    def record_consent(self, user_id: str, consent_given: bool) -> bool:
        """Records user consent status with timestamp."""
        now_iso = datetime.datetime.utcnow().isoformat()
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        consent_val = 1 if consent_given else 0
        consent_date = now_iso if consent_given else None
        cursor.execute("""
        UPDATE users SET consent_given = ?, consent_date = ?, updated_at = ?
        WHERE user_id = ?
        """, (consent_val, consent_date, now_iso, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def update_language(self, user_id: str, language: str) -> bool:
        valid_langs = ["English", "Yoruba", "Nigerian Pidgin"]
        if language not in valid_langs:
            return False
        now_iso = datetime.datetime.utcnow().isoformat()
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET language = ?, updated_at = ? WHERE user_id = ?", (language, now_iso, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def update_alias(self, user_id: str, alias: str) -> bool:
        now_iso = datetime.datetime.utcnow().isoformat()
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET alias = ?, updated_at = ? WHERE user_id = ?", (alias.strip(), now_iso, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def update_user_group(
        self,
        user_id: str,
        user_group: str,
        expected_delivery_date: str = None,
        baby_birth_date: str = None
    ) -> bool:
        now_iso = datetime.datetime.utcnow().isoformat()
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE users SET user_group = ?,
                         expected_delivery_date = coalesce(?, expected_delivery_date),
                         baby_birth_date = coalesce(?, baby_birth_date),
                         updated_at = ?
        WHERE user_id = ?
        """, (user_group, expected_delivery_date, baby_birth_date, now_iso, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def delete_user(self, user_id: str) -> bool:
        """Deletes user and all associated reminders (Right to be Forgotten)."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def add_reminder(
        self,
        user_id: str,
        reminder_type: str,
        reminder_text: str,
        scheduled_time: str,
        frequency: str = "once"
    ) -> int:
        now_iso = datetime.datetime.utcnow().isoformat()
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO reminders (user_id, reminder_type, reminder_text, scheduled_time, frequency, status, delivered, created_at)
        VALUES (?, ?, ?, ?, ?, 'active', 0, ?)
        """, (user_id, reminder_type, reminder_text, scheduled_time, frequency, now_iso))
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reminder_id

    def get_reminder(self, reminder_id: int, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM reminders WHERE reminder_id = ? AND user_id = ?", (reminder_id, user_id))
        else:
            cursor.execute("SELECT * FROM reminders WHERE reminder_id = ?", (reminder_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def cancel_reminder(self, user_id: str, reminder_id: int) -> bool:
        """Cancels an active reminder for a user."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE reminders SET status = 'cancelled' WHERE reminder_id = ? AND user_id = ?
        """, (reminder_id, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def update_reminder(
        self,
        user_id: str,
        reminder_id: int,
        reminder_text: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        frequency: Optional[str] = None
    ) -> bool:
        """Edits an existing reminder's text, time, or frequency."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE reminders SET
            reminder_text = coalesce(?, reminder_text),
            scheduled_time = coalesce(?, scheduled_time),
            frequency = coalesce(?, frequency)
        WHERE reminder_id = ? AND user_id = ?
        """, (reminder_text, scheduled_time, frequency, reminder_id, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def get_due_reminders(self, current_time: str = None) -> List[Dict[str, Any]]:
        """Retrieves due active reminders."""
        if not current_time:
            current_time = datetime.datetime.utcnow().isoformat()
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM reminders 
        WHERE delivered = 0 AND status = 'active' AND scheduled_time <= ? 
        ORDER BY scheduled_time ASC
        """, (current_time,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_active_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves all non-delivered, active reminders for a specific user."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM reminders 
        WHERE user_id = ? AND delivered = 0 AND status = 'active' 
        ORDER BY scheduled_time ASC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves all reminders for a specific user (including delivered and cancelled)."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM reminders WHERE user_id = ? ORDER BY scheduled_time DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def mark_reminder_delivered(self, reminder_id: int):
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET delivered = 1 WHERE reminder_id = ?", (reminder_id,))
        conn.commit()
        conn.close()


def backup_database(
    source_db_path: Optional[str] = None,
    backup_dir: str = "/var/backups/motherlypulse"
) -> str:
    """
    Safely creates a consistent online SQLite backup accounting for WAL mode.
    Does not block active concurrent readers or writers.
    """
    src_path = source_db_path or get_default_db_path()
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source database not found: {src_path}")

    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"motherlypulse_backup_{timestamp}.sqlite3")

    # Use SQLite's online backup API (locks pages incrementally without corruption)
    src_conn = sqlite3.connect(src_path)
    dst_conn = sqlite3.connect(backup_file)
    with dst_conn:
        src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()

    try:
        os.chmod(backup_file, 0o600)
    except OSError:
        pass

    return backup_file
