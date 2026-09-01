import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.models import Video, Job
from ..worker.job_runner import PipelineJobRunner

router = APIRouter()

class ProcessRequest(BaseModel):
    user_hint: str = ""

@router.post("/videos/{video_id}/process")
def trigger_process_pipeline(
    video_id: str,
    background_tasks: BackgroundTasks,
    body: ProcessRequest = ProcessRequest(),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

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

    background_tasks.add_task(PipelineJobRunner.run_full_pipeline, video_id, job_id, db, body.user_hint)

    return {
        "success": True,
        "video_id": video_id,
        "job_id": job_id,
        "status": "queued"
    }
