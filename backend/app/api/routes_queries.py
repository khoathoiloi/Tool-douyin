import json
import uuid
from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.models import SearchQuery, Video, VideoAnalysis
from ..pipeline.query_generator import QueryGenerator
from ..core.config import settings

router = APIRouter()

class CustomQueryCreate(BaseModel):
    query: str
    category: str = "core_topic"

class QueryToggleUpdate(BaseModel):
    is_enabled: bool

@router.get("/videos/{video_id}/queries")
def get_queries(video_id: str, db: Session = Depends(get_db)):
    queries = db.query(SearchQuery).filter(SearchQuery.video_id == video_id).all()
    results = []
    for q in queries:
        variants = []
        try:
            variants = json.loads(q.expanded_variants)
        except Exception:
            pass
        results.append({
            "id": q.id,
            "query": q.query,
            "category": q.category,
            "reason": q.reason,
            "score": q.score,
            "is_enabled": q.is_enabled,
            "is_custom": q.is_custom,
            "variants": variants
        })
    return {"queries": results}

@router.post("/videos/{video_id}/queries")
def generate_or_regenerate_queries(video_id: str, db: Session = Depends(get_db)):
    analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video_id).first()
    if not analysis:
        raise HTTPException(status_code=400, detail="Run analysis first before generating queries")
        
    profile = analysis.to_profile_dict()
    raw_queries = QueryGenerator.generate_20_queries(profile, api_key=settings.GEMINI_API_KEY)
    
    db.query(SearchQuery).filter(SearchQuery.video_id == video_id).delete()
    saved = []
    for q in raw_queries:
        variants = QueryGenerator.expand_query(q["query"])
        sq = SearchQuery(
            id=str(uuid.uuid4()),
            video_id=video_id,
            query=q["query"],
            category=q.get("category", "core_topic"),
            reason=q.get("reason", ""),
            score=float(q.get("score", 0.9)),
            is_enabled=True,
            is_custom=False,
            expanded_variants=json.dumps(variants, ensure_ascii=False)
        )
        db.add(sq)
        saved.append(sq)
    db.commit()
    return {"success": True, "count": len(saved)}

@router.post("/videos/{video_id}/queries/custom")
def add_custom_query(video_id: str, body: CustomQueryCreate, db: Session = Depends(get_db)):
    variants = QueryGenerator.expand_query(body.query)
    sq = SearchQuery(
        id=str(uuid.uuid4()),
        video_id=video_id,
        query=body.query.strip(),
        category=body.category,
        reason="Custom user query",
        score=1.0,
        is_enabled=True,
        is_custom=True,
        expanded_variants=json.dumps(variants, ensure_ascii=False)
    )
    db.add(sq)
    db.commit()
    return {"success": True, "id": sq.id}

@router.patch("/videos/{video_id}/queries/{query_id}")
def update_query_status(video_id: str, query_id: str, body: QueryToggleUpdate, db: Session = Depends(get_db)):
    sq = db.query(SearchQuery).filter(SearchQuery.id == query_id, SearchQuery.video_id == video_id).first()
    if not sq:
        raise HTTPException(status_code=404, detail="Query not found")
    sq.is_enabled = body.is_enabled
    db.commit()
    return {"success": True, "is_enabled": sq.is_enabled}
