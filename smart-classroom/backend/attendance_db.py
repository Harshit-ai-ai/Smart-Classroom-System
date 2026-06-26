"""
CSTPE Attendance Database - Extended Schema
Tracks Accumulated Active Presence with adaptive gap thresholds,
session IDs, environmental validation, and blockchain audit integration.
Provides comprehensive Excel reporting for teachers and students.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

from policy_engine import policy
from config import is_feature_enabled

DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "attendance.db")


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Core attendance tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_tracking (
            student_name TEXT PRIMARY KEY,
            first_seen TEXT,
            last_seen TEXT,
            accumulated_seconds INTEGER,
            status TEXT,
            session_id TEXT,

            adaptive_gap_threshold INTEGER DEFAULT 10,
            env_validated INTEGER DEFAULT 1,
            biometric_score REAL DEFAULT 0.0,
            zk_proof_count INTEGER DEFAULT 0,

            avg_height REAL DEFAULT 0,
            avg_posture REAL DEFAULT 0,
            avg_csr REAL DEFAULT 0,
            avg_swr REAL DEFAULT 0,
            avg_attention REAL DEFAULT 0,
                   
            height_samples INTEGER DEFAULT 0,
            posture_samples INTEGER DEFAULT 0,
            csr_samples INTEGER DEFAULT 0,
            swr_samples INTEGER DEFAULT 0,
            attention_samples INTEGER DEFAULT 0
        )
    """)

    # Historical attendance records (per-day log)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            date TEXT NOT NULL,
            class_name TEXT DEFAULT 'General',
            first_seen TEXT,
            last_seen TEXT,
            accumulated_seconds INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Absent',
            biometric_score REAL DEFAULT 0.0,
            zk_proof_count INTEGER DEFAULT 0,
            session_count INTEGER DEFAULT 1,
            env_violations INTEGER DEFAULT 0,
            avg_height REAL DEFAULT 0,
            avg_posture REAL DEFAULT 0,
            avg_csr REAL DEFAULT 0,
            avg_swr REAL DEFAULT 0,
            avg_attention REAL DEFAULT 0,
            UNIQUE(student_name, date, class_name)
        )
    """)

    # Embedding store table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embedding_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            embedding TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


def update_attendance(students, metadata=None, class_name="General"):
    """
    Called every frame. Updates the Accumulated Active Presence.
    students: list of recognized names.
    metadata: optional dict with per-student extra data.
    Returns a list of dicts with current student stats.
    """
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    today_str = now.strftime("%Y-%m-%d")
    metadata = metadata or {}

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    stats = []

    for student in students:
        if "Unknown" in student or "Possible" in student:
            continue

        student_meta = metadata.get(student, {})
        height = student_meta.get("height")
        posture = student_meta.get("posture")
        csr = student_meta.get("csr")
        swr = student_meta.get("swr")
        attention = student_meta.get("attention")
        adaptive_gap = student_meta.get("adaptive_gap", policy.get_int("gap_seconds", 10))
        env_valid = student_meta.get("env_valid", True)
        bio_score = student_meta.get("biometric_score", 0.0)

        cursor.execute(
            "SELECT first_seen, last_seen, accumulated_seconds, status, session_id, adaptive_gap_threshold, zk_proof_count, avg_height, avg_posture, avg_csr, avg_swr, avg_attention, height_samples, posture_samples, csr_samples, swr_samples, attention_samples FROM attendance_tracking WHERE student_name = ?",
            (student,),
        )
        row = cursor.fetchone()

        if row is None:
            import uuid
            session_id = str(uuid.uuid4())[:8]

            height_samples = 1 if height is not None else 0
            posture_samples = 1 if posture is not None else 0
            csr_samples = 1 if csr is not None else 0
            swr_samples = 1 if swr is not None else 0
            attention_samples = 1 if attention is not None else 0

            cursor.execute("""
                INSERT INTO attendance_tracking
                (
                student_name,
                first_seen,
                last_seen,
                accumulated_seconds,
                status,
                session_id,
                adaptive_gap_threshold,
                env_validated,
                biometric_score,
                zk_proof_count,

                avg_height,
                avg_posture,
                avg_csr,
                avg_swr,   
                avg_attention, 
                height_samples,
                posture_samples,
                csr_samples,
                swr_samples,
                attention_samples
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student, now_str, now_str, 0, "In Progress",
                  session_id, adaptive_gap, int(env_valid), bio_score, 0, height if height is not None else 0, posture if posture is not None else 0, csr if csr is not None else 0, swr if swr is not None else 0, attention if attention is not None else 0, height_samples, posture_samples, csr_samples, swr_samples, attention_samples))

            stat_entry = {
                "student": student,
                "accumulated_seconds": 0,
                "status": "In Progress",
                "session_id": session_id,
                "adaptive_gap": adaptive_gap,
                "env_valid": env_valid,
                "biometric_score": bio_score,
            }
            stats.append(stat_entry)

            # Log to blockchain
            if is_feature_enabled("blockchain_audit"):
                _log_audit("session_start", student, stat_entry)

            # Initialize daily history record
            _upsert_history(
                cursor,
                student,
                today_str,
                class_name,
                now_str,
                0,
                "In Progress",
                bio_score,
                height if height is not None else 0,
                posture if posture is not None else 0,
                csr if csr is not None else 0,
                swr if swr is not None else 0,
                attention if attention is not None else 0
            )

        else:
            (
            first_seen,
            last_seen_str,
            accumulated_seconds,
            status,
            session_id,
            stored_gap,
            zk_count,

            avg_height,
            avg_posture,
            avg_csr,
            avg_swr,
            avg_attention,
            height_samples,
            posture_samples,
            csr_samples,
            swr_samples,
            attention_samples
            ) = row
            last_seen = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S")

            time_diff = (now - last_seen).total_seconds()

            effective_gap = adaptive_gap if is_feature_enabled("adaptive_gap_threshold") else policy.get_int("gap_seconds", 10)
            should_accumulate = env_valid or not is_feature_enabled("environmental_gating")

            if time_diff < effective_gap and should_accumulate:
                accumulated_seconds += int(time_diff)
            elif time_diff >= effective_gap:
                if is_feature_enabled("session_recovery"):
                    import uuid
                    session_id = str(uuid.uuid4())[:8]

            threshold_seconds = policy.get_int("threshold_minutes", 40) * 60
            if accumulated_seconds >= threshold_seconds:
                status = "Present"

            if height is not None:

                avg_height = (
                avg_height * height_samples +
                height
                ) / (height_samples + 1)

                height_samples += 1

            if posture is not None:

                avg_posture = (
                avg_posture * posture_samples +
                posture
                ) / (posture_samples + 1)

                posture_samples += 1

            if csr is not None:

                avg_csr = (
                avg_csr * csr_samples +
                csr
                ) / (csr_samples + 1)

                csr_samples += 1

            if swr is not None:

                avg_swr = (
                avg_swr * swr_samples +
                swr
                ) / (swr_samples + 1)

                swr_samples+= 1

            if attention is not None:

                avg_attention = (
                avg_attention * attention_samples +
                attention
                ) / (attention_samples + 1)

                attention_samples += 1

            cursor.execute("""
                UPDATE attendance_tracking
                SET last_seen = ?,
                accumulated_seconds = ?,
                status = ?,
                session_id = ?,

                adaptive_gap_threshold = ?,
                env_validated = ?,
                biometric_score = ?,

                avg_height = ?,
                avg_posture = ?,
                avg_csr = ?,
                avg_swr = ?,
                avg_attention = ?,
                height_samples = ?,
                posture_samples = ?,
                csr_samples = ?,
                swr_samples = ?,
                attention_samples = ?
                WHERE student_name = ?
            """, (now_str, accumulated_seconds, status,
                  session_id, effective_gap, int(env_valid), bio_score, avg_height, avg_posture, avg_csr, avg_swr, avg_attention, height_samples, posture_samples, csr_samples, swr_samples, attention_samples, student))

            stat_entry = {
                "student": student,
                "accumulated_seconds": accumulated_seconds,
                "status": status,
                "session_id": session_id,
                "adaptive_gap": effective_gap,
                "env_valid": env_valid,
                "biometric_score": bio_score,
                "height": height,
                "posture": posture,
                "csr": csr,
                "swr": swr,
                "attention": attention,
            }
            stats.append(stat_entry)

            if is_feature_enabled("blockchain_audit"):
                _log_audit("attendance_update", student, {
                    "accumulated_seconds": accumulated_seconds,
                    "time_diff": time_diff,
                    "status": status,
                })

            if is_feature_enabled("zero_knowledge_proofs"):
                _generate_zk_proof(student, last_seen_str, now_str, True)
                cursor.execute(
                    "UPDATE attendance_tracking SET zk_proof_count = ? WHERE student_name = ?",
                    (zk_count + 1, student),
                )

            # Update daily history record
            _upsert_history(cursor, student, today_str, class_name, now_str, accumulated_seconds, status, bio_score, avg_height, avg_posture, avg_csr, avg_swr, avg_attention)

    conn.commit()
    conn.close()

    return stats


def _upsert_history(cursor, student, date_str, class_name, last_seen, acc_seconds, status, bio_score, avg_height, avg_posture, avg_csr, avg_swr, avg_attention):
    """Insert or update the daily attendance history record."""
    cursor.execute(
        "SELECT id FROM attendance_history WHERE student_name = ? AND date = ? AND class_name = ?",
        (student, date_str, class_name),
    )
    row = cursor.fetchone()

    if row is None:
        cursor.execute("""
            INSERT INTO attendance_history
            (student_name, date, class_name, first_seen, last_seen, accumulated_seconds, status, biometric_score, avg_height, avg_posture, avg_csr, avg_swr, avg_attention)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student, date_str, class_name, last_seen, last_seen, acc_seconds, status, bio_score, avg_height, avg_posture, avg_csr, avg_swr, avg_attention))
    else:
        cursor.execute("""
            UPDATE attendance_history
            SET last_seen = ?, accumulated_seconds = ?, status = ?, biometric_score = ?, avg_height=?, avg_posture=?, avg_csr=?, avg_swr=?, avg_attention=?
            WHERE id = ?
        """, (last_seen, acc_seconds, status, bio_score, avg_height, avg_posture, avg_csr, avg_swr, avg_attention,row[0]))


def get_all_stats():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM attendance_tracking", conn)
    conn.close()
    return df.to_dict(orient="records")


def get_student_history(student_name):
    """Get attendance history for a specific student across all dates."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT * FROM attendance_history WHERE student_name = ? ORDER BY date DESC",
        conn,
        params=(student_name,),
    )
    conn.close()
    return df.to_dict(orient="records")


def get_all_history(date_filter=None):
    """Get attendance history for all students, optionally filtered by date."""
    conn = sqlite3.connect(DB_FILE)
    if date_filter:
        df = pd.read_sql_query(
            "SELECT * FROM attendance_history WHERE date = ? ORDER BY student_name",
            conn,
            params=(date_filter,),
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM attendance_history ORDER BY date DESC, student_name",
            conn,
        )
    conn.close()
    return df.to_dict(orient="records")


def get_class_summary(class_name="General", date_filter=None):
    """Get a summary for a specific class."""
    conn = sqlite3.connect(DB_FILE)
    if date_filter:
        df = pd.read_sql_query(
            "SELECT * FROM attendance_history WHERE class_name = ? AND date = ?",
            conn,
            params=(class_name, date_filter),
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM attendance_history WHERE class_name = ?",
            conn,
            params=(class_name,),
        )
    conn.close()

    if df.empty:
        return {"total_students": 0, "present": 0, "absent": 0, "in_progress": 0, "records": []}

    records = df.to_dict(orient="records")
    present = len(df[df["status"] == "Present"])
    in_progress = len(df[df["status"] == "In Progress"])
    absent = len(df[df["status"] == "Absent"])

    return {
        "total_students": len(df),
        "present": present,
        "in_progress": in_progress,
        "absent": absent,
        "attendance_rate": round(present / len(df) * 100, 1) if len(df) > 0 else 0,
        "records": records,
    }


def export_to_excel():
    """
    Generate a comprehensive multi-sheet Excel report for the teacher.
    Sheets:
      1. Today's Attendance - Current session with all columns
      2. Attendance History - Historical records across all dates
      3. Student Summary - Per-student aggregated stats
      4. Class Summary - Per-date attendance rates
      5. Audit Trail - Blockchain audit events
    """
    conn = sqlite3.connect(DB_FILE)

    excel_file = os.path.join(os.path.dirname(__file__), "attendance_report.xlsx")

    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        # Sheet 1: Today's Session
        df_today = pd.read_sql_query("SELECT * FROM attendance_tracking", conn)
        if not df_today.empty:
            df_today["active_minutes"] = (df_today["accumulated_seconds"] / 60).round(1)
            threshold = policy.get_int("threshold_minutes", 40)
            df_today["progress_pct"] = ((df_today["accumulated_seconds"] / (threshold * 60)) * 100).clip(upper=100).round(1)
            df_today["attention_pct"] = (
                df_today["avg_attention"] * 100
            ).round(1)

            df_today["height_m"] = (
                df_today["avg_height"]
            ).round(2)

            df_today["csr_score"] = (
                df_today["avg_csr"]
            ).round(3)

            df_today["swr_score"] = (
                df_today["avg_swr"]
            ).round(3)

            df_today["posture_angle"] = (
                df_today["avg_posture"]
            ).round(2)

            df_today.to_excel(writer, sheet_name="Today Session", index=False)

        # Sheet 2: Attendance History
        df_history = pd.read_sql_query(
            "SELECT * FROM attendance_history ORDER BY date DESC, student_name",
            conn,
        )
        if not df_history.empty:
            df_history["active_minutes"] = (df_history["accumulated_seconds"] / 60).round(1)
        df_history.to_excel(writer, sheet_name="Attendance History", index=False)

        # Sheet 3: Student Summary
        if not df_history.empty:
            student_summary = df_history.groupby("student_name").agg(
                total_classes=("date", "count"),
                classes_present=("status", lambda x: (x == "Present").sum()),
                total_active_seconds=("accumulated_seconds", "sum"),
                avg_biometric_score=("biometric_score", "mean"),
                first_recorded=("date", "min"),
                last_recorded=("date", "max"),
            ).reset_index()
            student_summary["attendance_rate_pct"] = (
                (student_summary["classes_present"] / student_summary["total_classes"]) * 100
            ).round(1)
            student_summary["total_active_hours"] = (student_summary["total_active_seconds"] / 3600).round(2)
            student_summary.to_excel(writer, sheet_name="Student Summary", index=False)
        else:
            pd.DataFrame(columns=["student_name", "total_classes", "classes_present", "attendance_rate_pct"]).to_excel(
                writer, sheet_name="Student Summary", index=False
            )

        # Sheet 4: Daily Class Summary
        if not df_history.empty:
            daily_summary = df_history.groupby("date").agg(
                total_students=("student_name", "nunique"),
                present_count=("status", lambda x: (x == "Present").sum()),
                in_progress_count=("status", lambda x: (x == "In Progress").sum()),
                absent_count=("status", lambda x: (x == "Absent").sum()),
                avg_accumulated_seconds=("accumulated_seconds", "mean"),
            ).reset_index()
            daily_summary["attendance_rate_pct"] = (
                (daily_summary["present_count"] / daily_summary["total_students"]) * 100
            ).round(1)
            daily_summary.to_excel(writer, sheet_name="Daily Summary", index=False)
        else:
            pd.DataFrame(columns=["date", "total_students", "present_count", "attendance_rate_pct"]).to_excel(
                writer, sheet_name="Daily Summary", index=False
            )

        # Sheet 5: Audit Trail
        try:
            from audit_blockchain import audit_chain
            events = audit_chain.get_recent_events(limit=500)
            if events:
                df_audit = pd.DataFrame(events)
                df_audit.to_excel(writer, sheet_name="Audit Trail", index=False)
            else:
                pd.DataFrame(columns=["timestamp", "event_type", "student", "hash"]).to_excel(
                    writer, sheet_name="Audit Trail", index=False
                )
        except Exception:
            pd.DataFrame(columns=["timestamp", "event_type", "student", "hash"]).to_excel(
                writer, sheet_name="Audit Trail", index=False
            )

    conn.close()
    return excel_file


def export_student_report(student_name):
    """
    Generate a personal attendance report Excel file for a specific student.
    """
    conn = sqlite3.connect(DB_FILE)

    excel_file = os.path.join(os.path.dirname(__file__), f"student_report_{student_name}.xlsx")

    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        # Attendance records
        df = pd.read_sql_query(
            "SELECT date, class_name, first_seen, last_seen, accumulated_seconds, status, biometric_score "
            "FROM attendance_history WHERE student_name = ? ORDER BY date DESC",
            conn,
            params=(student_name,),
        )
        if not df.empty:
            df["active_minutes"] = (df["accumulated_seconds"] / 60).round(1)
        df.to_excel(writer, sheet_name="My Attendance", index=False)

        # Summary
        if not df.empty:
            total = len(df)
            present = len(df[df["status"] == "Present"])
            summary_data = {
                "Metric": [
                    "Student Name",
                    "Total Classes Recorded",
                    "Classes Present",
                    "Classes Absent/Partial",
                    "Attendance Rate (%)",
                    "Total Active Hours",
                    "Average Biometric Score",
                    "Report Generated",
                ],
                "Value": [
                    student_name,
                    total,
                    present,
                    total - present,
                    round(present / total * 100, 1) if total > 0 else 0,
                    round(df["accumulated_seconds"].sum() / 3600, 2),
                    round(df["biometric_score"].mean(), 3),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ],
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
        else:
            pd.DataFrame({"Metric": ["No records found"], "Value": ["-"]}).to_excel(
                writer, sheet_name="Summary", index=False
            )

    conn.close()
    return excel_file


def finalize_day(class_name="General"):
    """
    End-of-day finalization. Marks any 'In Progress' students as
    'Absent' or 'Partial' based on their accumulated time,
    and freezes the daily record in history.
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    threshold = policy.get_int("threshold_minutes", 40) * 60

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT student_name, accumulated_seconds, status FROM attendance_tracking")
    rows = cursor.fetchall()

    finalized = []
    for student_name, acc_secs, status in rows:
        if status == "In Progress":
            if acc_secs >= threshold:
                final_status = "Present"
            elif acc_secs > 0:
                final_status = "Partial"
            else:
                final_status = "Absent"
        else:
            final_status = status

        # Update the tracking table
        cursor.execute(
            "UPDATE attendance_tracking SET status = ? WHERE student_name = ?",
            (final_status, student_name),
        )

        # Update the history record
        cursor.execute(
            "UPDATE attendance_history SET status = ? WHERE student_name = ? AND date = ? AND class_name = ?",
            (final_status, student_name, today_str, class_name),
        )

        finalized.append({
            "student": student_name,
            "accumulated_seconds": acc_secs,
            "final_status": final_status,
        })

        if is_feature_enabled("blockchain_audit"):
            _log_audit("day_finalized", student_name, {
                "date": today_str,
                "accumulated_seconds": acc_secs,
                "final_status": final_status,
            })

    conn.commit()
    conn.close()

    return finalized


def reset_db():
    """Reset the current session for a new class period."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance_tracking")
    cursor.execute("DELETE FROM embedding_store")
    conn.commit()
    conn.close()


def _log_audit(event_type, student, data):
    try:
        from audit_blockchain import audit_chain
        audit_chain.append_event(event_type, student, data)
    except Exception as e:
        print(f"Audit log error: {e}")


def _generate_zk_proof(student, window_start, window_end, was_present):
    try:
        from zk_prover import zk_prover
        zk_prover.generate_proof(student, window_start, window_end, was_present)
    except Exception as e:
        print(f"ZK proof error: {e}")