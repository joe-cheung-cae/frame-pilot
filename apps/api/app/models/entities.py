from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


def new_id() -> str:
    return uuid4().hex


def utc_now() -> datetime:
    return datetime.now(UTC)


class Project(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    name: str
    root_path: str
    source_mode: str = "copy"
    source_root_path: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    total_images: int = 0
    processed_images: int = 0
    last_processed_at: datetime | None = None
    schema_version: int = 2


class Photo(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project_id: str = Field(index=True, foreign_key="project.id")
    original_path: str
    project_copy_path: str | None = None
    source_identity: str | None = None
    filename: str
    file_ext: str | None = None
    file_size: int = 0
    file_mtime: float | None = None
    content_hash: str | None = None
    width: int = 0
    height: int = 0
    capture_time: datetime | None = None
    camera_model: str | None = None
    lens_model: str | None = None
    focal_length: str | None = None
    aperture: str | None = None
    shutter_speed: str | None = None
    iso: int | None = None
    thumbnail_path: str | None = None
    preview_path: str | None = None
    perceptual_hash: str | None = None
    sharpness_score: float = 0.0
    blur_score: float = 1.0
    exposure_score: float = 0.0
    contrast_score: float = 0.0
    noise_score: float = 0.0
    face_presence: bool = False
    face_sharpness_score: float = 0.0
    eye_open_confidence: float | None = None
    face_quality_score: float = 0.0
    aesthetic_score: float = 0.5
    overall_score: float = 0.0
    embedding: str | None = None
    ai_recommendation: str = "Unreviewed"
    recommendation_explanation: str = "Processing has not produced a recommendation yet."
    user_status: str = "Unreviewed"
    star_rating: int = 0
    group_id: str | None = Field(default=None, foreign_key="photogroup.id")
    processing_state: str = "imported"
    processing_error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PhotoGroup(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project_id: str = Field(index=True, foreign_key="project.id")
    group_type: str = "single"
    representative_photo_id: str | None = Field(default=None, foreign_key="photo.id")
    photo_count: int = 0
    score_summary: str = "{}"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProcessingJob(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project_id: str = Field(index=True, foreign_key="project.id")
    job_type: str = "processing"
    status: str = "queued"
    current_step: str = "queued"
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    progress_percent: float = 0.0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def retryable(self) -> bool:
        return self.job_type == "import" and self.status in {"failed", "complete_with_errors"}


class ExportRecord(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project_id: str = Field(index=True, foreign_key="project.id")
    mode: str
    status: str = "complete"
    selected_count: int = 0
    statuses: str = "[]"
    output_path: str
    error_message: str | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
