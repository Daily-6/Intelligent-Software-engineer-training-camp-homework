from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import threading
import uuid
import os

from harness.core.loop import AgentLoop
from harness.core.llm import MockLLMClient
from harness.core.action import Action
from harness.tools.dispatcher import ToolDispatcher
from harness.tools.file_tools import read_file, write_file, list_dir
from harness.governance.middleware import GovernanceMiddleware
from harness.governance.guardrail import Rule
from harness.config import Config, SandboxConfig
from harness.memory.store import MemoryStore


class TaskRequest(BaseModel):
    task: str


class DenyRequest(BaseModel):
    reason: str = ""


_sessions = {}
_lock = threading.Lock()


def _create_loop(config: Config) -> AgentLoop:
    root = config.project_root
    os.makedirs(root, exist_ok=True)
    script = [Action(tool_name="finish", args={}, thought="done")]
    llm = MockLLMClient(script)
    dispatcher = ToolDispatcher()
    dispatcher.register("read_file", lambda args, ctx: read_file(args["path"], root))
    dispatcher.register("write_file", lambda args, ctx: write_file(args["path"], args["content"], root))
    dispatcher.register("list_dir", lambda args, ctx: list_dir(args["path"], root))
    dispatcher.register("finish", lambda args, ctx: type("R", (), {"success": True, "output": "finished", "error": ""})())
    rules = [
        Rule(pattern=r"rm\s+-rf\s+/", severity="deny", tool="execute_shell", description="rm -rf"),
        Rule(pattern=r"git\s+push", severity="require_approval", tool="execute_shell", description="git push"),
    ]
    mw = GovernanceMiddleware(rules=rules, sandbox_config=config.sandbox, project_root=root, readonly_paths=[".git/"])
    memory = MemoryStore()
    return AgentLoop(llm=llm, dispatcher=dispatcher, governance=mw, memory=memory, config=config)


def create_app(config: Config = None) -> FastAPI:
    if config is None:
        config = Config.default()
    app = FastAPI(title="Coding Agent Harness")

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "<html><body><h1>Coding Agent Harness</h1><p>WebUI loading...</p></body></html>"

    @app.post("/api/sessions")
    async def create_session(req: TaskRequest):
        sid = str(uuid.uuid4())[:8]
        loop = _create_loop(config)
        with _lock:
            _sessions[sid] = {"loop": loop, "session": None, "status": "running"}
        def run_task():
            session = loop.run(req.task)
            with _lock:
                _sessions[sid]["session"] = session
                _sessions[sid]["status"] = session.status
        t = threading.Thread(target=run_task, daemon=True)
        t.start()
        return {"id": sid, "status": "running", "task": req.task}

    @app.get("/api/sessions/{sid}")
    async def get_session(sid: str):
        with _lock:
            if sid not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            data = _sessions[sid]
        session = data.get("session")
        if session:
            return {
                "id": sid,
                "task": session.task,
                "status": session.status,
                "turns": [
                    {"action": {"tool_name": t.action.tool_name, "args": t.action.args, "thought": t.action.thought},
                     "governance": {"blocked": t.governance_result.blocked, "reason": t.governance_result.reason} if t.governance_result else None,
                     "timestamp": t.timestamp}
                    for t in session.turns
                ],
            }
        return {"id": sid, "status": data["status"], "turns": []}

    @app.post("/api/sessions/{sid}/approve")
    async def approve_action(sid: str):
        with _lock:
            if sid not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            loop = _sessions[sid]["loop"]
        if not loop._governance.is_pending():
            raise HTTPException(status_code=409, detail="No pending approval")
        loop._governance.approve()
        return {"status": "approved"}

    @app.post("/api/sessions/{sid}/deny")
    async def deny_action(sid: str, req: DenyRequest = None):
        with _lock:
            if sid not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            loop = _sessions[sid]["loop"]
        if not loop._governance.is_pending():
            raise HTTPException(status_code=409, detail="No pending approval")
        reason = req.reason if req else ""
        loop._governance.deny(reason)
        return {"status": "denied", "reason": reason}

    @app.post("/api/sessions/{sid}/stop")
    async def stop_session(sid: str):
        with _lock:
            if sid not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            loop = _sessions[sid]["loop"]
        loop.stop()
        return {"status": "stopped"}

    @app.websocket("/ws/sessions/{sid}")
    async def ws_session(ws: WebSocket, sid: str):
        await ws.accept()
        with _lock:
            if sid not in _sessions:
                await ws.close(code=404)
                return
        import asyncio
        while True:
            with _lock:
                data = _sessions.get(sid, {})
                session = data.get("session")
                status = data.get("status", "running")
            if session:
                await ws.send_json({
                    "id": session.id,
                    "status": session.status,
                    "turns_count": len(session.turns),
                })
                if session.status in ("completed", "stopped", "error"):
                    await ws.close()
                    break
            else:
                await ws.send_json({"id": sid, "status": status, "turns_count": 0})
            await asyncio.sleep(1)

    return app


app = create_app()
