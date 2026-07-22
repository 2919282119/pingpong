from pydantic import BaseModel, Field
from typing import Optional

from app.config import ACTION_TYPES


class AnalyzeRequest(BaseModel):
    action_type: str = Field(..., description="One of: " + ", ".join(ACTION_TYPES))


class VideoInfo(BaseModel):
    duration_s: float
    processed_fps: int
    original_width: int
    original_height: int


class ActionSegment(BaseModel):
    start_ms: float
    end_ms: float
    action_type: str
    confidence: float


class MetricResult(BaseModel):
    name: str
    user_value: float
    template_value: float
    diff: float
    score: float
    level: str
    problem: str
    suggestion: str


class SegmentReport(BaseModel):
    start_ms: float
    end_ms: float
    action_type: str
    template_source: str
    similarity_score: float
    user_video_url: str = ""
    template_video_url: str = ""
    metrics: list[MetricResult]


class TypeStatistics(BaseModel):
    total_segments: int
    by_type: dict[str, int]


class AnalysisReport(BaseModel):
    video_info: VideoInfo
    overall_score: float
    action_segments: list[SegmentReport]
    statistics: TypeStatistics


class ErrorResponse(BaseModel):
    detail: str
