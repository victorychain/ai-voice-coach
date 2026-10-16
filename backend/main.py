"""
Local Vocal Critic + Music Flamingo API.

Serves the frontend and runs NVIDIA Music Flamingo on the workstation GPU.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import traceback
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from model import (
    check_model_status,
    run_comprehensive_critique,
    run_detailed_critique,
    run_prompt_analysis,
    stream_vocal,
    warmup_in_background,
)
from prompts import get_critique_conversation, list_prompt_modes

STATIC_DIR = BACKEND_DIR / "static"
UPLOAD_DIR = BACKEND_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
MAX_FILE_SIZE = 100 * 1024 * 1024

@asynccontextmanager
async def lifespan(_app: FastAPI):
    warmup_in_background()
    yield


app = FastAPI(
    title="Vocal Critic + Music Flamingo",
    description="Local music understanding and vocal coaching on Music Flamingo",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CritiqueResponse(BaseModel):
    id: str
    status: str
    type: str
    audio_file: str
    analysis: Optional[str] = None
    aspects: Optional[dict] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_status: dict


class UploadResponse(BaseModel):
    id: str
    filename: str
    message: str


critique_results: dict = {}


def cleanup_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as exc:
        print(f"Error cleaning up file: {exc}")


def _save_upload(file: UploadFile) -> tuple[str, Path]:
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    if file_path.stat().st_size > MAX_FILE_SIZE:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="File too large. Max size: 100MB")
    return file_id, file_path


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok", "model_status": check_model_status()}


@app.get("/prompts")
async def prompts():
    return {"modes": list_prompt_modes()}


@app.post("/upload", response_model=UploadResponse)
async def upload_audio(file: UploadFile = File(...)):
    file_id, _ = _save_upload(file)
    return {
        "id": file_id,
        "filename": file.filename,
        "message": "File uploaded successfully. Use /analyze to start analysis.",
    }


@app.post("/analyze/{file_id}", response_model=CritiqueResponse)
async def analyze_audio(
    file_id: str,
    background_tasks: BackgroundTasks,
    analysis_type: str = "comprehensive",
):
    matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found. Please upload first.")

    file_path = matching_files[0]
    critique_results[file_id] = {
        "id": file_id,
        "status": "processing",
        "type": analysis_type,
        "audio_file": file_path.name,
    }
    background_tasks.add_task(run_analysis_task, file_id, str(file_path), analysis_type)
    return CritiqueResponse(**critique_results[file_id])


def run_analysis_task(file_id: str, file_path: str, analysis_type: str):
    try:
        if analysis_type == "detailed":
            result = run_detailed_critique(file_path)
        else:
            result = run_prompt_analysis(file_path, mode=analysis_type)
        critique_results[file_id].update({"status": "completed", **result})
    except Exception as exc:
        critique_results[file_id].update({"status": "error", "error": str(exc)})
    finally:
        cleanup_file(file_path)


@app.get("/result/{file_id}", response_model=CritiqueResponse)
async def get_result(file_id: str):
    if file_id not in critique_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return CritiqueResponse(**critique_results[file_id])


@app.post("/analyze-sync")
async def analyze_sync(
    file: UploadFile = File(...),
    analysis_type: str = "comprehensive",
    prompt: Optional[str] = None,
):
    file_id, file_path = _save_upload(file)
    try:
        if analysis_type == "detailed":
            result = run_detailed_critique(str(file_path))
        else:
            result = run_prompt_analysis(str(file_path), mode=analysis_type, custom_prompt=prompt)
        return {"id": file_id, "status": "completed", **result}
    except Exception as exc:
        print("=" * 50)
        print("ERROR in analyze_sync:")
        traceback.print_exc()
        print("=" * 50)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}")
    finally:
        cleanup_file(str(file_path))


@app.post("/analyze-stream")
async def analyze_stream(
    file: UploadFile = File(...),
    analysis_type: str = "comprehensive",
    prompt: Optional[str] = None,
):
    file_id, file_path = _save_upload(file)

    def event_stream():
        try:
            conversation = get_critique_conversation(
                str(file_path),
                mode=analysis_type,
                custom_prompt=prompt,
            )
            yield f"data: {json.dumps({'status': 'generating', 'id': file_id})}\n\n"

            from queue import Queue
            from threading import Thread

            queue: Queue = Queue()

            def produce():
                try:
                    text = stream_vocal(
                        str(file_path),
                        conversation,
                        on_token=lambda piece: queue.put(("token", piece)),
                    )
                    queue.put(("done", text))
                except Exception as exc:
                    queue.put(("error", str(exc)))

            Thread(target=produce, daemon=True).start()
            while True:
                kind, payload = queue.get()
                if kind == "token":
                    yield f"data: {json.dumps({'token': payload})}\n\n"
                elif kind == "done":
                    yield f"data: {json.dumps({'done': True, 'analysis': payload, 'id': file_id, 'type': analysis_type})}\n\n"
                    break
                else:
                    yield f"data: {json.dumps({'error': payload})}\n\n"
                    break
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            cleanup_file(str(file_path))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.delete("/cleanup/{file_id}")
async def cleanup_upload(file_id: str):
    matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    for path in matching_files:
        path.unlink(missing_ok=True)
    critique_results.pop(file_id, None)
    return {"message": "Cleaned up", "id": file_id}


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.svg")
async def favicon():
    favicon = STATIC_DIR / "favicon.svg"
    if not favicon.exists():
        raise HTTPException(status_code=404, detail="Favicon not found")
    return FileResponse(favicon)


if (STATIC_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
