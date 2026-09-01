from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.models import VideoAnalysis

router = APIRouter()

@router.get("/videos/{video_id}/analysis")
def get_video_analysis(video_id: str, db: Session = Depends(get_db)):
    analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Video analysis profile not found or still processing")
    return analysis.to_profile_dict()
