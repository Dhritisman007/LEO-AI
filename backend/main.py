from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
import google.generativeai as genai
import os
from dotenv import load_dotenv
from tools import TOOLS, TOOL_DESCRIPTIONS
from agent import run_agent
from tools.file_tools import get_file_tree, get_file_content
from tools.shell_tools import run_python_streaming
from memory import memory_stats
from evals.runner import run_single_eval, run_all_evals
from evals.test_cases import TEST_CASES
from rate_limiter import check_rate_limit, rate_limit_status
from sse_starlette.sse import EventSourceResponse
from agent_streaming import run_agent_streaming

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-lite-latest")

app = FastAPI(title="LEO Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
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

class AgentRequest(BaseModel):
    task: str
    max_steps: int = 10
    user_id: str = "anonymous"

class EvalRequest(BaseModel):
    categories: list = None
    user_id: str = "eval_user"

class SingleEvalRequest(BaseModel):
    test_id: str
    user_id: str = "eval_user"

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

@app.post("/agent")
def agent(req: AgentRequest):
    try:
        check_rate_limit(req.user_id)  # raises 429 if over limit
        result = run_agent(req.task, req.max_steps, req.user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/stream")
async def agent_stream(task: str, user_id: str = "anonymous", max_steps: int = 10):
    try:
        check_rate_limit(user_id)
    except HTTPException:
        raise

    async def event_generator():
        async for chunk in run_agent_streaming(task, max_steps, user_id):
            yield chunk

    return EventSourceResponse(event_generator())

@app.get("/workspace/tree")
def workspace_tree(user_id: str = "anonymous"):
    return get_file_tree(user_id)

@app.get("/workspace/file/{filename:path}")
def workspace_file(filename: str, user_id: str = "anonymous"):
    result = get_file_content(filename, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result

@app.get("/memory/stats")
def get_memory_stats(user_id: str = "anonymous"):
    return memory_stats(user_id)

@app.get("/rate-limit/{user_id}")
def get_rate_limit(user_id: str):
    return rate_limit_status(user_id)


@app.get("/evals/cases")
def list_eval_cases():
    """List all available test cases."""
    return {
        "total": len(TEST_CASES),
        "cases": [
            {"id": c["id"], "category": c["category"], "task": c["task"][:80]}
            for c in TEST_CASES
        ]
    }

@app.post("/evals/run")
def run_evals(req: EvalRequest):
    """Run all evals (optionally filtered by category)."""
    try:
        summary = run_all_evals(
            categories=req.categories,
            user_id=req.user_id
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evals/run-one")
def run_one_eval(req: SingleEvalRequest):
    """Run a single eval by id."""
    case = next((c for c in TEST_CASES if c["id"] == req.test_id), None)
    if not case:
        raise HTTPException(status_code=404, detail=f"Test case '{req.test_id}' not found")
    try:
        result = run_single_eval(case, user_id=req.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/execute")
async def websocket_execute(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            code = data.get("code", "")
            if not code:
                await websocket.send_json({"type": "error", "content": "No code provided"})
                continue
            await run_python_streaming(code, websocket)
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")