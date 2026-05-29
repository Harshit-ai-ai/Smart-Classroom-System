import { useEffect, useRef, useState } from "react";
import axios from "axios";

function App() {

  const API =
    "https://www.smart-classroom-system-production.up.railway.app";

  const videoRef = useRef(null);

  const canvasRef = useRef(null);

  const [students, setStudents] = useState([]);

  const [count, setCount] = useState(0);

  const [loading, setLoading] = useState(false);

  const [resultImage, setResultImage] = useState("");

  useEffect(() => {

    startCamera();

  }, []);

  const startCamera = async () => {

    try {

      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: true
        });

      videoRef.current.srcObject = stream;

    } catch (err) {

      alert(
        "Camera access denied"
      );

      console.log(err);
    }
  };

  const captureAttendance = async () => {

    setLoading(true);

    const canvas = canvasRef.current;

    const video = videoRef.current;

    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    ctx.drawImage(
      video,
      0,
      0
    );

    const image = canvas.toDataURL(
      "image/jpeg"
    );

    try {

      const res = await axios.post(
        `${API}/attendance`,
        {
          image: image
        }
      );

      setStudents(
        res.data.present
      );

      setCount(
        res.data.count
      );

      setResultImage(
        `${API}/static/result.jpg?t=` +
        new Date().getTime()
      );

    } catch (err) {

      console.log(err);
    }

    setLoading(false);
  };

  return (

    <div
      style={{
        fontFamily: "Arial",
        padding: "20px",
        background: "#f5f5f5",
        minHeight: "100vh"
      }}
    >

      <h1>
        Smart Classroom Attendance
      </h1>

      <video
        ref={videoRef}
        autoPlay
        playsInline
        width="700"
        style={{
          borderRadius: "10px",
          border: "3px solid black"
        }}
      />

      <br /><br />

      <button
        onClick={captureAttendance}
        style={{
          padding: "15px 30px",
          fontSize: "18px",
          cursor: "pointer"
        }}
      >

        {
          loading
          ?
          "Processing..."
          :
          "Capture Attendance"
        }

      </button>

      <h2>
        Present Students: {count}
      </h2>

      <table
        border="1"
        cellPadding="10"
        style={{
          background: "white"
        }}
      >

        <thead>

          <tr>

            <th>
              Student Name
            </th>

          </tr>

        </thead>

        <tbody>

          {
            students.map(
              (
                s,
                i
              ) => (

                <tr key={i}>

                  <td>
                    {s}
                  </td>

                </tr>
              )
            )
          }

        </tbody>

      </table>

      <br />

      <a
        href={`${API}/static/attendance.csv`}
        download
      >

        <button
          style={{
            padding: "10px 20px",
            fontSize: "16px"
          }}
        >

          Download Attendance CSV

        </button>

      </a>

      <br /><br />

      <h2>
        Detection Result
      </h2>

      {
        resultImage &&
        (
          <img
            src={resultImage}
            alt="result"
            width="700"
            style={{
              border: "3px solid green",
              borderRadius: "10px"
            }}
          />
        )
      }

      <canvas
        ref={canvasRef}
        style={{
          display: "none"
        }}
      />

    </div>
  );
}

export default App;