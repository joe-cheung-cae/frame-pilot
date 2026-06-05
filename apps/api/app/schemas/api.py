from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    root_path: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Project name is required")
        return stripped

    @field_validator("root_path")
    @classmethod
    def blank_root_path_uses_default(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ProjectRead(BaseModel):
    id: str
    name: str
    root_path: str
    source_mode: str
    source_root_path: str | None
    created_at: datetime
    updated_at: datetime
    total_images: int
    processed_images: int
    last_processed_at: datetime | None
    schema_version: int


class PhotoRead(BaseModel):
    id: str
    project_id: str
    filename: str
    file_ext: str | None
    file_size: int
    file_mtime: float | None
    content_hash: str | None
    project_copy_path: str | None
    source_identity: str | None
    width: int
    height: int
    capture_time: datetime | None
    camera_model: str | None
    lens_model: str | None
    focal_length: str | None
    aperture: str | None
    shutter_speed: str | None
    iso: int | None
    thumbnail_path: str | None
    preview_path: str | None
    perceptual_hash: str | None
    sharpness_score: float
    blur_score: float
    exposure_score: float
    contrast_score: float
    noise_score: float
    face_presence: bool
    face_sharpness_score: float
    eye_open_confidence: float | None
    face_quality_score: float
    aesthetic_score: float
    overall_score: float
    ai_recommendation: str
    recommendation_explanation: str
    user_status: str
    star_rating: int
    group_id: str | None
    processing_state: str
    processing_error: str | None


class PhotoStatusCountsRead(BaseModel):
    Pick: int = 0
    Maybe: int = 0
    Reject: int = 0
    Unreviewed: int = 0


class ImportSkippedFile(BaseModel):
    filename: str
    reason: str


class ImportTimingStageRead(BaseModel):
    calls: int
    seconds: float


class ImportTimingRead(BaseModel):
    total_files: int
    imported_files: int
    skipped_files: int
    total_seconds: float
    stages: dict[str, ImportTimingStageRead]


class JobRead(BaseModel):
    id: str
    project_id: str
    job_type: str
    status: str
    current_step: str
    total_items: int
    processed_items: int
    failed_items: int
    progress_percent: float
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None


class ImportResult(BaseModel):
    imported: list[PhotoRead]
    skipped: list[ImportSkippedFile]
    job: JobRead | None = None
    total_files: int
    accepted_files: int
    skipped_files: int
    failed_files: int
    timing: ImportTimingRead | None = None


class PhotoUpdate(BaseModel):
    user_status: str | None = None
    star_rating: int | None = Field(default=None, ge=0, le=5)

    @field_validator("user_status")
    @classmethod
    def status_must_be_valid(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"Pick", "Maybe", "Reject", "Unreviewed"}
        if value not in allowed:
            raise ValueError(f"Status must be one of {sorted(allowed)}")
        return value

    @model_validator(mode="after")
    def must_include_an_update(self) -> "PhotoUpdate":
        if self.user_status is None and self.star_rating is None:
            raise ValueError("At least one photo update field is required")
        return self


class PhotoBatchUpdate(PhotoUpdate):
    photo_ids: list[str] = Field(min_length=1)


class GroupRead(BaseModel):
    id: str
    project_id: str
    group_type: str
    representative_photo_id: str | None
    photo_count: int
    score_summary: str


class ExportCreate(BaseModel):
    mode: str = "csv"
    statuses: list[str] = ["Pick"]

    @field_validator("mode")
    @classmethod
    def mode_must_be_valid(cls, value: str) -> str:
        allowed = {"csv", "folder", "zip"}
        if value not in allowed:
            raise ValueError(f"Export mode must be one of {sorted(allowed)}")
        return value

    @field_validator("statuses")
    @classmethod
    def statuses_must_be_valid(cls, value: list[str]) -> list[str]:
        allowed_order = ["Pick", "Maybe", "Reject", "Unreviewed"]
        allowed = set(allowed_order)
        if not value:
            raise ValueError("At least one status is required")
        invalid = sorted(set(value) - allowed)
        if invalid:
            raise ValueError(f"Statuses must be one of {sorted(allowed)}")
        selected = set(value)
        return [status for status in allowed_order if status in selected]


class ExportRead(BaseModel):
    id: str
    project_id: str
    mode: str
    status: str
    selected_count: int
    statuses: str
    output_path: str
    error_message: str | None
    completed_at: datetime | None
    created_at: datetime
