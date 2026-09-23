from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
import google.generativeai as genai
import jwt as pyjwt
import os
from dotenv import load_dotenv
from tools import TOOLS, TOOL_DESCRIPTIONS
from agent import run_agent
from context_engine import build_context, format_context_for_prompt
from tools.file_tools import get_file_tree, get_file_content
from tools.shell_tools import run_python_streaming
from storage import get_file_url, download_file, IS_PRODUCTION
from memory import memory_stats
from evals.runner import run_single_eval, run_all_evals
from evals.test_cases import TEST_CASES
from rate_limiter import check_rate_limit, rate_limit_status
from sse_starlette.sse import EventSourceResponse
from agent_streaming import run_agent_streaming
from checkpoints import list_checkpoints, load_checkpoint, delete_checkpoint
from multi_agent import run_multi_agent
from analytics import (
    get_overview, get_daily_activity, get_top_tools,
    get_recent_tasks, get_language_breakdown,
)
from keepalive import start_keepalive

load_dotenv()

NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-lite-latest")

app = FastAPI(title="LEO Agent API")

_default_origins = [
    "http://localhost:3000", "http://localhost:3001",
    "http://127.0.0.1:3000", "http://127.0.0.1:3001",
]
_frontend_url = os.getenv("FRONTEND_URL")
allow_origins = _default_origins + [_frontend_url] if _frontend_url else _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    filename: str = None

class ExplainRequest(BaseModel):
    code: str
    filename: str = "unknown"
    task: str = ""
    user_id: str = "anonymous"

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

class ResumeRequest(BaseModel):
    checkpoint_id: str
    user_id: str = "anonymous"
    additional_steps: int = 20

class MultiAgentRequest(BaseModel):
    task: str
    user_id: str = "anonymous"

@app.on_event("startup")
def on_startup():
    start_keepalive()


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
    from tools.shell_tools import run_code
    return run_code(req.code, req.language, req.filename)

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

@app.post("/agent/multi")
async def multi_agent(req: MultiAgentRequest):
    try:
        check_rate_limit(req.user_id)
        context = format_context_for_prompt(req.user_id)
        result = await run_multi_agent(req.task, req.user_id, context)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File, Form

@app.post("/agent/with-file")
async def agent_with_file(
    task: str = Form(...),
    user_id: str = Form(default="anonymous"),
    max_steps: int = Form(default=10),
    file: UploadFile = File(...)
):
    """Run agent with an attached file as context."""
    try:
        check_rate_limit(user_id)

        content = await file.read()
        filename = file.filename or "uploaded_file"
        content_type = file.content_type or ""

        # Decode file content based on type
        file_context = ""

        if content_type.startswith("image/"):
            # Save image to workspace for LEO to reference
            import os
            workspace = f"/tmp/leo_workspace/{user_id}"
            os.makedirs(workspace, exist_ok=True)
            filepath = os.path.join(workspace, filename)
            with open(filepath, "wb") as f:
                f.write(content)
            file_context = f"[Image attached: {filename} — saved to workspace. You can reference it by filename.]"

        elif content_type == "application/pdf":
            # Extract text from PDF
            try:
                import io
                import pypdf
                pdf = pypdf.PdfReader(io.BytesIO(content))
                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                file_context = f"[PDF: {filename}]\n{text[:8000]}"
            except Exception:
                file_context = f"[PDF attached: {filename} — could not extract text]"

        else:
            # Plain text, code, JSON, CSV, markdown etc
            try:
                text = content.decode("utf-8")
                file_context = f"[File: {filename}]\n```\n{text[:8000]}\n```"
            except UnicodeDecodeError:
                file_context = f"[Binary file attached: {filename} — cannot read as text]"

        # Inject file context into the task
        enriched_task = f"{task}\n\nATTACHED FILE CONTEXT:\n{file_context}"

        result = run_agent(enriched_task, max_steps, user_id)
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

@app.get("/checkpoints/{user_id}")
def get_checkpoints(user_id: str):
    return {"checkpoints": list_checkpoints(user_id)}

@app.post("/agent/resume")
def resume_agent(req: ResumeRequest):
    """Resume a paused agent task from a checkpoint."""
    checkpoint = load_checkpoint(req.checkpoint_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    try:
        result = run_agent(
            task=checkpoint["task"],
            max_steps=req.additional_steps,
            user_id=req.user_id,
            checkpoint=checkpoint
        )
        if result.get("final_answer") and not result["final_answer"].startswith("ERROR"):
            delete_checkpoint(req.checkpoint_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain")
async def explain_code(req: ExplainRequest):
    """Stream a plain-English explanation of code LEO generated."""
    from fastapi.responses import StreamingResponse

    prompt = f"""You are LEO, a friendly AI coding agent. A user asked you to complete this task:

Task: {req.task}

You generated this code in a file called {req.filename}:
{req.code}

Now explain this code clearly to the user in plain English. Structure your explanation as:

1. **What it does** — one sentence summary
2. **How it works** — walk through the logic step by step, in plain English, no jargon
3. **Key concepts used** — briefly explain any programming concepts a beginner might not know
4. **Why this approach** — explain why you wrote it this way vs alternatives

Be friendly, clear, and concise. Assume the user is learning."""

    def generate():
        try:
            explain_model = genai.GenerativeModel(
                "gemini-flash-lite-latest",
                generation_config={"temperature": 0.4}
            )
            response = explain_model.generate_content(
                prompt,
                stream=True
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error generating explanation: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/workspace/tree")
def workspace_tree(user_id: str = "anonymous"):
    return get_file_tree(user_id)

@app.get("/workspace/file/{filename:path}")
def workspace_file(filename: str, user_id: str = "anonymous"):
    result = get_file_content(filename, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result

@app.get("/workspace/context")
def workspace_context(user_id: str = "anonymous"):
    return build_context(user_id)


def verify_backend_token(user_id: str, token: str):
    """Verify a short-lived JWT minted by the frontend's /api/backend-token
    route (signed with NEXTAUTH_SECRET after checking the real NextAuth
    session) and confirm it belongs to the requested user_id."""
    if not NEXTAUTH_SECRET:
        raise HTTPException(status_code=500, detail="Server auth not configured")
    try:
        payload = pyjwt.decode(token, NEXTAUTH_SECRET, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Download link expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid download token")

    if payload.get("sub") != user_id:
        raise HTTPException(status_code=403, detail="You can only download your own files")


@app.get("/workspace/download/{filename:path}")
def workspace_download(filename: str, token: str, user_id: str = "anonymous"):
    verify_backend_token(user_id, token)

    if IS_PRODUCTION:
        result = get_file_url(filename, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "File not found"))
        return RedirectResponse(result["url"])

    result = download_file(filename, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "File not found"))

    content = result["content"]
    if isinstance(content, str):
        content = content.encode("utf-8")

    safe_filename = filename.rsplit("/", 1)[-1]
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'},
    )

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


# ── Analytics endpoints ────────────────────────────────────────

@app.get("/analytics/overview")
def analytics_overview(user_id: str = "anonymous", days: int = 30):
    return get_overview(user_id, days)


@app.get("/analytics/daily")
def analytics_daily(user_id: str = "anonymous", days: int = 14):
    return {"data": get_daily_activity(user_id, days)}


@app.get("/analytics/tools")
def analytics_tools(user_id: str = "anonymous", days: int = 30):
    return {"tools": get_top_tools(user_id, days)}


@app.get("/analytics/tasks")
def analytics_tasks(user_id: str = "anonymous", limit: int = 20):
    return {"tasks": get_recent_tasks(user_id, limit)}


@app.get("/analytics/languages")
def analytics_languages(user_id: str = "anonymous", days: int = 30):
    return {"languages": get_language_breakdown(user_id, days)}