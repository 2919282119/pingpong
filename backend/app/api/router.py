import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from app.api.deps import get_current_user
from app.config import TEMP_DIR, ACTION_TYPES
from app.models.db import User
from app.services.analysis_manager import AnalysisManager

logger = logging.getLogger(__name__)
router = APIRouter()

# Global analysis manager
_manager = AnalysisManager()

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


@router.post("/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    action_type: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """Upload video and start async analysis. Returns task ID immediately."""
    if action_type not in ACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action_type '{action_type}'. Must be one of: {', '.join(ACTION_TYPES)}",
        )

    ext = Path(video.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    temp_path = TEMP_DIR / f"upload_{id(video)}{ext}"
    content = await video.read()
    temp_path.write_bytes(content)
    logger.info("Saved upload: %s, type=%s (%d bytes)",
                temp_path, action_type, len(content))

    task_id = _manager.create_task(str(temp_path), action_type, current_user.id)
    return {"task_id": task_id}


@router.get("/analyze/{task_id}")
async def get_analysis(task_id: str, current_user: User = Depends(get_current_user)):
    """Poll analysis status and result."""
    task = _manager.get_task(task_id, current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/analyze/history/list")
async def get_history(current_user: User = Depends(get_current_user)):
    """Get list of completed analyses for the current user."""
    return {"history": _manager.get_history(current_user.id)}


@router.delete("/analyze/history")
async def delete_history(current_user: User = Depends(get_current_user)):
    """Clear the current user's analysis history."""
    _manager.clear_history(current_user.id)
    return {"status": "ok"}
