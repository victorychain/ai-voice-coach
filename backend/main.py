"""
FastAPI backend for the Vocal Critic tool.
Handles audio uploads and Music Flamingo inference.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed audio formats
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

app = FastAPI(
    title="Vocal Critic API",
    description="AI-powered vocal performance analysis using Music Flamingo",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
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


# Store for async job results
critique_results: dict = {}


def cleanup_file(file_path: str):
    """Remove uploaded file after processing."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up file: {e}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API and model health status."""
    from model import check_model_status
    
    model_status = check_model_status()
    return {
        "status": "healthy",
        "model_status": model_status,
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file for analysis.
    Supported formats: WAV, MP3, FLAC, M4A, OGG
    Max size: 100MB
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique ID
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Check file size
    if file_path.stat().st_size > MAX_FILE_SIZE:
        file_path.unlink()
        raise HTTPException(status_code=400, detail="File too large. Max size: 100MB")
    
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
    """
    Start vocal analysis on an uploaded file.
    
    Args:
        file_id: ID from upload response
        analysis_type: "comprehensive" or "detailed"
    """
    # Find the uploaded file
    matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found. Please upload first.")
    
    file_path = matching_files[0]
    
    # Initialize result
    critique_results[file_id] = {
        "id": file_id,
        "status": "processing",
        "type": analysis_type,
        "audio_file": file_path.name,
    }
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis_task,
        file_id,
        str(file_path),
        analysis_type,
    )
    
    return CritiqueResponse(**critique_results[file_id])


async def run_analysis_task(file_id: str, file_path: str, analysis_type: str):
    """Background task to run the vocal analysis."""
    try:
        from model import run_comprehensive_critique, run_detailed_critique
        
        if analysis_type == "detailed":
            result = run_detailed_critique(file_path)
        else:
            result = run_comprehensive_critique(file_path)
        
        critique_results[file_id].update({
            "status": "completed",
            **result,
        })
        
    except Exception as e:
        critique_results[file_id].update({
            "status": "error",
            "error": str(e),
        })
    
    finally:
        # Cleanup uploaded file
        cleanup_file(file_path)


@app.get("/result/{file_id}", response_model=CritiqueResponse)
async def get_result(file_id: str):
    """Get the analysis result for a file."""
    if file_id not in critique_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return CritiqueResponse(**critique_results[file_id])


@app.post("/analyze-sync")
async def analyze_sync(file: UploadFile = File(...), analysis_type: str = "comprehensive"):
    """
    Synchronous endpoint that uploads and analyzes in one request.
    Use for smaller files when you can wait for the result.
    """
    import traceback
    
    # Validate file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Save temporarily
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Run analysis
        from model import run_comprehensive_critique, run_detailed_critique
        
        if analysis_type == "detailed":
            result = run_detailed_critique(str(file_path))
        else:
            result = run_comprehensive_critique(str(file_path))
        
        return {
            "id": file_id,
            "status": "completed",
            **result,
        }
        
    except Exception as e:
        # Print full traceback to console
        print("=" * 50)
        print("ERROR in analyze_sync:")
        traceback.print_exc()
        print("=" * 50)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        cleanup_file(str(file_path))


@app.delete("/cleanup/{file_id}")
async def cleanup_upload(file_id: str):
    """Manually cleanup an uploaded file."""
    matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    
    for f in matching_files:
        f.unlink()
    
    if file_id in critique_results:
        del critique_results[file_id]
    
    return {"message": "Cleaned up", "id": file_id}


# Development server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

