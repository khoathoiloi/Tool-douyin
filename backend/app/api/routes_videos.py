import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.models import Video, Job
from ..core.config import settings
from ..worker.job_runner import PipelineJobRunner

router = APIRouter()

@router.post("/videos")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_hint: str = Form(""),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db)
):
    # Validation: extension
    filename = file.filename or "uploaded_video.mp4"
    ext = filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format .{ext}. Allowed: {settings.ALLOWED_EXTENSIONS}")

    video_id = str(uuid.uuid4())
    save_filename = f"{video_id}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    # Save file asynchronously
    async with aiofiles.open(save_path, "wb") as out_file:
        content = await file.read()
        if len(content) > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size ({settings.MAX_VIDEO_SIZE_MB}MB)")
        await out_file.write(content)

    video = Video(
        id=video_id,
        filename=filename,
        file_path=save_path,
        filesize=len(content)
    )
    db.add(video)

    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        video_id=video_id,
        stage="queued",
        status="pending",
        progress_percent=0
    )
    db.add(job)
    db.commit()

    if auto_process:
        # Launch pipeline in background task without blocking HTTP request
        background_tasks.add_task(PipelineJobRunner.run_full_pipeline, video_id, job_id, db, user_hint)

    return {
        "success": True,
        "video_id": video_id,
        "job_id": job_id,
        "filename": filename,
        "filesize": len(content),
        "status": "queued"
    }

@router.get("/videos/{video_id}")
def get_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {
        "id": video.id,
        "filename": video.filename,
        "filesize": video.filesize,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "created_at": video.created_at.isoformat() if video.created_at else ""
    }
