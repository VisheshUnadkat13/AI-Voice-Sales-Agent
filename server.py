import os
import uuid
import tempfile
import shutil

from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from llm_client import chat
from prompts import build_agent_system_prompt
from stt_client import transcribe
from tts_client import synthesize
from excel_manager import get_next_pending_lead, update_lead_record
from summarizer import summarize_call

app = FastAPI(title="AI Voice Sales Agent - Phase 2")

TMP_DIR = tempfile.mkdtemp(prefix="voice_agent_")
SESSIONS: dict[str, dict] = {}  # session_id -> {messages, lead, row, transcript_lines}

CLOSING_PHRASES = ["have a great day", "thanks again for your time", "goodbye"]


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html") as f:
        return f.read()


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/api/start_call")
def start_call():
    result = get_next_pending_lead()
    if result is None:
        raise HTTPException(404, "No pending leads left in the CRM.")
    row, lead = result

    with open("data/knowledge_base.md") as f:
        kb = f.read()

    system_prompt = build_agent_system_prompt(
        lead_name=lead["Name"], company=lead["Company"], knowledge_base=kb
    )
    messages = [{"role": "system", "content": system_prompt}]
    opening = chat(messages + [{"role": "user", "content": "[Call connected. Begin the call.]"}])
    messages.append({"role": "assistant", "content": opening})

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "messages": messages,
        "lead": lead,
        "row": row,
        "transcript_lines": [f"Agent: {opening}"],
        "ended": False,
    }

    audio_path = os.path.join(TMP_DIR, f"{session_id}_opening.mp3")
    synthesize(opening, audio_path)

    return {
        "session_id": session_id,
        "lead_name": lead["Name"],
        "company": lead["Company"],
        "agent_text": opening,
        "audio_url": f"/api/audio/{session_id}_opening.mp3",
    }


@app.post("/api/turn")
async def turn(session_id: str = Form(...), audio: UploadFile = None):
    session = SESSIONS.get(session_id)
    if not session or session["ended"]:
        raise HTTPException(400, "Invalid or ended session.")

    in_path = os.path.join(TMP_DIR, f"{session_id}_in_{uuid.uuid4().hex}.webm")
    with open(in_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    lead_text = transcribe(in_path)
    session["transcript_lines"].append(f"Lead: {lead_text}")
    session["messages"].append({"role": "user", "content": lead_text})

    reply = chat(session["messages"])
    session["messages"].append({"role": "assistant", "content": reply})
    session["transcript_lines"].append(f"Agent: {reply}")

    call_should_end = any(p in reply.lower() for p in CLOSING_PHRASES)

    out_name = f"{session_id}_{uuid.uuid4().hex}.mp3"
    out_path = os.path.join(TMP_DIR, out_name)
    synthesize(reply, out_path)

    return {
        "lead_text": lead_text,
        "agent_text": reply,
        "audio_url": f"/api/audio/{out_name}",
        "call_should_end": call_should_end,
    }


@app.post("/api/end_call")
def end_call(session_id: str = Form(...)):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(400, "Invalid session.")
    if session["ended"]:
        return {"status": "already ended"}

    session["ended"] = True
    transcript = "\n".join(session["transcript_lines"])
    summary = summarize_call(transcript)
    update_lead_record(session["row"], summary)

    return {"status": "ok", "summary": summary}


@app.get("/api/audio/{filename}")
def get_audio(filename: str):
    path = os.path.join(TMP_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Audio not found.")
    return FileResponse(path, media_type="audio/mpeg")
