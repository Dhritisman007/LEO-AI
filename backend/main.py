from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
import google.generativeai as genai
import os
from dotenv import load_dotenv
from tools import TOOLS, TOOL_DESCRIPTIONS

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
    language: str = "python"

class ToolRequest(BaseModel):
    tool: str
    params: dict = {}

@app.get("/")
def root():
    return {"status": "LEO backend is alive 🐐"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tools")
def get_tools():
    return {"tools": TOOL_DESCRIPTIONS}

@app.post("/tools/run")
def run_tool(req: ToolRequest):
    if req.tool not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool '{req.tool}' not found")
    try:
        result = TOOLS[req.tool](**req.params)
        return result
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        response = model.generate_content(req.message)
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute")
def execute(req: ExecuteRequest):
    from tools.shell_tools import run_python, run_shell
    if req.language == "python":
        return run_python(req.code)
    else:
        return run_shell(req.code)