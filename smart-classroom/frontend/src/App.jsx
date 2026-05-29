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

      alert(
        "Error processing attendance"
      );
    }

    setLoading(false);
  };

  return (

    <div
      style={{
        fontFamily: "Arial",
        background: "#f4f6f9",
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "30px"
      }}
    >

      <div
        style={{
          width: "100%",
          maxWidth: "900px",
          background: "white",
          padding: "30px",
          borderRadius: "20px",
          boxShadow: "0px 4px 20px rgba(0,0,0,0.1)",
          textAlign: "center"
        }}
      >

        <h1
          style={{
            marginBottom: "25px",
            color: "#222"
          }}
        >
          Smart Classroom Attendance
        </h1>

        <video
          ref={videoRef}
          autoPlay
          playsInline
          width="700"
          style={{
            width: "100%",
            maxWidth: "700px",
            borderRadius: "15px",
            border: "4px solid #222",
            marginBottom: "20px"
          }}
        />

        <br />

        <button
          onClick={captureAttendance}
          style={{
            padding: "14px 28px",
            fontSize: "18px",
            border: "none",
            borderRadius: "10px",
            background: "#2563eb",
            color: "white",
            cursor: "pointer",
            fontWeight: "bold",
            marginBottom: "25px",
            transition: "0.2s"
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

        <h2
          style={{
            color: "#111"
          }}
        >
          Present Students: {count}
        </h2>

        <div
          style={{
            overflowX: "auto",
            marginTop: "20px"
          }}
        >

          <table
            style={{
              margin: "0 auto",
              borderCollapse: "collapse",
              width: "100%",
              maxWidth: "500px",
              background: "white"
            }}
          >

            <thead>

              <tr
                style={{
                  background: "#2563eb",
                  color: "white"
                }}
              >

                <th
                  style={{
                    padding: "12px",
                    border: "1px solid #ddd"
                  }}
                >
                  Student Name
                </th>

              </tr>

            </thead>

            <tbody>

              {
                students.length > 0
                ?
                students.map(
                  (
                    s,
                    i
                  ) => (

                    <tr key={i}>

                      <td
                        style={{
                          padding: "12px",
                          border: "1px solid #ddd"
                        }}
                      >
                        {s}
                      </td>

                    </tr>
                  )
                )
                :
                (
                  <tr>

                    <td
                      style={{
                        padding: "12px",
                        border: "1px solid #ddd"
                      }}
                    >
                      No students detected
                    </td>

                  </tr>
                )
              }

            </tbody>

          </table>

        </div>

        <br />

        <a
          href={`${API}/download`}
          target="_blank"
          rel="noreferrer"
          style={{
            textDecoration: "none"
          }}
        >

          <button
            style={{
              padding: "12px 24px",
              fontSize: "16px",
              border: "none",
              borderRadius: "10px",
              background: "#16a34a",
              color: "white",
              cursor: "pointer",
              fontWeight: "bold"
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
              style={{
                width: "100%",
                maxWidth: "700px",
                border: "4px solid #16a34a",
                borderRadius: "15px",
                marginTop: "15px"
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

    </div>
  );
}

export default App;