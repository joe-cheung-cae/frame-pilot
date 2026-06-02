from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    root_path: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Project name is required")
        return stripped


class ProjectRead(BaseModel):
    id: str
    name: str
    root_path: str
    created_at: datetime
    updated_at: datetime
    total_images: int
    processed_images: int


class PhotoRead(BaseModel):
    id: str
    project_id: str
    filename: str
    file_size: int
    width: int
    height: int
    capture_time: Optional[datetime]
    camera_model: Optional[str]
    lens_model: Optional[str]
    focal_length: Optional[str]
    aperture: Optional[str]
    shutter_speed: Optional[str]
    iso: Optional[int]
    thumbnail_path: Optional[str]
    preview_path: Optional[str]
    sharpness_score: float
    blur_score: float
    exposure_score: float
    contrast_score: float
    noise_score: float
    face_presence: bool
    face_sharpness_score: float
    eye_open_confidence: Optional[float]
    face_quality_score: float
    aesthetic_score: float
    overall_score: float
    ai_recommendation: str
    recommendation_explanation: str
    user_status: str
    star_rating: int
    group_id: Optional[str]


class PhotoUpdate(BaseModel):
    user_status: Optional[str] = None
    star_rating: Optional[int] = Field(default=None, ge=0, le=5)

    @field_validator("user_status")
    @classmethod
    def status_must_be_valid(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {"Pick", "Maybe", "Reject", "Unreviewed"}
        if value not in allowed:
            raise ValueError(f"Status must be one of {sorted(allowed)}")
        return value


class GroupRead(BaseModel):
    id: str
    project_id: str
    group_type: str
    representative_photo_id: Optional[str]
    photo_count: int


class JobRead(BaseModel):
    id: str
    project_id: str
    status: str
    current_step: str
    total_items: int
    processed_items: int
    error_message: Optional[str]


class ExportCreate(BaseModel):
    mode: str = "csv"
    statuses: list[str] = ["Pick"]


class ExportRead(BaseModel):
    id: str
    project_id: str
    mode: str
    status: str
    output_path: str
    created_at: datetime

