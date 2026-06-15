from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
import google.generativeai as genai
import subprocess
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

app = FastAPI(title="LEO Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"  # default to python

@app.get("/")
def root():
    return {"status": "LEO backend is alive 🐐"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        response = model.generate_content(req.message)
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute")
def execute(req: ExecuteRequest):
    try:
        # Write code to a temp file
        suffix = ".py" if req.language == "python" else ".js"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False
        ) as f:
            f.write(req.code)
            tmp_path = f.name

        # Run inside Docker sandbox
        filename = os.path.basename(tmp_path)
        if req.language == "python":
            cmd = f"docker run --rm -v {tmp_path}:/workspace/{filename} leo-sandbox python3 /workspace/{filename}"
        else:
            cmd = f"docker run --rm -v {tmp_path}:/workspace/{filename} leo-sandbox node /workspace/{filename}"

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30  # kill if takes longer than 30s
        )

        os.unlink(tmp_path)  # cleanup temp file

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "success": result.returncode == 0
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Code execution timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))