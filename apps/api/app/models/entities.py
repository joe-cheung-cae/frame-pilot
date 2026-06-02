from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


def new_id() -> str:
    return uuid4().hex


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    name: str
    root_path: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    total_images: int = 0
    processed_images: int = 0


class Photo(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project_id: str = Field(index=True, foreign_key="project.id")
    original_path: str
    filename: str
    file_size: int = 0
    width: int = 0
    height: int = 0
    capture_time: Optional[datetime] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    focal_length: Optional[str] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    iso: Optional[int] = None
    thumbnail_path: Optional[str] = None
    preview_path: Optional[str] = None
    sharpness_score: float = 0.0
    blur_score: float = 1.0
    exposure_score: float = 0.0
    contrast_score: float = 0.0
    noise_score: float = 0.0
    face_presence: bool = False
    face_sharpness_score: float = 0.0
    eye_open_confidence: Optional[float] = None
    face_quality_score: float = 0.0
    aesthetic_score: float = 0.5
    overall_score: float = 0.0
    embedding: Optional[str] = None
    ai_recommendation: str = "Unreviewed"
    recommendation_explanation: str = "Processing has not produced a recommendation yet."
    user_status: str = "Unreviewed"
    star_rating: int = 0
    group_id: Optional[str] = Field(default=None, foreign_key="photogroup.id")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PhotoGroup(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project_id: str = Field(index=True, foreign_key="project.id")
    group_type: str = "single"
    representative_photo_id: Optional[str] = Field(default=None, foreign_key="photo.id")
    photo_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProcessingJob(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project_id: str = Field(index=True, foreign_key="project.id")
    status: str = "queued"
    current_step: str = "queued"
    total_items: int = 0
    processed_items: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ExportRecord(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project_id: str = Field(index=True, foreign_key="project.id")
    mode: str
    status: str = "complete"
    output_path: str
    created_at: datetime = Field(default_factory=utc_now)

