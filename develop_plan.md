# FramePilot Development Plan

## 1. Project Overview

FramePilot is a local-first AI-assisted photo culling web application for photographers. Its purpose is to reduce the time spent selecting photos after a shoot by automatically grouping similar images, detecting technically weak shots, ranking candidates, and allowing the user to make the final creative decision.

The product should not attempt to fully replace human judgment. Instead, it should remove obvious low-quality frames and present the best candidates from each burst or similar-photo group.

Primary product statement:

> FramePilot helps photographers quickly turn hundreds or thousands of photos into a clean, reviewable shortlist.

## 2. Target Users

### 2.1 Primary Users

- Hobby photographers who shoot large batches during travel, family events, street photography, wildlife, or portraits.
- Semi-professional photographers who need a faster pre-selection workflow before editing in Lightroom, Capture One, or other post-processing tools.
- Users who prefer privacy and do not want to upload original photos to a cloud-based service.

### 2.2 Initial User Scenario

A user imports a folder containing 500 to 2,000 photos from a camera. FramePilot generates previews, groups similar photos, detects blurry or failed frames, recommends the best shots in each group, and lets the user manually confirm the final picks.

## 3. Product Positioning

FramePilot should be positioned as an AI-assisted workflow tool, not a fully automatic photo editor.

The core value is:

- Save time during photo selection.
- Group near-duplicate burst shots.
- Identify technically weak images.
- Recommend the best image from each similar group.
- Keep the user in control of final selection.
- Preserve privacy through local-first processing.

## 4. MVP Scope

The MVP should focus on a complete and reliable culling workflow.

### 4.1 MVP Features

1. Create a new project.
2. Import a local folder or multiple image files.
3. Generate thumbnails and preview images.
4. Extract basic metadata from each image.
5. Compute technical quality scores.
6. Compute image embeddings for visual similarity.
7. Group near-duplicate or burst photos.
8. Recommend the best photo in each group.
9. Provide a fast manual review interface.
10. Allow the user to mark photos as Pick, Maybe, or Reject.
11. Export selected photos or export a CSV selection list.

### 4.2 Out of Scope for MVP

The following features should not be implemented in the first version:

- Full RAW development pipeline.
- Cloud synchronization.
- User accounts.
- Payment system.
- Lightroom plugin.
- Advanced personalized model training.
- Online collaboration.
- Mobile version.
- Full professional color management.

## 5. Supported File Types

### 5.1 MVP File Types

Support these formats first:

- JPEG
- PNG
- WebP

### 5.2 Future File Types

Add support later for:

- HEIC
- Sony ARW
- Canon CR3
- Nikon NEF
- DNG

RAW support should be treated as a separate milestone because RAW decoding, embedded preview extraction, color management, and performance optimization will significantly increase complexity.

## 6. Core Workflow

The MVP workflow should be:

1. User opens FramePilot in the browser.
2. User creates a new project.
3. User selects a local folder or uploads multiple files.
4. The system creates a local project database.
5. The system generates thumbnails.
6. The system extracts image metadata.
7. The system computes technical quality metrics.
8. The system computes visual embeddings.
9. The system groups similar photos.
10. The system ranks photos inside each group.
11. User reviews groups in a culling interface.
12. User confirms Pick, Maybe, or Reject.
13. User exports selected photos or a selection list.

## 7. AI and Image Analysis Requirements

### 7.1 Technical Quality Metrics

For each image, compute the following scores:

- Sharpness score
- Blur risk score
- Exposure score
- Contrast score
- Noise risk score
- Face presence flag
- Face sharpness score
- Eye-open confidence score, if face and eye detection are available
- Aesthetic score, if a lightweight aesthetic model is available
- Overall score

### 7.2 Similarity Grouping

The system should group photos using a combination of:

- Visual embedding similarity
- EXIF capture time distance
- Filename sequence proximity
- Image dimensions
- Camera model, if available
- Lens and focal length, if available

The grouping algorithm should support burst sequences and near-duplicate compositions.

A simple first implementation may use:

- Generate one embedding per image.
- Sort images by capture time or filename.
- Compare each image with nearby images in the sorted list.
- Group images when cosine similarity is above a configurable threshold.
- Split groups when capture time difference is too large.

### 7.3 Group Ranking

Inside each group, rank images by:

```text
final_score =
    0.30 * sharpness_score
  + 0.20 * exposure_score
  + 0.20 * face_quality_score
  + 0.20 * aesthetic_score
  - 0.10 * duplicate_penalty
```

The weights should be configurable in code. The scoring model should be simple and transparent in the MVP.

### 7.4 Decision Labels

Each photo should have one of these user-facing statuses:

- Pick
- Maybe
- Reject
- Unreviewed

AI should provide a recommendation, but the user decision must override the AI recommendation.

## 8. Recommendation Explanation

Each recommendation should include a short explanation.

Examples:

```text
Recommended because it has the highest sharpness score in this similar-photo group.
```

```text
Rejected because it appears blurry and is visually similar to a sharper image.
```

```text
Marked as Maybe because the face quality is good, but exposure is slightly low.
```

The explanation does not need to be generated by an LLM. It can be rule-based in the MVP.

## 9. User Interface Requirements

### 9.1 Main Pages

Implement these pages:

1. Home page
2. Project creation page
3. Import page
4. Processing status page
5. Culling workspace
6. Export page

### 9.2 Culling Workspace Layout

The culling workspace should include:

- Left sidebar: group list and filters
- Center area: large photo preview
- Bottom filmstrip: photos in the current group
- Right panel: score details and recommendation explanation
- Top toolbar: project name, progress, export button

### 9.3 Review Filters

Provide filters for:

- All photos
- Picks
- Maybes
- Rejects
- Unreviewed
- AI recommended
- Blurry photos
- Duplicate groups
- Photos with faces

### 9.4 Keyboard Shortcuts

Support the following shortcuts:

- Left arrow: previous photo
- Right arrow: next photo
- P: mark as Pick
- M: mark as Maybe
- X: mark as Reject
- U: mark as Unreviewed
- 1 to 5: assign star rating
- Space: toggle large preview
- G: go to group view

Keyboard-first review is critical for fast culling.

## 10. Technology Stack

### 10.1 Frontend

Use:

- Next.js
- React
- TypeScript
- Tailwind CSS
- Zustand or Jotai for client state
- TanStack Query for server state

### 10.2 Backend

Use:

- Python
- FastAPI
- Pydantic
- SQLite for MVP metadata storage
- SQLAlchemy or SQLModel
- Uvicorn

### 10.3 Image Processing

Use:

- OpenCV
- Pillow
- imagehash
- exifread or piexif
- NumPy

### 10.4 AI Runtime

Start with backend-side inference for simplicity:

- ONNX Runtime
- OpenCLIP or another lightweight image embedding model exported to ONNX
- Optional lightweight face detection model

Browser-side inference can be explored later with ONNX Runtime Web.

### 10.5 Storage

Use a local project directory structure:

```text
frame-pilot-project/
  project.db
  thumbnails/
  previews/
  exports/
  cache/
```

The original photos should not be modified.

## 11. Local-First Design

The application should be designed as a local-first tool.

Requirements:

- Original photos remain on the user's computer.
- The app should not upload photos to a remote server in MVP.
- The backend should run locally during development and initial deployment.
- Project metadata should be stored in SQLite.
- Generated thumbnails and previews should be cached locally.

For the browser file workflow, use standard file upload first. Later, support the File System Access API for a better local folder experience on compatible browsers.

## 12. Data Model

### 12.1 Project

Fields:

- id
- name
- root_path
- created_at
- updated_at
- total_images
- processed_images

### 12.2 Photo

Fields:

- id
- project_id
- original_path
- filename
- file_size
- width
- height
- capture_time
- camera_model
- lens_model
- focal_length
- aperture
- shutter_speed
- iso
- thumbnail_path
- preview_path
- sharpness_score
- blur_score
- exposure_score
- contrast_score
- noise_score
- face_quality_score
- aesthetic_score
- overall_score
- ai_recommendation
- user_status
- star_rating
- group_id
- created_at
- updated_at

### 12.3 PhotoGroup

Fields:

- id
- project_id
- group_type
- representative_photo_id
- photo_count
- created_at
- updated_at

### 12.4 ProcessingJob

Fields:

- id
- project_id
- status
- current_step
- total_items
- processed_items
- error_message
- created_at
- updated_at

## 13. Backend API Design

Implement these API endpoints:

```text
POST   /api/projects
GET    /api/projects
GET    /api/projects/{project_id}
DELETE /api/projects/{project_id}

POST   /api/projects/{project_id}/import
POST   /api/projects/{project_id}/process
GET    /api/projects/{project_id}/jobs/{job_id}

GET    /api/projects/{project_id}/photos
GET    /api/projects/{project_id}/photos/{photo_id}
PATCH  /api/projects/{project_id}/photos/{photo_id}

GET    /api/projects/{project_id}/groups
GET    /api/projects/{project_id}/groups/{group_id}

POST   /api/projects/{project_id}/export
GET    /api/projects/{project_id}/export/{export_id}
```

## 14. Processing Pipeline

Implement the processing pipeline as separate stages:

### Stage 1: Import

- Register source files.
- Validate file type.
- Store file metadata.
- Create database records.

### Stage 2: Thumbnail Generation

- Generate small thumbnails for grid view.
- Generate medium previews for review.
- Cache generated files.

### Stage 3: Metadata Extraction

- Extract EXIF metadata.
- Parse capture time.
- Parse camera model and lens model.
- Store focal length, aperture, shutter speed, and ISO when available.

### Stage 4: Technical Scoring

- Compute sharpness using Laplacian variance or a similar method.
- Estimate exposure from histogram distribution.
- Estimate contrast from luminance statistics.
- Estimate noise risk from high-frequency patterns.

### Stage 5: Embedding Generation

- Resize image for model input.
- Run embedding model.
- Store embedding vector in a local cache or database-friendly format.

### Stage 6: Similarity Grouping

- Sort photos by capture time or filename.
- Compare nearby images using embedding cosine similarity.
- Create duplicate or similar-photo groups.
- Assign each photo to a group.

### Stage 7: Ranking and Recommendation

- Compute final score.
- Select the representative photo for each group.
- Assign AI recommendation.
- Generate rule-based explanation.

## 15. Export Requirements

Support these MVP export modes:

1. Export selected files into a folder.
2. Export selected files into a ZIP archive.
3. Export a CSV file containing filename, status, star rating, group id, and score.

Future export modes:

- Lightroom-compatible XMP sidecar rating.
- Capture One compatible metadata.
- Copy only Picks and Maybes to a target folder.

## 16. Performance Requirements

The MVP should be designed for batches of 500 to 2,000 JPEG images.

Performance goals:

- Thumbnail generation should stream progress to the UI.
- The UI should remain responsive during processing.
- Processing should be restartable if interrupted.
- Previously processed images should not be reprocessed unless the source file changes.
- Large image previews should be lazy-loaded.

## 17. Privacy and Safety Requirements

- Do not upload original photos to any remote service in the MVP.
- Do not modify original photos.
- Keep project metadata local.
- Clearly show where exported files are written.
- Provide a clear warning before deleting any generated cache or project metadata.
- Do not implement automatic deletion of original photos.

## 18. Development Milestones

### Milestone 1: Project Skeleton

Deliverables:

- Next.js frontend app.
- FastAPI backend app.
- Local development scripts.
- Basic README.
- Basic project creation API.
- SQLite database setup.

Acceptance criteria:

- Frontend and backend can be started locally.
- A new project can be created and listed.

### Milestone 2: Image Import and Thumbnail Generation

Deliverables:

- Multi-image upload.
- Image validation.
- Thumbnail generation.
- Preview generation.
- Photo grid UI.

Acceptance criteria:

- User can import JPEG, PNG, and WebP images.
- User can see generated thumbnails in the browser.

### Milestone 3: Metadata and Technical Scoring

Deliverables:

- EXIF extraction.
- Sharpness score.
- Exposure score.
- Contrast score.
- Overall technical score.
- Score display in UI.

Acceptance criteria:

- Each photo shows basic metadata and technical scores.
- Blurry photos should generally receive lower sharpness scores than clear photos.

### Milestone 4: Similarity Grouping

Deliverables:

- Image embedding pipeline.
- Similarity comparison.
- Similar-photo group creation.
- Group view UI.

Acceptance criteria:

- Burst or near-duplicate photos are grouped together.
- Each group has a representative photo.

### Milestone 5: AI Recommendation and Manual Review

Deliverables:

- Ranking inside each group.
- Pick, Maybe, Reject status.
- Keyboard shortcuts.
- Rule-based explanation.
- Review progress indicator.

Acceptance criteria:

- User can quickly review photos using keyboard shortcuts.
- AI recommendations can be overridden manually.

### Milestone 6: Export

Deliverables:

- Export selected photos to folder.
- Export selected photos to ZIP.
- Export CSV selection list.

Acceptance criteria:

- User can export final Picks.
- Exported CSV correctly reflects user decisions.

### Milestone 7: Polish and Reliability

Deliverables:

- Error handling.
- Empty states.
- Progress indicators.
- Basic tests.
- Documentation.

Acceptance criteria:

- The app handles failed image imports gracefully.
- The processing pipeline can be resumed.
- The README explains how to run and use the app.

## 19. Testing Plan

### 19.1 Unit Tests

Test:

- Metadata parsing.
- Score normalization.
- Similarity calculation.
- Group creation logic.
- Ranking logic.
- Export logic.

### 19.2 Integration Tests

Test:

- Project creation.
- Image import.
- Processing pipeline.
- Photo status update.
- Export workflow.

### 19.3 Manual Test Dataset

Create a small local test dataset with:

- Sharp images.
- Blurry images.
- Underexposed images.
- Overexposed images.
- Similar burst photos.
- Portrait photos with open and closed eyes, if available.

Do not commit private or copyrighted photos to the repository. Use synthetic or public-domain test images only.

## 20. Suggested Repository Structure

```text
frame-pilot/
  apps/
    web/
      package.json
      src/
    api/
      pyproject.toml
      app/
        main.py
        api/
        core/
        db/
        models/
        services/
        workers/
        image/
        ai/
  packages/
    shared/
  docs/
    architecture.md
    api.md
    scoring.md
  scripts/
  README.md
  develop_plan.md
```

## 21. Implementation Rules for Codex

When implementing this project, follow these rules:

1. Keep the MVP small and functional.
2. Do not implement account login or cloud upload.
3. Do not modify original user photos.
4. Prefer simple deterministic algorithms before adding complex AI models.
5. Keep the scoring logic explainable.
6. Use TypeScript on the frontend.
7. Use Python type hints on the backend.
8. Add tests for core scoring, grouping, and export logic.
9. Keep large model files out of the repository.
10. Document how to download or configure optional models.
11. Make all scripts runnable from the repository root.
12. Use English for all code, comments, documentation, and commit messages.

## 22. Future Roadmap

After the MVP is stable, consider adding:

- RAW preview extraction.
- HEIC support.
- Face-aware portrait ranking.
- Closed-eye detection.
- Personalized user preference learning.
- Lightroom XMP sidecar export.
- Local desktop packaging with Tauri or Electron.
- Browser-side inference using ONNX Runtime Web.
- GPU acceleration for embedding generation.
- Photo style clustering.
- Smart album generation.
- Before-and-after comparison mode.

## 23. References

These references justify the product direction and technical approach:

- Existing AI culling tools commonly detect out-of-focus frames, motion blur, closed eyes, poor expressions, near-duplicates, and exposure failures.
- Some AI culling tools group duplicate or near-duplicate photos by pose and scene similarity.
- The browser File System Access API can allow web apps to read from and write to local files and directories after user permission.
- ONNX Runtime Web supports running ONNX models in browser-based applications, which can be explored after the backend-first MVP is stable.

## 24. Definition of Done for MVP

The MVP is complete when:

- A user can create a local project.
- A user can import at least 500 JPEG images.
- The system can generate thumbnails and previews.
- The system can compute technical scores.
- The system can group similar images.
- The system can recommend the best photo in each group.
- The user can manually mark Pick, Maybe, or Reject.
- The user can export selected photos and a CSV list.
- Original photos are never modified.
- The project can be run locally from documented commands.
