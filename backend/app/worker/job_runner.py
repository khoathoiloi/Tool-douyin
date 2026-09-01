import os
import uuid
import json
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.models import Video, VideoAnalysis, SearchQuery, SearchResult, Job
from ..core.config import settings
from ..video.metadata import VideoMetadataExtractor
from ..video.keyframes import AdaptiveKeyframeExtractor
from ..pipeline.video_processor import VideoProcessor
from ..ai.asr import VideoASREngine
from ..ai.ocr import VideoOCREngine
from ..ai.analyzer import MultiLayerVideoAnalyzer
from ..douyin.search_strategy import WaterfallSearchStrategy
from ..ranking.scoring import MultiLayerScoringEngine
from ..pipeline.reranker import LLMReranker
from ..pipeline.deduplicator import Deduplicator
from ..providers.factory import get_search_provider

# Setup logging
log_dir = os.path.join(settings.BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "app.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PipelineJobRunner")

class PipelineJobRunner:
    @staticmethod
    def update_job(db: Session, job_id: str, stage: str, status: str, progress: int, error: str = None):
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.stage = stage
            job.status = status
            job.progress_percent = progress
            if error:
                job.error_message = error
            db.commit()

    @classmethod
    async def run_full_pipeline(
        cls,
        video_id: str,
        job_id: str,
        db: Session,
        user_hint: str = "",
        deep_search: bool = False
    ):
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            cls.update_job(db, job_id, "failed", "failed", 0, "Video record not found")
            return

        try:
            logger.info(f"Starting pipeline for video {video_id} (job {job_id})")

            # Stage 1: Video Metadata & Keyframes (15%)
            cls.update_job(db, job_id, "processing", "in_progress", 15)
            has_video_file = os.path.exists(video.file_path) and os.path.getsize(video.file_path) > 1024

            video_dir = os.path.dirname(video.file_path) if has_video_file else settings.UPLOAD_DIR
            frames_dir = os.path.join(video_dir, f"frames_{video.id}")
            audio_path = os.path.join(video_dir, f"audio_{video.id}.mp3")

            meta = VideoMetadataExtractor.extract(video.file_path) if has_video_file else {"duration": 15.0, "fps": 30.0, "has_audio": True}
            video.duration = meta.get("duration", 0)
            video.width = meta.get("width", 0)
            video.height = meta.get("height", 0)
            db.commit()

            keyframe_items = []
            extracted_audio = ""
            if has_video_file:
                keyframe_items = AdaptiveKeyframeExtractor.extract_adaptive_keyframes(video.file_path, frames_dir, max_frames=8)
                extracted_audio = VideoProcessor.extract_audio(video.file_path, audio_path)

            # Stage 2: ASR, OCR, MultiLayer Vision Analysis (40%)
            cls.update_job(db, job_id, "analyzing", "in_progress", 40)
            asr_res = VideoASREngine.transcribe_audio(extracted_audio, api_key=settings.GEMINI_API_KEY)
            ocr_items = VideoOCREngine.extract_text(keyframe_items, api_key=settings.GEMINI_API_KEY)

            profile = MultiLayerVideoAnalyzer.analyze(
                keyframe_items=keyframe_items,
                ocr_items=ocr_items,
                asr_data=asr_res,
                metadata=meta,
                user_hint=user_hint,
                api_key=settings.GEMINI_API_KEY
            )

            # Save Analysis Profile
            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video.id).first()
            if not analysis:
                analysis = VideoAnalysis(id=str(uuid.uuid4()), video_id=video.id)
                db.add(analysis)

            analysis.summary = profile.get("summary", "")
            analysis.main_topic = profile.get("categories", ["General"])[0] if profile.get("categories") else "General"
            analysis.secondary_topics = json.dumps(profile.get("categories", []), ensure_ascii=False)
            analysis.people = json.dumps(profile.get("subjects", []), ensure_ascii=False)
            analysis.objects = json.dumps(profile.get("appearance", []), ensure_ascii=False)
            analysis.actions = json.dumps(profile.get("actions", []), ensure_ascii=False)
            analysis.locations = json.dumps(profile.get("environment", []), ensure_ascii=False)
            analysis.products = json.dumps(profile.get("appearance", []), ensure_ascii=False)
            analysis.brands = json.dumps(profile.get("keywords", {}).get("trend", []), ensure_ascii=False)
            analysis.spoken_language = asr_res.get("language", "vi")
            analysis.transcript = asr_res.get("transcript", "")
            analysis.ocr_text = json.dumps([o.get("text") for o in ocr_items if isinstance(o, dict)], ensure_ascii=False)
            analysis.visual_style = json.dumps(profile.get("keywords", {}).get("style", []), ensure_ascii=False)
            analysis.camera_style = json.dumps(profile.get("camera", []), ensure_ascii=False)
            analysis.content_format = profile.get("categories", ["General"])[0] if profile.get("categories") else "General"
            analysis.emotional_tone = json.dumps(profile.get("emotional_tone", []), ensure_ascii=False)
            analysis.search_concepts = json.dumps(profile.get("keywords", {}).get("primary", []), ensure_ascii=False)
            db.commit()

            # Stage 3: Tiered Chinese Queries (60%)
            cls.update_job(db, job_id, "generating_queries", "in_progress", 60)
            queries_dict = profile.get("queries", {})

            db.query(SearchQuery).filter(SearchQuery.video_id == video.id).delete()

            for category, q_list in queries_dict.items():
                for q_text in q_list:
                    sq = SearchQuery(
                        id=str(uuid.uuid4()),
                        video_id=video.id,
                        query=q_text,
                        category=category,
                        reason=f"Nhóm truy vấn {category}",
                        score=0.95 if category in ["exact", "high_similarity"] else 0.85,
                        is_enabled=True,
                        is_custom=False,
                        expanded_variants=json.dumps([], ensure_ascii=False)
                    )
                    db.add(sq)
            db.commit()

            # Stage 4: 4-Phase Waterfall Search & Candidate Collection (75%)
            cls.update_job(db, job_id, "searching", "in_progress", 75)
            provider = get_search_provider()
            candidates = await WaterfallSearchStrategy.execute_search(
                queries_by_tier=queries_dict,
                provider=provider,
                deep_search=deep_search,
                max_candidates=100
            )

            # Stage 5: Multi-layer Similarity Scoring & Re-ranking (90%)
            cls.update_job(db, job_id, "ranking", "in_progress", 90)
            candidate_dicts = []
            for c in candidates:
                cand_d = {
                    "video_id": video.id,
                    "platform": c.platform,
                    "remote_video_id": c.video_id,
                    "url": c.url,
                    "author": c.author,
                    "title": c.title,
                    "description": c.description,
                    "hashtags": c.hashtags,
                    "cover_url": c.cover_url,
                    "publish_time": c.publish_time,
                    "like_count": c.like_count,
                    "comment_count": c.comment_count,
                    "share_count": c.share_count,
                    "search_query": c.search_query
                }
                score_info = MultiLayerScoringEngine.calculate_score(profile, cand_d)
                cand_d["relevance_score"] = score_info["final_score"]
                cand_d["final_score"] = score_info["final_score"]
                cand_d["score_pct"] = score_info["score_pct"]
                candidate_dicts.append(cand_d)

            # LLM Reranker on Top 30
            reranked = LLMReranker.rerank_candidates(profile, candidate_dicts, top_n=30, api_key=settings.GEMINI_API_KEY)

            # Save Results
            db.query(SearchResult).filter(SearchResult.video_id == video.id).delete()
            for r in reranked:
                sr = SearchResult(
                    id=str(uuid.uuid4()),
                    video_id=video.id,
                    platform=r.get("platform", "douyin"),
                    remote_video_id=r.get("remote_video_id", ""),
                    url=r.get("url", ""),
                    author=r.get("author", ""),
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    hashtags=json.dumps(r.get("hashtags", []), ensure_ascii=False),
                    cover_url=r.get("cover_url", ""),
                    publish_time=r.get("publish_time", ""),
                    like_count=r.get("like_count", 0),
                    comment_count=r.get("comment_count", 0),
                    share_count=r.get("share_count", 0),
                    search_query=r.get("search_query", ""),
                    relevance_score=r.get("relevance_score", 0.0),
                    final_score=r.get("final_score", 0.0)
                )
                db.add(sr)
            db.commit()

            # Clean temporary frame files
            if os.path.exists(frames_dir):
                for f in os.listdir(frames_dir):
                    os.remove(os.path.join(frames_dir, f))
                os.rmdir(frames_dir)

            cls.update_job(db, job_id, "completed", "completed", 100)
            logger.info(f"Pipeline completed successfully for video {video_id}. Found {len(reranked)} results.")

        except Exception as e:
            logger.error(f"Pipeline failed for video {video_id}: {e}", exc_info=True)
            cls.update_job(db, job_id, "failed", "failed", 0, str(e))
