import sqlite3
from datetime import datetime

DB_NAME = "interviews.db"

def create_database():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT UNIQUE,
            company TEXT,
            role TEXT,
            interview_date TEXT,
            interview_time TEXT,
            timezone TEXT,
            interview_type TEXT,
            whatsapp_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()
    connection.close()

def save_interview(email_id, data):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO interviews
        (
            email_id,
            company,
            role,
            interview_date,
            interview_time,
            timezone,
            interview_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        email_id,
        data["company"],
        data["role"],
        data["date"],
        data["time"],
        data["timezone"],
        data["interview_type"]
    ))
    connection.commit()
    inserted = cursor.rowcount == 1
    connection.close()
    return inserted

def claim_notification(email_id):
    """Atomically claim a pending message notification for one interview."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE interviews SET whatsapp_sent = 2 "
        "WHERE email_id = ? AND whatsapp_sent = 0",
        (email_id,)
    )
    connection.commit()
    claimed = cursor.rowcount == 1
    connection.close()
    return claimed

def finish_notification(email_id, sent):
    """Mark a notification sent, or return it to pending so it can be retried."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE interviews SET whatsapp_sent = ? WHERE email_id = ?",
        (1 if sent else 0, email_id)
    )
    connection.commit()
    connection.close()

def get_recent_interviews(hours=24):
    """Get interviews found in the last specified hours"""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    
    time_threshold = datetime.now().timestamp() - (hours * 3600)
    
    cursor.execute("""
        SELECT COUNT(*) FROM interviews 
        WHERE created_at >= datetime(?, 'unixepoch')
    """, (time_threshold,))
    
    count = cursor.fetchone()[0]
    connection.close()
    
    return count
