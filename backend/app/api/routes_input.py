import os
import uuid
import aiofiles
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Video, Job, SearchQuery, SearchResult
from ..core.config import settings
from ..douyin.url_parser import DouyinUrlParser
from ..worker.job_runner import PipelineJobRunner
from ..providers.factory import get_search_provider
from ..pipeline.ranking_engine import RankingEngine
from ..pipeline.deduplicator import Deduplicator

router = APIRouter()

class UrlInputRequest(BaseModel):
    url: str
    user_hint: Optional[str] = ""
    deep_search: Optional[bool] = False

class KeywordSearchRequest(BaseModel):
    keyword: str
    deep_search: Optional[bool] = False
    limit: Optional[int] = 20
    min_likes: Optional[int] = 0

# 1. Input Mode A: Upload Video File
@router.post("/input/upload")
async def input_upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_hint: str = Form(""),
    deep_search: bool = Form(False),
    db: Session = Depends(get_db)
):
    filename = file.filename or "uploaded_video.mp4"
    ext = filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format .{ext}. Allowed: {settings.ALLOWED_EXTENSIONS}")

    video_id = str(uuid.uuid4())
    save_filename = f"{video_id}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    async with aiofiles.open(save_path, "wb") as out_file:
        content = await file.read()
        if len(content) > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File exceeds max size ({settings.MAX_VIDEO_SIZE_MB}MB)")
        await out_file.write(content)

    video = Video(id=video_id, filename=filename, file_path=save_path, filesize=len(content))
    db.add(video)

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, video_id=video_id, stage="queued", status="pending", progress_percent=0)
    db.add(job)
    db.commit()

    background_tasks.add_task(PipelineJobRunner.run_full_pipeline, video_id, job_id, db, user_hint)

    return {
        "success": True,
        "input_type": "upload",
        "video_id": video_id,
        "job_id": job_id,
        "filename": filename,
        "status": "queued"
    }

# 2. Input Mode B: Douyin / TikTok URL
@router.post("/input/url")
async def input_douyin_url(
    body: UrlInputRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if not DouyinUrlParser.is_valid_url(body.url):
        raise HTTPException(status_code=400, detail="Đường dẫn không hợp lệ. Vui lòng nhập link URL hợp lệ.")

    meta = DouyinUrlParser.parse_and_fetch_metadata(body.url, settings.UPLOAD_DIR)
    if not meta.get("success", False):
        raise HTTPException(status_code=400, detail=meta.get("error", "Không thể phân tích URL Douyin này."))

    video_id = str(uuid.uuid4())
    video_path = meta.get("video_path")

    # If direct video file wasn't downloaded, create a placeholder video record with title & meta
    if not video_path:
        # Create a lightweight metadata container
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
    background_tasks.add_task(PipelineJobRunner.run_full_pipeline, video_id, job_id, db, combined_hint)

    return {
        "success": True,
        "input_type": "url",
        "video_id": video_id,
        "job_id": job_id,
        "url": meta.get("url"),
        "title": meta.get("title"),
        "author": meta.get("author"),
        "cover_url": meta.get("cover_url"),
        "has_downloaded_video": meta.get("has_downloaded_video"),
        "status": "queued"
    }

# 3. Input Mode C: Direct Manual Keyword Search
@router.post("/input/keyword")
async def input_manual_keyword(
    body: KeywordSearchRequest,
    db: Session = Depends(get_db)
):
    kw = body.keyword.strip()
    if not kw:
        raise HTTPException(status_code=400, detail="Vui lòng nhập từ khóa tiếng Trung cần tìm kiếm.")

    provider = get_search_provider()
    limit = 50 if body.deep_search else min(50, max(5, body.limit or 20))
    raw_results = await provider.search(kw, limit=limit)

    # Save to ad-hoc session / virtual video
    video_id = f"kw_{uuid.uuid4().hex[:8]}"
    video = Video(id=video_id, filename=f"Keyword_{kw}.txt", file_path="", filesize=0)
    db.add(video)

    saved_results = []
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
    import json
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
        saved_results.append(sr)

    db.commit()

    return {
        "success": True,
        "input_type": "keyword",
        "video_id": video_id,
        "keyword": kw,
        "results_count": len(saved_results),
        "results": [
            {
                "id": s.id,
                "video_id": s.remote_video_id,
                "url": s.url,
                "author": s.author,
                "title": s.title,
                "like_count": s.like_count,
                "cover_url": s.cover_url,
                "search_query": s.search_query,
                "final_score": s.final_score
            } for s in saved_results
        ]
    }
