import base64
import os
from face_engine import recognize

# Check if test.jpeg exists
if not os.path.exists("test.jpeg"):
    print("test.jpeg not found.")
    exit(1)

# Encode test.jpeg to base64
with open("test.jpeg", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    
print("Testing YOLO + Face Engine with test.jpeg...")
results = recognize(encoded_string)
print("Vision Pipeline Results:", results)
print("TEST SUCCESSFUL!")
