import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
from attendance_db import init_db, update_attendance, get_all_stats

# Remove DB if it exists to start fresh
if os.path.exists("attendance.db"):
    os.remove("attendance.db")

print("Initializing DB...")
init_db()

print("\n--- Test 1: First Sighting ---")
stats1 = update_attendance(["Alice", "Bob"])
print(stats1)
assert len(stats1) == 2
assert stats1[0]["accumulated_seconds"] == 0

print("\n--- Test 2: Sighting 5 seconds later ---")
# Wait a moment to simulate time passing (in real app, time_diff is calculated based on datetime.now())
# We'll just mock the datetime by sleeping, or we can trust the real-time.
time.sleep(2)
stats2 = update_attendance(["Alice"])
print(stats2)
# Alice should have ~2 seconds accumulated, Bob should not be updated.
assert stats2[0]["accumulated_seconds"] >= 2

print("\n--- Test 3: Sighting 15 seconds later (Loophole test) ---")
# The logic says if time_diff < 10, add to accumulated time. If > 10, it means they left.
time.sleep(11)
stats3 = update_attendance(["Alice"])
print(stats3)
# Alice should NOT have gained the 11 seconds because she was gone too long!
# Her accumulated time should remain what it was previously.
assert stats3[0]["accumulated_seconds"] < 10 # Should be around 2

print("\nAll logical checks passed successfully!")
