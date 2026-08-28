# API

> 语言：[English](api.md) | **中文**

开发期间的基础 URL：`http://127.0.0.1:8000`。

`GET /health` 和 `GET /api/health` 返回 `status`、`version` 和 `service`。`version` 是 API 的 `APP_VERSION` 值。Playwright 和桌面 sidecar 探测无前缀的 `/health` URL，作为 2xx 检查。

已实现的端点：

```text
GET    /health
GET    /api/health

POST   /api/projects
GET    /api/projects
GET    /api/projects/{project_id}
DELETE /api/projects/{project_id}

GET    /api/desktop/project-roots
POST   /api/desktop/project-roots

POST   /api/projects/{project_id}/imports
POST   /api/projects/{project_id}/imports/from-paths
POST   /api/projects/{project_id}/process
GET    /api/projects/{project_id}/jobs
GET    /api/projects/{project_id}/jobs/{job_id}
POST   /api/projects/{project_id}/jobs/{job_id}/cancel
POST   /api/projects/{project_id}/jobs/{job_id}/retry

GET    /api/projects/{project_id}/photos
GET    /api/projects/{project_id}/photos/status-counts
GET    /api/projects/{project_id}/photos/{photo_id}
PATCH  /api/projects/{project_id}/photos/{photo_id}
PATCH  /api/projects/{project_id}/photos/batch

GET    /api/projects/{project_id}/groups
GET    /api/projects/{project_id}/groups/{group_id}

POST   /api/projects/{project_id}/exports
GET    /api/projects/{project_id}/exports
GET    /api/projects/{project_id}/exports/{export_id}
GET    /api/projects/{project_id}/exports/{export_id}/download
```

生成的缩略图和预览通过以下路径提供：

```text
GET /api/assets/{project_id}/{thumbnails|previews}/{filename}
```

## 项目响应

项目响应包含图像总数和处理元数据：

```json
{
  "id": "project-id",
  "name": "Weekend shoot",
  "root_path": ".../.framepilot-data/projects/project-id",
  "source_mode": "copy",
  "source_root_path": null,
  "total_images": 12,
  "processed_images": 10,
  "last_processed_at": "2026-06-02T12:00:00Z",
  "schema_version": 2,
  "active_import_job": null,
  "created_at": "2026-06-02T11:30:00Z",
  "updated_at": "2026-06-02T12:00:00Z"
}
```

`last_processed_at` 在第一次处理作业完成前为 `null`。v2 当前使用 `copy` 模式，将导入的照片复制到本地项目目录，且不修改原始源文件。
`active_import_job` 是该项目最新的、非过期的排队或运行中导入作业；当导入衍生工作未在进行时为 `null`。项目列表和仪表板使用这个轻量字段，把处于活动导入的项目导回导入进度，而不是处理或筛选。
当 `POST /api/projects` 省略 `root_path` 或将其发送为空时，FramePilot 使用默认的托管项目目录。项目创建 UI 将其作为可选的本地项目数据文件夹字段暴露。自定义 `root_path` 必须是 `{data_dir}/projects` 下可用的本地目录、`FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` 条目，或通过 `POST /api/desktop/project-roots` 注册的文件夹。无效存储路径会在创建项目元数据之前返回 `422`。

`GET` 和 `POST /api/desktop/project-roots` 仅在 `FRAMEPILOT_DESKTOP=1` 时存在；否则返回 `404`。`POST` 接受 `{"path": "/absolute/folder"}`，要求该目录已存在；会拒绝被拦截的系统路径、文件系统锚点、数据目录以及数据目录的父目录，并在 `{data_dir}/desktop_project_roots.json` 中最多存储 50 条解析后的路径。`GET` 返回 `{"roots": [...]}`。该注册表以文件为后端，不存储在 Settings 中。

`DELETE /api/projects/{project_id}` 从应用数据库中移除该项目及相关本地元数据记录。它不会从磁盘删除项目文件夹、已复制的原片、生成的预览或导出产物。

## 导入响应

`POST /api/projects/{project_id}/imports` 在 `files` 表单字段下接受多个文件。每个请求最多包含 100 个文件。更大的选择应分块上传，并共享同一个逻辑导入作业。

可选表单字段：

- `job_id`：将此分块追加到已有的运行中导入作业
- `expected_total`：所有分块的文件总数，用于进度显示
- `finalize`：`true`（默认）开始为待处理照片生成衍生文件；`false` 保持作业打开以接收更多分块

新导入在没有 `job_id` 时，若该项目已有另一个活动导入作业，则返回 `409`。

响应包含已接受的照片记录、同步跳过的文件、导入计数，以及用于轮询的导入作业。新接受的照片可能仍将 `processing_state` 设为 `processing`，并且在后台衍生作业完成前，可能尚未填充缩略图、预览、元数据、分数、哈希或嵌入字段。

```json
{
  "imported": [
    {
      "id": "photo-id",
      "filename": "frame.jpg",
      "file_ext": ".jpg",
      "file_size": 2481203,
      "file_mtime": 1780411200.0,
      "content_hash": "sha256-hex",
      "project_copy_path": ".../originals/frame.jpg",
      "source_identity": "sha256:sha256-hex",
      "capture_time": null,
      "camera_model": null,
      "lens_model": null,
      "focal_length": null,
      "aperture": null,
      "shutter_speed": null,
      "iso": null,
      "perceptual_hash": null,
      "thumbnail_path": null,
      "preview_path": null,
      "processing_state": "processing",
      "processing_error": null,
      "user_status": "Unreviewed",
      "ai_recommendation": "Unreviewed"
    }
  ],
  "skipped": [
    {
      "filename": "notes.txt",
      "reason": "Only JPEG, PNG, and WebP files are supported"
    }
  ],
  "total_files": 2,
  "accepted_files": 1,
  "skipped_files": 1,
  "failed_files": 1,
  "job": {
    "id": "job-id",
    "project_id": "project-id",
    "job_type": "import",
    "status": "running",
    "current_step": "derivative_generation",
    "total_items": 2,
    "processed_items": 0,
    "failed_items": 1,
    "progress_percent": 50.0,
    "error_message": null,
    "cancellation_requested": false,
    "cancelled_at": null,
    "started_at": "2026-06-02T12:00:00Z",
    "completed_at": null,
    "retryable": false
  }
}
```

导入端点以上传/登记为界：它在受支持的文件已复制到项目、文件身份元数据已记录、照片行已创建或安全复用、并且已创建导入作业之后返回。昂贵的衍生生成、元数据提取、评分、感知哈希和嵌入生成会继续在 FastAPI 进程内后台任务中进行，该任务打开新的数据库会话。轮询 `GET /api/projects/{project_id}/jobs/{job_id}`，直到导入作业到达 `complete`、`complete_with_errors`、`failed` 或 `cancelled`，然后重新加载照片，再假定预览或分数已就绪。

这条后台路径改善了请求响应性和可见进度，但不能在 API 进程退出后持久存活。要在后端重启后自动恢复被中断的衍生作业，需要持久化的本地工作器。

导入作业状态为：

- `complete`：所有所选文件已导入或被安全复用。
- `complete_with_errors`：至少一个文件已导入或被安全复用，并且至少一个文件在衍生生成期间被跳过或失败。
- `failed`：每个所选文件都被跳过，或每个被接受的文件在衍生生成中都失败。
- `cancelled`：用户请求了协作式取消，本地后台工作器在安全检查点停止。

如果同步校验期间每个文件都被跳过，端点返回 `422`，失败的导入作业仍可通过 `GET /api/projects/{project_id}/jobs` 看到。导入新照片会使先前的分组和 AI 推荐失效，因此应在导入作业到达终态后再重新运行处理。以相同的上传文件名和 SHA-256 内容哈希再次导入文件时，若现有项目照片记录以及已生成的缩略图/预览仍然存在，则复用它们；这不会创建重复记录，也不会重置用户审阅状态。
multipart 响应包含 `remaining_paths: []`，并将 `expanded_total` 设为该请求中的文件数，以便浏览器客户端可以忽略这些字段。

单数路由 `/api/projects/{project_id}/import` 仍作为向后兼容别名可用。

## 路径导入

`POST /api/projects/{project_id}/imports/from-paths` 复制 API 已经可以读取的本地文件。它不会通过浏览器 File API 上传照片字节。请求 JSON：

```json
{
  "paths": ["/abs/folder", "/abs/file.jpg"],
  "job_id": null,
  "expected_total": null,
  "finalize": true
}
```

API 先将目录展开为普通文件，然后在该 HTTP 请求中最多消费 100 个展开后的文件。因此一个包含 250 张照片的文件夹是三次请求（100 + 100 + 50），绝不是一次调用。输入或展开文件上限被超出、相对路径、缺失路径或空的 `paths` 列表会返回 `422`。

`expanded_total` 是所提交 `paths` 的完整展开计数（250 个文件的文件夹在第一次请求上为 250），不是 100 文件切片大小。`remaining_paths` 是按确定性顺序剩余的展开**文件**路径——不是原始文件夹路径。250 个文件的文件夹在第一次响应中 `len(remaining_paths) == 150`，然后是 50，然后是 `[]`。

使用同一个 `job_id` 的客户端循环：

1. POST 文件夹或文件列表。如果选择可能超过 100 个展开文件，发送 `finalize: false`。
2. 读取 `remaining_paths`、`expanded_total` 和 `job.id`。
3. 使用同一个 `job_id` 重新 POST `remaining_paths`，并将 `expected_total` 设为第一次的 `expanded_total`。
4. 仅在最后一片、当本次请求消费剩余文件时发送 `finalize: true`。

作业控制与 multipart 导入一致：没有该 `job_id` 的新导入在另一个导入活动时返回 `409`；`expected_total` 会更新 `job.total_items`。每个被消费的文件以 `rb` 打开，并经过现有的登记/复制路径复制。源文件永不被修改、删除或硬链接。当 `finalize` 为 true、给定的是单个输入目录、且 `source_root_path` 为空时，API 将该目录存为只读项目元数据。它不会重新扫描该文件夹。
当 EXIF 数据可用时，后台衍生作业会记录基本的拍摄时间、相机、镜头、焦距、光圈、快门速度和 ISO 元数据。数值型 EXIF 有理数会规范化为稳定的显示字符串。
HEIC 和 RAW 扩展名（如 `.heic`、`.dng`、`.arw`、`.cr3` 和 `.nef`）被识别为计划中的未来格式，但 v2 当前会以明确的不支持格式原因跳过它们，而不是尝试本地解码。

## 作业

`POST /api/projects/{project_id}/process` 创建本地后台处理作业，并以 `202 Accepted` 返回一个 `ProcessingJob`。轮询 `GET /api/projects/{project_id}/jobs/{job_id}`，直到作业到达 `complete` 或 `failed`。
如果同一项目有排队或正在运行的导入作业，处理端点返回 `409 Conflict`，而不是启动处理：

```json
{
  "detail": {
    "message": "Import is still running for this project. Wait for the import job to finish before processing.",
    "job_id": "import-job-id"
  }
}
```

导入作业到达 `complete`、`complete_with_errors`、`failed` 或 `cancelled` 等终态后，处理可以开始。
如果更早的排队或运行中处理作业超过 10 分钟没有更新，项目和作业端点会将该过期作业标记为失败。过期处理清理会清除部分分组，移除照片分组分配，将已处理或进行中的照片恢复为带中断原因的可重试 `imported` 状态，并将项目已处理计数重置为零。之后的处理请求可以启动替换作业，并从已导入照片集重建分组。API 启动时也会在进程重启后立即将残留的活动作业标记为失败。

`GET /api/projects/{project_id}/jobs` 按最新优先返回项目作业，包括 `import` 和 `processing` 作业。可选的 `limit` 和 `offset` 查询参数可以为大型作业历史分页。导入 UI 在上传/登记返回后轮询返回的导入作业；处理 UI 使用作业历史，在页面重新加载或导航后继续轮询排队或运行中的处理作业。如果排队或正在运行的导入作业超过 10 分钟没有更新，作业端点会将其标记为失败，并将 `current_step` 设为 `failed - stale`；这可以防止中断的本地导入永远保持活动，同时又不会重试或修改照片。

`POST /api/projects/{project_id}/jobs/{job_id}/cancel` 为排队或正在运行的导入作业请求协作式取消。它设置 `cancellation_requested`，并以 `202 Accepted` 返回更新后的作业；终态导入作业作为安全空操作以 `200 OK` 返回。该端点不会杀死 API 进程、删除原始文件、删除已复制的原片，或移除已生成的衍生文件。后台工作器在每张照片之前以及每次照片级衍生/评分/哈希处理后检查该请求，到达安全检查点后将作业标记为 `cancelled`，并记录 `cancelled_at` 和 `completed_at`。已经完成的照片衍生文件保持缓存，未处理的照片保持可重试。

`POST /api/projects/{project_id}/jobs/{job_id}/retry` 重试失败、`complete_with_errors` 或 `cancelled` 的导入作业。它创建新的本地导入作业，并对生成的缩略图或预览缺失、或导入状态仍为 `processing` 或 `failed` 的项目照片重新运行衍生/评分/哈希/嵌入工作。它不会重新登记已上传的文件、创建重复的照片记录、重置 `user_status`、重置 `star_rating`、删除已生成的衍生文件、删除已复制的原片，或修改源照片。现有有效的缩略图和预览文件会被复用；缺失的衍生文件会尽可能从本地已复制的原片重新生成。如果部分照片恢复而其他照片无法重建，重试作业以 `complete_with_errors` 完成，并在受影响的照片上记录失败项。如果另一个导入作业已经排队或正在运行，重试返回 `409`。

作业包含：

```json
{
  "id": "job-id",
  "project_id": "project-id",
  "job_type": "processing",
  "status": "running",
  "current_step": "ranking group 1 of 3",
  "total_items": 12,
  "processed_items": 4,
  "failed_items": 0,
  "progress_percent": 33.33,
  "error_message": null,
  "cancellation_requested": false,
  "cancelled_at": null,
  "started_at": "2026-06-02T12:00:00Z",
  "completed_at": null,
  "retryable": false
}
```

已完成的作业表示已为当前导入照片集重建分组、排序和推荐解释。
如果项目已经完全处理且未变更，新的处理作业会完成，并将 `current_step` 设为 `complete - no changes`，现有分组保持不动。

每张照片还暴露本地处理状态：

- `imported`：照片已导入，正在等待分组/排序。
- `processing`：当前处理作业正在处理该照片。
- `processed`：该照片的分组/排序已完成。
- `failed`：作业跳过该照片并记录了 `processing_error`。

处理在分组前校验生成的缩略图和预览文件。缺失的衍生文件会尽可能从本地已复制的原片重新生成；无法恢复的衍生失败会记录为失败的照片项，而不是让整个作业失败。
如果整个处理作业在各张照片完成前失败，部分分组会被清除，已经标记为 `processed` 或仍在进行中的照片会带着中断原因回到 `imported`，以便下一次处理运行可以重试它们。

`GET /api/projects/{project_id}/photos` 按分组、AI 推荐优先级、分数和文件名的审阅顺序返回照片。可选的 `limit` 和 `offset` 查询参数可以为大型项目分页；省略它们则保留完整列表响应。筛选工作区请求初始有界页以加快首次渲染，并在需要完整的浏览器内上下文时暴露显式的完整加载操作。

`GET /api/projects/{project_id}/photos/status-counts` 返回轻量的审阅状态总计，而不填充完整照片记录：

```json
{
  "Pick": 12,
  "Maybe": 8,
  "Reject": 20,
  "Unreviewed": 60
}
```

导出 UI 使用该端点，在提交导出请求前为大型项目计算所选计数。

`PATCH /api/projects/{project_id}/photos/{photo_id}` 和 `PATCH /api/projects/{project_id}/photos/batch` 更新审阅状态和星级评分。请求必须至少包含 `user_status` 或 `star_rating` 之一。筛选工作区中的批量操作作用于当前已加载照片中的过滤/分组范围；当工作区仅部分加载时，批量标记会在应用前加载整个项目，因此无需先单独点击“加载全部”即可完成全项目批量。键盘审阅仍使用当前已加载分页，直到用户显式加载全部照片。

`GET /api/projects/{project_id}/groups` 按稳定的创建顺序返回分组，供逐组审阅。可选的 `limit` 和 `offset` 查询参数可以为大型分组列表分页。筛选工作区请求初始有界页，并在分组列表可能继续时暴露显式的完整加载操作。每个分组包含一个 JSON `score_summary` 字符串，含顶部照片 id、最高分、分数差距、置信度标签、推荐计数，以及简短的确定性解释。

分组响应示例：

```json
{
  "id": "group-id",
  "project_id": "project-id",
  "group_type": "duplicate",
  "representative_photo_id": "photo-id",
  "photo_count": 2,
  "score_summary": "{\"best_score\": 0.82, \"confidence\": \"medium\", \"explanation\": \"Medium confidence because the top photo leads the next candidate by 0.07.\", \"recommendation_counts\": {\"Maybe\": 1, \"Pick\": 1, \"Reject\": 0, \"Unreviewed\": 0}, \"score_gap\": 0.07, \"top_photo_id\": \"photo-id\"}"
}
```

## 导出

`POST /api/projects/{project_id}/exports` 接受：

```json
{
  "mode": "csv",
  "statuses": ["Pick", "Maybe"]
}
```

支持的模式为 `csv`、`folder` 和 `zip`。支持的状态为 `Pick`、`Maybe`、`Reject` 和 `Unreviewed`。状态过滤器按该支持顺序去重存储。

响应包含导出的照片数量和本地输出路径：

```json
{
  "id": "export-id",
  "project_id": "project-id",
  "mode": "csv",
  "status": "complete",
  "selected_count": 12,
  "processed_count": 12,
  "total_count": 12,
  "statuses": "[\"Pick\", \"Maybe\"]",
  "output_path": ".../exports/csv/selection-export-id.csv",
  "error_message": null,
  "completed_at": "2026-06-02T12:00:01Z",
  "created_at": "2026-06-02T12:00:00Z"
}
```

导出写入按模式划分的本地项目目录：`exports/csv/`、`exports/zip/` 和 `exports/folders/`。重复导出会使用唯一路径。没有匹配照片的请求返回 `422`，并且不写入导出产物。如果任何所选本地原片副本缺失，或所选源路径解析到项目本地 `originals/` 目录之外，ZIP 和文件夹导出失败。缺失文件失败会在响应 detail 和导出历史错误消息中保留缺失路径；项目原片包含性失败使用不含路径的安全消息。如果产物创建失败，API 返回 `500`，在可能时删除项目导出目录内的部分输出，并保留一条本地导出历史记录，将 `status` 设为 `failed` 且设置 `error_message`。

当导出处于 `running` 时，`processed_count` 与 `total_count` 会随着文件或 CSV 行写入而推进，便于客户端显示细粒度进度（例如 `Running (3/12)`）。完成后两个计数与 `selected_count` 一致。

CSV 导出包含文件名、项目照片 id、原始路径、项目副本路径、源身份、内容哈希、文件大小、文件 mtime、拍摄和相机元数据、用户状态、星级评分、分组 id、AI 推荐、总体和技术分数、人脸和睁眼信号、图像尺寸、推荐解释、处理状态和处理错误。

导出记录可以按最新优先列出：

```text
GET /api/projects/{project_id}/exports
```

响应是与创建响应相同形状的导出记录数组，按最新优先排序。可选的 `limit` 和 `offset` 查询参数可以为大型导出历史分页。Web 导出页使用该端点显示本地导出历史、所选计数、状态摘要、输出路径，以及 CSV 和 ZIP 记录的下载链接，先加载最近的记录，并在用户请求更早导出时提高有界限制。

已完成的 CSV 和 ZIP 导出可从以下路径下载：

```text
GET /api/projects/{project_id}/exports/{export_id}/download
```

文件夹导出可在其本地输出路径使用，不会作为单个产物下载。
失败或仍在运行的导出记录从下载端点返回 `409`。
单数 `/api/projects/{project_id}/export` 路由仍作为向后兼容别名可用。

XMP sidecar 导出在 v2.0 中未实现。计划中的做法记录在 [导出互操作](export_interoperability.zh.md)。

实验性的人脸和睁眼字段是来自简单颜色、形状、亮度和锐度检查的本地启发式分数。它们不是由捆绑的专业人脸检测模型生成的，应视为弱的 MVP 排序提示。
