from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from face_engine import recognize
from attendance_db import save_attendance

app = FastAPI()

os.makedirs("static", exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory="."),
    name="static"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://smart-classroom-system-vert.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttendanceRequest(BaseModel):

    image: str

@app.get("/download")
def download_csv():
    return FileResponse(
        "attendance.csv",
        media_type="text/csv",
        filename="attendance.csv"
    )

@app.get("/db")
def check_db():

    from face_engine import load_encodings

    return {
        "students":
        list(
            load_encodings().keys()
        )
    }


@app.get("/")
def home():

    return {
        "message":
        "Smart Classroom Backend Running"
    }


@app.post("/recognize")
async def recognize_students(
    request: AttendanceRequest
):

    students = recognize(
        request.image
    )

    return {
        "students":
        students
    }


@app.post("/attendance")
async def attendance(
    request: AttendanceRequest
):

    students = recognize(
        request.image
    )

    save_attendance(
        students
    )

    return {

        "present":
        students,

        "count":
        len(
            students
        )
    }

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )


    