from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio

from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from face_engine import recognize
from attendance_db import update_attendance, export_to_excel, get_all_stats

app = FastAPI()

os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="."), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttendanceRequest(BaseModel):
    image: str

# WebSocket connection manager for live teacher dashboard
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send initial state
    await websocket.send_json({"type": "init", "data": get_all_stats()})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/download")
def download_excel():
    excel_file = export_to_excel()
    return FileResponse(
        excel_file, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        filename="attendance_report.xlsx"
    )

@app.get("/db")
def check_db():
    from face_engine import load_encodings
    return {"students": list(load_encodings().keys())}

@app.get("/")
def home():
    return {"message": "Smart Classroom Backend Running (YOLO + Temporal Tracking Active)"}

@app.post("/recognize")
async def recognize_students(request: AttendanceRequest):
    students = recognize(request.image)
    return {"students": students}

@app.post("/attendance")
async def attendance(request: AttendanceRequest):
    # Run YOLO + Face Recognition
    students = recognize(request.image)
    
    # Update temporal Accumulated Active Presence (AAP) database
    stats = update_attendance(students)
    
    # Broadcast updates to Teacher Dashboard
    await manager.broadcast({"type": "update", "data": stats})
    
    return {
        "present": students,
        "count": len(students),
        "stats": stats
    }

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)