import os
import uuid
import json
import aiofiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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

# =====================================================================
# PYDANTIC SCHEMAS / REQUEST & RESPONSE MODELS
# =====================================================================

class SearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query in Vietnamese, English or Chinese")
    keyword: Optional[str] = Field(None, description="Alias for query")
    language: Optional[str] = Field("auto", description="Language mode: auto, vi, zh, en")
    mode: Optional[str] = Field("normal", description="Search depth: normal or deep")
    deep_search: Optional[bool] = Field(False, description="Flag for deep search")
    custom_queries: Optional[List[str]] = Field(None, description="Optional custom Chinese queries")
    min_likes: Optional[int] = Field(0, description="Minimum likes threshold")
    limit: Optional[int] = Field(20, description="Number of results desired")

class UrlAnalyzeRequest(BaseModel):
    url: str = Field(..., description="Douyin or TikTok video link")
    user_hint: Optional[str] = Field("", description="Optional topic hint")
    deep_search: Optional[bool] = Field(False, description="Flag for deep search")

class SmartTranslateRequest(BaseModel):
    query: str = Field(..., description="Query to analyze and translate")
    language: Optional[str] = Field("auto", description="auto, vi, zh, en")
    mode: Optional[str] = Field("normal", description="normal or deep")

class HistoryCreateRequest(BaseModel):
    query: str
    results_count: Optional[int] = 0
    language: Optional[str] = "vi"
    tags: Optional[List[str]] = None

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
    douyin_cookie: Optional[str] = None
    douyin_search_provider: Optional[str] = None
    weight_semantic: Optional[float] = None
    weight_visual: Optional[float] = None
    weight_keyword: Optional[float] = None


# =====================================================================
# 1. POST /api/v1/search (Unified Smart Multi-language Search Endpoint)
# =====================================================================
@router.post("/search", summary="Smart Douyin Search (Vietnamese / Chinese / English)")
@router.post("/search/smart", include_in_schema=False)
@router.post("/search/keyword", include_in_schema=False)
async def api_v1_search(body: SearchRequest, db: Session = Depends(get_db)):
    q = (body.query or body.keyword or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail={"error": {"code": "EMPTY_QUERY", "message": "Từ khóa tìm kiếm không được để trống."}})

    mode = "deep" if (body.mode == "deep" or body.deep_search) else "normal"

    result = await SmartSearchService.execute_smart_search(
        query=q,
        language=body.language or "auto",
        mode=mode,
        custom_queries=body.custom_queries,
        min_likes=body.min_likes or 0,
        db=db
    )
    return result


# =====================================================================
# 2. POST /api/v1/analyze/video & POST /api/v1/search/video (Video Upload Pipeline)
# =====================================================================
@router.post("/analyze/video", summary="Upload video file and trigger AI Multimodal analysis")
@router.post("/search/video", include_in_schema=False)
async def api_v1_analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_hint: str = Form(""),
    deep_search: bool = Form(False),
    db: Session = Depends(get_db)
):
    filename = file.filename or "uploaded_video.mp4"
    ext = filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_FORMAT", "message": f"Định dạng .{ext} không được hỗ trợ. Vui lòng tải file: {', '.join(settings.ALLOWED_EXTENSIONS)}"}}
        )

    video_id = str(uuid.uuid4())
    save_filename = f"{video_id}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    async with aiofiles.open(save_path, "wb") as out_file:
        content = await file.read()
        if len(content) > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail={"error": {"code": "FILE_TOO_LARGE", "message": f"Video vượt quá dung lượng cho phép ({settings.MAX_VIDEO_SIZE_MB}MB)."}})
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
        "filename": filename,
        "filesize": len(content),
        "status": "queued",
        "message": "Video đã được tải lên thành công, đang xếp hàng xử lý."
    }


# =====================================================================
# 3. POST /api/v1/analyze/url & POST /api/v1/search/url (URL Video Link Analysis)
# =====================================================================
@router.post("/analyze/url", summary="Analyze video directly from Douyin / TikTok URL")
@router.post("/search/url", include_in_schema=False)
async def api_v1_analyze_url(
    body: UrlAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if not DouyinUrlParser.is_valid_url(body.url):
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_URL", "message": "Đường dẫn không hợp lệ. Vui lòng nhập link Douyin hoặc TikTok."}})

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


# =====================================================================
# 4. POST /api/v1/files (Decoupled File Storage Upload)
# =====================================================================
@router.post("/files", summary="Upload standalone video or media asset")
async def api_v1_upload_file(file: UploadFile = File(...)):
    filename = file.filename or "file.mp4"
    ext = filename.split(".")[-1].lower()
    file_id = str(uuid.uuid4())
    save_filename = f"{file_id}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    async with aiofiles.open(save_path, "wb") as out_file:
        content = await file.read()
        if len(content) > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail={"error": {"code": "FILE_TOO_LARGE", "message": "File vượt quá giới hạn dung lượng."}})
        await out_file.write(content)

    return {
        "file_id": file_id,
        "filename": filename,
        "filesize": len(content),
        "path": save_path,
        "url": f"/uploads/{save_filename}"
    }


# =====================================================================
# 5. GET /api/v1/jobs/{job_id} (Poll Realtime Job Status)
# =====================================================================
@router.get("/jobs/{job_id}", summary="Check realtime progress and stage of a processing job")
@router.get("/search/{job_id}", include_in_schema=False)
def api_v1_get_job(job_id: str, db: Session = Depends(get_db)):
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


# =====================================================================
# 6. GET /api/v1/search/{job_id}/results (Paginated, Scored Results)
# =====================================================================
@router.get("/search/{job_id}/results", summary="Get paginated and ranked Douyin video results")
def api_v1_get_job_results(
    job_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    min_score: float = Query(70.0, description="Minimum match percentage"),
    sort_by: str = Query("similarity", description="similarity, likes, comments, shares, newest"),
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

    filtered = [r for r in formatted if r["score"] >= min_score]

    if sort_by == "likes":
        filtered.sort(key=lambda x: x["like_count"] or 0, reverse=True)
    elif sort_by == "comments":
        filtered.sort(key=lambda x: x["comment_count"] or 0, reverse=True)
    elif sort_by == "shares":
        filtered.sort(key=lambda x: x["share_count"] or 0, reverse=True)

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


# =====================================================================
# 7. GET & POST & DELETE /api/v1/history (Search & Analysis History)
# =====================================================================
@router.get("/history", summary="List past search and analysis sessions")
def api_v1_get_history(db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.created_at.desc()).limit(50).all()
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

@router.post("/history", summary="Save a custom search query to history")
def api_v1_create_history(body: HistoryCreateRequest, db: Session = Depends(get_db)):
    video_id = f"hist_{uuid.uuid4().hex[:8]}"
    video = Video(
        id=video_id,
        filename=f"Search_{body.query[:30]}",
        file_path="",
        filesize=0
    )
    db.add(video)
    db.commit()
    return {"success": True, "id": video_id, "query": body.query}

@router.delete("/history/{video_id}", summary="Delete a history session")
def api_v1_delete_history(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        db.delete(video)
        db.commit()
    return {"success": True, "message": "Đã xóa lịch sử tìm kiếm."}


# =====================================================================
# 8. GET & PUT /api/v1/settings (Manage Backend Configurations securely)
# =====================================================================
@router.get("/settings", summary="Get current backend settings (masked secrets)")
def api_v1_get_settings():
    def mask_key(k: str) -> str:
        if not k or len(k) < 8:
            return "******" if k else ""
        return k[:4] + "*" * (len(k) - 8) + k[-4:]

    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ai_provider": getattr(settings, "AI_PROVIDER", "gemini"),
        "gemini_api_key_configured": bool(getattr(settings, "GEMINI_API_KEY", "")),
        "gemini_api_key_masked": mask_key(getattr(settings, "GEMINI_API_KEY", "")),
        "openai_api_key_configured": bool(getattr(settings, "OPENAI_API_KEY", "")),
        "openai_api_key_masked": mask_key(getattr(settings, "OPENAI_API_KEY", "")),
        "douyin_cookie_configured": bool(getattr(settings, "DOUYIN_COOKIE", "")),
        "douyin_search_provider": getattr(settings, "DOUYIN_SEARCH_PROVIDER", "live"),
        "weights": {
            "semantic": settings.WEIGHT_SEMANTIC,
            "visual": settings.WEIGHT_VISUAL,
            "keyword": settings.WEIGHT_KEYWORD,
            "hashtag": settings.WEIGHT_HASHTAG,
            "content_type": settings.WEIGHT_CONTENT_TYPE,
            "popularity": settings.WEIGHT_POPULARITY
        }
    }

@router.put("/settings", summary="Update runtime configuration and API keys")
def api_v1_update_settings(body: SettingsUpdateRequest):
    if body.gemini_api_key is not None:
        settings.GEMINI_API_KEY = body.gemini_api_key
        os.environ["GEMINI_API_KEY"] = body.gemini_api_key
        os.environ["AI_API_KEY"] = body.gemini_api_key
    if body.openai_api_key is not None:
        settings.OPENAI_API_KEY = body.openai_api_key
        os.environ["OPENAI_API_KEY"] = body.openai_api_key
    if body.ai_provider is not None:
        settings.AI_PROVIDER = body.ai_provider
    if body.douyin_cookie is not None:
        settings.DOUYIN_COOKIE = body.douyin_cookie
        os.environ["DOUYIN_COOKIE"] = body.douyin_cookie
    if body.douyin_search_provider is not None:
        settings.DOUYIN_SEARCH_PROVIDER = body.douyin_search_provider
    if body.weight_semantic is not None:
        settings.WEIGHT_SEMANTIC = body.weight_semantic
    if body.weight_visual is not None:
        settings.WEIGHT_VISUAL = body.weight_visual
    if body.weight_keyword is not None:
        settings.WEIGHT_KEYWORD = body.weight_keyword

    return {"success": True, "message": "Cấu hình backend đã được cập nhật thành công."}


# =====================================================================
# 9. NLP & TRANSLATION UTILITY ROUTES
# =====================================================================
@router.post("/query/translate", summary="Translate & preview Chinese keywords for Vietnamese queries")
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

@router.post("/query/generate", summary="Generate Chinese query variations with priority scores")
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
