import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.models import SearchResult, Video

router = APIRouter()

@router.get("/videos/{video_id}/results")
def get_search_results(video_id: str, db: Session = Depends(get_db)):
    results = db.query(SearchResult).filter(SearchResult.video_id == video_id).order_by(SearchResult.final_score.desc()).all()
    output = []
    for r in results:
        hashtags = []
        try:
            hashtags = json.loads(r.hashtags)
        except Exception:
            pass
        output.append({
            "id": r.id,
            "platform": r.platform,
            "video_id": r.remote_video_id,
            "url": r.url,
            "author": r.author,
            "title": r.title,
            "description": r.description,
            "hashtags": hashtags,
            "cover_url": r.cover_url,
            "publish_time": r.publish_time,
            "like_count": r.like_count,
            "comment_count": r.comment_count,
            "share_count": r.share_count,
            "search_query": r.search_query,
            "relevance_score": r.relevance_score,
            "final_score": r.final_score
        })
    return {"results": output, "count": len(output)}
