import os
import uuid
import json
import aiofiles
from pydantic import BaseModel
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Video, VideoAnalysis, SearchQuery, SearchResult, Job
from ..core.config import settings
from ..douyin.url_parser import DouyinUrlParser
from ..worker.job_runner import PipelineJobRunner
from ..providers.factory import get_search_provider
from ..ranking.scoring import MultiLayerScoringEngine
from ..ranking.filters import AdvancedResultFilter
from ..pipeline.deduplicator import Deduplicator

from ..smart_search.smart_search_service import SmartSearchService
from ..smart_search.chinese_query_generator import ChineseQueryGenerator
from ..smart_search.language_detector import LanguageDetector

router = APIRouter(prefix="/v1")

# Models
class SmartTranslateRequest(BaseModel):
    query: str
    language: Optional[str] = "auto"
    mode: Optional[str] = "normal"

class SmartSearchRequest(BaseModel):
    query: str
    language: Optional[str] = "auto"
    mode: Optional[str] = "normal"
    custom_queries: Optional[List[str]] = None
    min_likes: Optional[int] = 0
class UrlSearchRequest(BaseModel):
    url: str
    user_hint: Optional[str] = ""
    deep_search: Optional[bool] = False

class KeywordSearchRequest(BaseModel):
    keyword: str
    deep_search: Optional[bool] = False
    limit: Optional[int] = 20
    min_likes: Optional[int] = 0

# 1. POST /api/v1/search/video (Upload Video for Galaxy S9)
@router.post("/search/video")
async def api_v1_search_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_hint: str = Form(""),
    deep_search: bool = Form(False),
    db: Session = Depends(get_db)
):
    filename = file.filename or "mobile_video.mp4"
    ext = filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_FORMAT", "message": f"Định dạng .{ext} không được hỗ trợ."}})

    video_id = str(uuid.uuid4())
    save_filename = f"{video_id}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    async with aiofiles.open(save_path, "wb") as out_file:
        content = await file.read()
        if len(content) > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail={"error": {"code": "FILE_TOO_LARGE", "message": "Video vượt quá dung lượng cho phép."}})
        await out_file.write(content)

    video = Video(id=video_id, filename=filename, file_path=save_path, filesize=len(content))
    db.add(video)

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, video_id=video_id, stage="queued", status="pending", progress_percent=0)
    db.add(job)
    db.commit()

    background_tasks.add_task(PipelineJobRunner.run_full_pipeline, video_id, job_id, db, user_hint, deep_search)

    return {
        "job_id": job_id,
        "video_id": video_id,
        "status": "queued",
        "message": "Video đã được tải lên thành công, đang xếp hàng xử lý."
    }

# 2. POST /api/v1/search/url (Douyin/TikTok URL for Galaxy S9)
@router.post("/search/url")
async def api_v1_search_url(
    body: UrlSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if not DouyinUrlParser.is_valid_url(body.url):
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_URL", "message": "Đường dẫn không hợp lệ."}})

    meta = DouyinUrlParser.parse_and_fetch_metadata(body.url, settings.UPLOAD_DIR)
    if not meta.get("success", False):
        raise HTTPException(status_code=400, detail={"error": {"code": "METADATA_FETCH_FAILED", "message": "Không thể lấy thông tin từ link này. Vui lòng thử upload video trực tiếp."}})

    video_id = str(uuid.uuid4())
    video_path = meta.get("video_path")
    if not video_path:
        video_path = os.path.join(settings.UPLOAD_DIR, f"{video_id}_placeholder.mp4")
        with open(video_path, "wb") as f:
            f.write(b"")

    video = Video(
        id=video_id,
        filename=f"Douyin_{meta.get('remote_id') or 'link'}.mp4",
        file_path=video_path,
        filesize=os.path.getsize(video_path) if os.path.exists(video_path) else 0
    )
    db.add(video)

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, video_id=video_id, stage="queued", status="pending", progress_percent=0)
    db.add(job)
    db.commit()

    combined_hint = f"{meta.get('title', '')} {body.user_hint or ''}".strip()
    background_tasks.add_task(PipelineJobRunner.run_full_pipeline, video_id, job_id, db, combined_hint, body.deep_search)

    return {
        "job_id": job_id,
        "video_id": video_id,
        "title": meta.get("title"),
        "author": meta.get("author"),
        "cover_url": meta.get("cover_url"),
        "status": "queued"
    }

# 3. POST /api/v1/search/keyword (Direct Keyword Search for Galaxy S9)
@router.post("/search/keyword")
async def api_v1_search_keyword(
    body: KeywordSearchRequest,
    db: Session = Depends(get_db)
):
    kw = body.keyword.strip()
    if not kw:
        raise HTTPException(status_code=400, detail={"error": {"code": "EMPTY_KEYWORD", "message": "Từ khóa tìm kiếm không được để trống."}})

    provider = get_search_provider()
    limit = 50 if body.deep_search else min(50, max(5, body.limit or 20))
    raw_results = await provider.search(kw, limit=limit)

    job_id = str(uuid.uuid4())
    video_id = f"kw_{uuid.uuid4().hex[:8]}"
    video = Video(id=video_id, filename=f"Keyword_{kw}.txt", file_path="", filesize=0)
    db.add(video)

    saved = []
    candidates = []
    for r in raw_results:
        candidates.append({
            "platform": r.platform,
            "remote_video_id": r.video_id,
            "url": r.url,
            "author": r.author,
            "title": r.title,
            "description": r.description,
            "hashtags": r.hashtags,
            "cover_url": r.cover_url,
            "publish_time": r.publish_time,
            "like_count": r.like_count,
            "comment_count": r.comment_count,
            "share_count": r.share_count,
            "search_query": kw,
            "final_score": 0.95 if kw in r.title else 0.85
        })

    unique_cands = Deduplicator.deduplicate(candidates)
    for c in unique_cands:
        if body.min_likes and c.get("like_count", 0) < body.min_likes:
            continue
        sr = SearchResult(
            id=str(uuid.uuid4()),
            video_id=video_id,
            platform=c.get("platform", "douyin"),
            remote_video_id=c.get("remote_video_id"),
            url=c.get("url"),
            author=c.get("author"),
            title=c.get("title"),
            description=c.get("description"),
            hashtags=json.dumps(c.get("hashtags", []), ensure_ascii=False),
            cover_url=c.get("cover_url"),
            publish_time=c.get("publish_time"),
            like_count=c.get("like_count", 0),
            comment_count=c.get("comment_count", 0),
            share_count=c.get("share_count", 0),
            search_query=kw,
            relevance_score=c.get("final_score", 0.9),
            final_score=c.get("final_score", 0.9)
        )
        db.add(sr)
        saved.append(sr)

    db.commit()

    return {
        "job_id": job_id,
        "video_id": video_id,
        "status": "completed",
        "keyword": kw,
        "results_count": len(saved),
        "results": [
            {
                "rank": idx + 1,
                "score": MathRound(s.final_score * 100),
                "match_tier": "Very High Match" if (s.final_score * 100) >= 90 else "High Match",
                "title": s.title,
                "url": s.url,
                "author": s.author,
                "cover_url": s.cover_url,
                "like_count": s.like_count,
                "comment_count": s.comment_count,
                "search_query": s.search_query
            } for idx, s in enumerate(saved)
        ]
    }

def MathRound(val):
    return int(round(val))

# 4. GET /api/v1/search/{job_id} (Poll Status for Galaxy S9)
@router.get("/search/{job_id}")
def api_v1_get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail={"error": {"code": "JOB_NOT_FOUND", "message": "Không tìm thấy phiên xử lý này."}})

    analysis_data = None
    if job.video_id:
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == job.video_id).first()
        if analysis:
            analysis_data = {
                "summary": analysis.summary,
                "main_topic": analysis.main_topic,
                "spoken_language": analysis.spoken_language,
                "transcript": analysis.transcript
            }

    queries = []
    if job.video_id:
        db_queries = db.query(SearchQuery).filter(SearchQuery.video_id == job.video_id).all()
        queries = [q.query for q in db_queries]

    return {
        "job_id": job.id,
        "video_id": job.video_id,
        "stage": job.stage,
        "status": job.status,
        "progress_percent": job.progress_percent,
        "error_message": job.error_message,
        "analysis": analysis_data,
        "queries": queries
    }

# 5. GET /api/v1/search/{job_id}/results (Paginated Results for Galaxy S9)
@router.get("/search/{job_id}/results")
def api_v1_get_job_results(
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_score: float = Query(70.0),
    sort_by: str = Query("similarity"),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail={"error": {"code": "JOB_NOT_FOUND", "message": "Không tìm thấy kết quả của job này."}})

    results = db.query(SearchResult).filter(SearchResult.video_id == job.video_id).order_by(SearchResult.final_score.desc()).all()
    
    formatted = []
    for idx, r in enumerate(results):
        score_pct = int(round((r.final_score or 0.8) * 100))
        tier = "Very High Match" if score_pct >= 90 else ("High Match" if score_pct >= 80 else ("Good Match" if score_pct >= 70 else "Possible Match"))
        formatted.append({
            "rank": idx + 1,
            "score": score_pct,
            "match_tier": tier,
            "video_id": r.remote_video_id,
            "url": r.url,
            "author": r.author,
            "title": r.title,
            "cover_url": r.cover_url,
            "like_count": r.like_count,
            "comment_count": r.comment_count,
            "share_count": r.share_count,
            "search_query": r.search_query
        })

    # Apply score filtering
    filtered = [r for r in formatted if r["score"] >= min_score]

    # Pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = filtered[start_idx:end_idx]

    return {
        "job_id": job.id,
        "video_id": job.video_id,
        "total_results": len(filtered),
        "page": page,
        "page_size": page_size,
        "has_more": end_idx < len(filtered),
        "results": paged_items
    }

# 6. GET /api/v1/history & DELETE /api/v1/history/{id}
@router.get("/history")
def api_v1_get_history(db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.created_at.desc()).limit(30).all()
    history = []
    for v in videos:
        count = db.query(SearchResult).filter(SearchResult.video_id == v.id).count()
        history.append({
            "id": v.id,
            "filename": v.filename,
            "results_count": count,
            "created_at": v.created_at.isoformat() if v.created_at else ""
        })
    return {"history": history}

@router.delete("/history/{video_id}")
def api_v1_delete_history(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        db.delete(video)
        db.commit()
    return {"success": True, "message": "Đã xóa lịch sử tìm kiếm."}

# 7. POST /api/v1/query/translate (Preview & Translate Vietnamese/English queries)
@router.post("/query/translate")
async def api_v1_query_translate(body: SmartTranslateRequest):
    q = body.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail={"error": {"code": "EMPTY_QUERY", "message": "Truy vấn không được để trống."}})
    
    result = await SmartSearchService.translate_and_generate(
        query=q,
        language=body.language or "auto",
        mode=body.mode or "normal"
    )
    return result

# 8. POST /api/v1/query/generate (Generate Query Variations)
@router.post("/query/generate")
async def api_v1_query_generate(body: SmartTranslateRequest):
    q = body.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail={"error": {"code": "EMPTY_QUERY", "message": "Truy vấn không được để trống."}})
    
    result = await SmartSearchService.translate_and_generate(
        query=q,
        language=body.language or "auto",
        mode=body.mode or "normal"
    )
    return {
        "original_query": q,
        "language": result.get("detected_language", "vi"),
        "queries": result.get("queries", {}),
        "flat_queries": result.get("flat_queries", []),
        "query_scores": result.get("query_scores", [])
    }

# 9. POST /api/v1/search/smart & POST /api/v1/search (Full Multi-language Douyin Smart Search)
@router.post("/search/smart")
@router.post("/search")
async def api_v1_search_smart(body: SmartSearchRequest, db: Session = Depends(get_db)):
    q = body.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail={"error": {"code": "EMPTY_QUERY", "message": "Truy vấn không được để trống."}})

    result = await SmartSearchService.execute_smart_search(
        query=q,
        language=body.language or "auto",
        mode=body.mode or "normal",
        custom_queries=body.custom_queries,
        min_likes=body.min_likes or 0,
        db=db
    )
    return result
