import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_FILE = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_tracking (
            student_name TEXT PRIMARY KEY,
            first_seen TEXT,
            last_seen TEXT,
            accumulated_seconds INTEGER,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def update_attendance(students):
    """
    Called every frame. Updates the Accumulated Active Presence.
    students is a list of recognized names.
    Returns a list of dicts with current student stats.
    """
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    stats = []
    
    for student in students:
        if "Unknown" in student or "Possible" in student:
            continue
            
        cursor.execute("SELECT first_seen, last_seen, accumulated_seconds, status FROM attendance_tracking WHERE student_name = ?", (student,))
        row = cursor.fetchone()
        
        if row is None:
            # First time seeing this student
            cursor.execute("""
                INSERT INTO attendance_tracking (student_name, first_seen, last_seen, accumulated_seconds, status)
                VALUES (?, ?, ?, ?, ?)
            """, (student, now_str, now_str, 0, "In Progress"))
            
            stats.append({
                "student": student,
                "accumulated_seconds": 0,
                "status": "In Progress"
            })
        else:
            first_seen, last_seen_str, accumulated_seconds, status = row
            last_seen = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S")
            
            # Calculate time difference
            time_diff = (now - last_seen).total_seconds()
            
            # If they were seen less than 10 seconds ago, add to accumulated time
            # This prevents someone from leaving for an hour and gaining that hour as presence
            if time_diff < 10:
                accumulated_seconds += int(time_diff)
                
            # If accumulated_seconds >= 2400 (40 mins), mark as Present
            if accumulated_seconds >= 2400:
                status = "Present"
                
            cursor.execute("""
                UPDATE attendance_tracking
                SET last_seen = ?, accumulated_seconds = ?, status = ?
                WHERE student_name = ?
            """, (now_str, accumulated_seconds, status, student))
            
            stats.append({
                "student": student,
                "accumulated_seconds": accumulated_seconds,
                "status": status
            })
            
    conn.commit()
    conn.close()
    
    return stats

def get_all_stats():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM attendance_tracking", conn)
    conn.close()
    return df.to_dict(orient="records")

def export_to_excel():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM attendance_tracking", conn)
    conn.close()
    
    excel_file = "attendance_report.xlsx"
    df.to_excel(excel_file, index=False)
    return excel_file