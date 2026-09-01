import json
import time
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    filesize = Column(Integer, default=0)
    duration = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("VideoAnalysis", back_populates="video", uselist=False, cascade="all, delete-orphan")
    queries = relationship("SearchQuery", back_populates="video", cascade="all, delete-orphan")
    results = relationship("SearchResult", back_populates="video", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="video", cascade="all, delete-orphan")


class VideoAnalysis(Base):
    __tablename__ = "video_analysis"

    id = Column(String(64), primary_key=True, index=True)
    video_id = Column(String(64), ForeignKey("videos.id"), nullable=False, unique=True)
    
    summary = Column(Text, default="")
    main_topic = Column(String(255), default="")
    secondary_topics = Column(Text, default="[]") # JSON list
    people = Column(Text, default="[]")
    objects = Column(Text, default="[]")
    actions = Column(Text, default="[]")
    locations = Column(Text, default="[]")
    products = Column(Text, default="[]")
    brands = Column(Text, default="[]")
    spoken_language = Column(String(64), default="")
    transcript = Column(Text, default="")
    ocr_text = Column(Text, default="[]")
    visual_style = Column(Text, default="[]")
    camera_style = Column(Text, default="[]")
    content_format = Column(String(128), default="")
    emotional_tone = Column(Text, default="[]")
    narrative_structure = Column(String(255), default="")
    key_moments = Column(Text, default="[]")
    search_concepts = Column(Text, default="[]")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    video = relationship("Video", back_populates="analysis")

    def to_profile_dict(self):
        def _parse(field):
            if isinstance(field, str):
                try:
                    return json.loads(field)
                except Exception:
                    return field
            return field or []

        return {
            "summary": self.summary,
            "main_topic": self.main_topic,
            "secondary_topics": _parse(self.secondary_topics),
            "people": _parse(self.people),
            "objects": _parse(self.objects),
            "actions": _parse(self.actions),
            "locations": _parse(self.locations),
            "products": _parse(self.products),
            "brands": _parse(self.brands),
            "spoken_language": self.spoken_language,
            "transcript": self.transcript,
            "ocr_text": _parse(self.ocr_text),
            "visual_style": _parse(self.visual_style),
            "camera_style": _parse(self.camera_style),
            "content_format": self.content_format,
            "emotional_tone": _parse(self.emotional_tone),
            "narrative_structure": self.narrative_structure,
            "key_moments": _parse(self.key_moments),
            "search_concepts": _parse(self.search_concepts)
        }


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(String(64), primary_key=True, index=True)
    video_id = Column(String(64), ForeignKey("videos.id"), nullable=False)
    query = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False) # core_topic, people_or_objects, actions, scene, content_format, long_tail
    reason = Column(String(512), default="")
    score = Column(Float, default=0.0)
    is_enabled = Column(Boolean, default=True)
    is_custom = Column(Boolean, default=False)
    expanded_variants = Column(Text, default="[]") # JSON list
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="queries")


class SearchResult(Base):
    __tablename__ = "search_results"

    id = Column(String(64), primary_key=True, index=True)
    video_id = Column(String(64), ForeignKey("videos.id"), nullable=False)
    query_id = Column(String(64), nullable=True)
    platform = Column(String(32), default="douyin")
    remote_video_id = Column(String(64), nullable=False)
    url = Column(String(512), nullable=False)
    author = Column(String(255), default="")
    title = Column(Text, default="")
    description = Column(Text, default="")
    hashtags = Column(Text, default="[]")
    cover_url = Column(String(512), default="")
    publish_time = Column(String(64), default="")
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    search_query = Column(String(255), default="")
    relevance_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    retrieved_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="results")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True, index=True)
    video_id = Column(String(64), ForeignKey("videos.id"), nullable=False)
    stage = Column(String(64), default="queued") # queued, processing, analyzing, generating_queries, searching, ranking, completed, failed
    status = Column(String(32), default="pending") # pending, in_progress, completed, failed
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    video = relationship("Video", back_populates="jobs")
