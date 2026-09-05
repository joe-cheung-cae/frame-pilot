# FramePilot v2 开发计划

> 语言：[English](develop_plan.md) | **中文**

## 1. 项目概述

FramePilot v2 是一款本地优先、类桌面的 AI 辅助照片筛选应用，面向认真的爱好摄影师和半专业摄影师。它把 v1 MVP 从概念验证本地 Web 应用演进为更可靠、可扩展、面向工作流的照片筛选工具。

v2 的目标不是完全替代人的审美判断。目标是去掉明显的技术失败，将近重复和连拍序列分组，在每组内对候选排序，解释为何推荐某张照片，并提供快速的键盘优先复核体验。

主要产品陈述：

> FramePilot v2 帮助摄影师把数百或数千张相机照片变成干净、可复核的短名单，提供本地优先处理、可解释的推荐，以及专业筛选工作流支持。

### 1.1 当前交付状态与下一切片

本节是「已经交付什么」和「下一步实现什么」的活指针。后文 stretch 列表是历史产品意图；已经交付的 stretch 项不要当新工作重开。

`main` 上已经交付：

- v2.0 本地 JPEG/PNG/WebP 精选工作流（项目、导入、评分/分组/排序、键盘审阅、CSV/ZIP/文件夹导出）。
- `2.1.0-desktop` RC（未签名的 Tauri 2 + localhost Python sidecar）。不要当成已签名商店发行。
- 第六阶段 / 6.1 本地持久作业回收（`npm run worker` / `python -m app.worker`；`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` 默认开启）。
- 第七阶段协作式**处理作业取消**（J7.01–J7.06，[#148](https://github.com/joe-cheung-cae/frame-pilot/pull/148)）。暂停/恢复（J7.07）**不在**该阶段完成定义内。计划：[docs/plans/2026-09-03-phase7-processing-cancel.zh.md](docs/plans/2026-09-03-phase7-processing-cancel.zh.md)。
- 未签名 Windows NSIS GUI 生命周期 QA（[#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)，2026-09-04 按 Windows-only 关闭）。macOS DMG 为 skip（没有 Mac 主机）；skip 不是 macOS pass。
- 第八阶段本地 **HEIC/HEIF 静帧预览**（H8.01–H8.06，[#157](https://github.com/joe-cheung-cae/frame-pilot/pull/157)；[#151](https://github.com/joe-cheung-cae/frame-pilot/issues/151) 已关闭）。计划：[docs/plans/2026-09-04-heic-preview.zh.md](docs/plans/2026-09-04-heic-preview.zh.md)。原片 HEIC 原样拷贝；用 `pillow-heif` 解码；WebP 衍生件；在 RGB 上评分/分组。RAW 仍跳过。

**下一步：** 第九阶段剩余 stretch 收口，**每次运行一个 GitHub issue**（S9.00–S9.13）。计划：[docs/plans/2026-09-04-remaining-stretch.zh.md](docs/plans/2026-09-04-remaining-stretch.zh.md)。总览 [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160)。S9.00–S9.08 已落地（到导入并发 [#168](https://github.com/joe-cheung-cae/frame-pilot/issues/168)）；从 **S9.09 更改数据目录**（[#170](https://github.com/joe-cheung-cae/frame-pilot/issues/170)）开始。不要发明第十阶段。不要在同一次运行里实现 S9.10–S9.13。

队列：S9.01 导出取消 → S9.02 J7.07 暂停 → S9.03 AVIF → S9.04 RAW 预览 → S9.05 XMP（[#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165)；历史 [#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117)）→ S9.06 托盘 → S9.07 独立预览 → S9.08 并发旋钮 → S9.09 数据目录 → S9.10 可选更新 → S9.11 签名就绪 CI → S9.12 macOS DMG QA → S9.13 文档残留修复。

## 2. v1 现状与 v2 动机

FramePilot v1 已经提供可用的 MVP 工作流：

- 本地项目创建。
- JPEG、PNG 和 WebP 导入。
- 缩略图和预览生成。
- 基本元数据提取。
- 确定性技术评分。
- 轻量人脸与睁眼启发式信号。
- 简单近重复分组。
- Pick、Maybe、Reject 和 Unreviewed 状态。
- 键盘快捷键。
- CSV、文件夹和 ZIP 导出。
- 基本的 API、前端和 E2E 测试结构。

然而，v1 已不足以支撑真实摄影工作流，因为：

- 大批量处理仍然过于同步。
- 进度和恢复行为有限。
- 相似分组对真实连拍和旅行照片集仍然太弱。
- 人脸与睁眼检测是启发式的，不应当作可靠的人像筛选。
- 筛选工作区对数千张照片还不够快、也不够专业。
- 导出和互操作需要更强。
- 尚未支持 RAW 和 HEIC 工作流。
- 真实大批量测试和性能验证仍然不足。

v2 应保留可用的 v1 基础，但重新设计处理架构、工作流 UX、导出层和算法策略。

## 3. 产品定位

FramePilot v2 应定位为：

- 本地优先的照片筛选工具。
- 云端照片筛选服务的尊重隐私替代方案。
- 进入 Lightroom、Capture One、darktable 或手工后期之前的预编辑工作流工具。
- 受专业照片筛选工具启发的快速键盘优先复核工作区。
- 可解释的 AI 助手，而不是创作品味的自动裁判。

FramePilot v2 不应定位为：

- 云端照片管理器。
- 完整 RAW 编辑器。
- Lightroom 替代品。
- 社交画廊服务。
- 全自动删除工具。

## 4. v2 产品目标

### 4.1 核心目标

1. 可靠支持 500 到 2,000 张照片的真实本地筛选。
2. 保持原始照片文件安全，永不修改它们。
3. 提供可恢复的后台处理，并显示可见进度。
4. 提高近重复和连拍分组质量。
5. 改进排序和推荐解释。
6. 提供更快、更专业的筛选工作区。
7. 支持稳健的 CSV、ZIP、文件夹和面向 sidecar 的导出工作流。
8. 提高真实本地工作流和文件安全的测试覆盖。
9. 保持 v2 对由 Codex 协助的单人开发者现实可行。

### 4.2 延伸目标

这些目标值得拥有，但不应阻塞第一个 v2 发布：

- HEIC 支持。
- RAW 内嵌预览提取。
- 兼容 Lightroom 的 XMP sidecar 导出。
- 可选的轻量本地 AI 模型。
- 浏览器端 ONNX Runtime Web 推理。
- 使用 Tauri 或 Electron 的本地桌面打包。
- embedding 生成的 GPU 加速。
- 用户偏好学习。

## 5. 目标用户与工作流

### 5.1 主要用户

- 拍摄旅行、家庭、街头、风景、野生或活动照片的爱好摄影师。
- 需要在后期前更快预选工作流的半专业摄影师。
- 关心隐私并偏好本地处理的用户。
- 希望保留创作控制、而不是让 AI 做最终决定的用户。

### 5.2 核心用户场景

用户导入一个包含 1,000 张来自相机卡的 JPEG 照片的文件夹。FramePilot v2 扫描该文件夹，创建本地项目，生成缩略图和预览，计算图像质量信号，将相似帧分组，在每组内排序照片，并呈现键盘优先的筛选工作区。用户确认 Pick 和 Maybe，拒绝明显失败，并将所选结果导出为 CSV、ZIP、复制文件，或未来的 XMP sidecar 评分。

### 5.3 未来用户场景

用户导入一个包含 JPEG、HEIC 和 RAW 文件的混合文件夹。FramePilot 从 RAW 文件提取内嵌预览，在预览上完成本地筛选，写入 XMP sidecar 评分，并允许用户在 Lightroom 或其他 RAW 工作流工具中继续后期。

## 6. v2 范围

### 6.1 v2.0 纳入范围

v2.0 应聚焦可靠的本地 MVP-plus 工作流：

1. 项目创建与打开。
2. 面向文件夹的导入和多文件导入。
3. 更安全的项目存储和路径管理。
4. 后台或伪后台处理任务。
5. 可恢复的处理状态。
6. 增量缩略图和预览生成。
7. 确定性技术评分改进。
8. 更强的感知哈希和基于元数据的分组。
9. 改进的组内排序。
10. 保守且透明的推荐解释。
11. 专业筛选工作区改进。
12. 面向更大项目的虚拟化照片列表。
13. CSV、ZIP、文件夹导出和下载端点。
14. 真实集成测试和真实本地 smoke E2E 测试。
15. 架构、算法、测试和迁移文档。

### 6.2 从 v2.0 推迟

以下应规划，但不作为 v2.0 必需：

- 完整 RAW 解码。
- 完整色彩管理的 RAW 渲染。
- 云同步。
- 用户账户。
- 支付系统。
- 在线协作。
- 移动版本。
- 大型捆绑 AI 模型。
- 自动删除原始照片。

## 7. 支持的文件类型

### 7.1 v2.0 必需文件类型

支持并测试：

- JPEG
- PNG
- WebP

### 7.2 v2.x 计划文件类型

作为独立里程碑稍后添加：

- HEIC
- DNG
- Sony ARW
- Canon CR3
- Nikon NEF

RAW 和 HEIC 支持应仅在 v2 处理架构稳定之后实现。RAW 支持最初应聚焦内嵌预览提取，而不是完整 RAW 显影。

## 8. 本地优先与隐私要求

FramePilot v2 必须保持本地优先。

要求：

- 原始照片必须永不被修改。
- 原始照片必须永不被自动删除。
- v2.0 中任何照片都不得上传到任何远程服务器。
- 项目元数据必须本地存储。
- 生成的缩略图、预览、缓存文件和导出必须本地存储。
- 可选 AI 模型必须本地运行。
- 若以后加入可选模型下载，用户必须显式选择加入。
- UI 必须清楚说明项目数据和导出存放在何处。

基于浏览器的文件夹访问可在受支持处使用 File System Access API。File System Access API 允许 Web 应用在用户授权后与本地文件和目录交互；在生产中依赖它之前应检查浏览器支持。

## 9. v2 架构方向

### 9.1 从 v1 保留

保留以下 v1 基础：

- Monorepo 结构。
- Next.js、React、TypeScript 前端。
- FastAPI 后端。
- SQLite 本地元数据数据库。
- 现有 Project、Photo、PhotoGroup、ProcessingJob 概念。
- 现有导入、评分、分组、复核和导出概念。
- 现有本地优先安全规则。
- 现有英文代码、注释、测试和提交说明约定；活文档为双语（英文页面加上匹配的中文 `*.zh.md`）。

### 9.2 在 v2 中重构

重构这些区域：

- 处理流水线组织。
- 任务进度状态模型。
- 文件路径和存储布局处理。
- 分组和排序服务。
- 导出服务和下载处理。
- 前端数据获取和筛选工作区状态。
- 测试组织。
- 文档结构。

### 9.3 在 v2 中更深入重新设计

更深入重新设计这些区域：

- 长时间处理架构。
- 恢复和增量处理。
- 相似分组策略。
- 专业筛选工作区 UX。
- 大批量渲染和虚拟化。
- 导出互操作策略。
- 算法配置和可解释性。

## 10. 后端架构

### 10.1 API 层

后端应继续使用 FastAPI。

推荐的 API 分组：

```text
/api/projects
/api/projects/{project_id}/imports
/api/projects/{project_id}/jobs
/api/projects/{project_id}/photos
/api/projects/{project_id}/groups
/api/projects/{project_id}/exports
/api/assets
/api/health
```

v2 应避免不必要的破坏性变更，但如果测试和文档已更新，API 路由可以重组。

### 10.2 数据模型

核心数据模型应包括：

#### Project

- id
- name
- root_path
- source_mode
- source_root_path
- created_at
- updated_at
- total_images
- processed_images
- last_processed_at
- schema_version

#### Photo

- id
- project_id
- original_path
- project_copy_path
- source_identity
- filename
- file_ext
- file_size
- file_mtime
- content_hash
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
- perceptual_hash
- embedding_path
- sharpness_score
- blur_score
- exposure_score
- contrast_score
- noise_score
- face_signal_score
- eye_open_signal_score
- aesthetic_score
- overall_score
- ai_recommendation
- recommendation_explanation
- user_status
- star_rating
- group_id
- processing_state
- processing_error
- created_at
- updated_at

#### PhotoGroup

- id
- project_id
- group_type
- representative_photo_id
- photo_count
- score_summary
- created_at
- updated_at

#### ProcessingJob

- id
- project_id
- job_type
- status
- current_step
- total_items
- processed_items
- failed_items
- progress_percent
- error_message
- started_at
- completed_at
- created_at
- updated_at

#### ExportRecord

- id
- project_id
- export_type
- status_filter
- output_path
- download_path
- selected_count
- created_at
- completed_at
- error_message

### 10.3 存储布局

使用如下本地项目布局：

```text
frame-pilot-project/
  project.db
  originals/
  thumbnails/
  previews/
  cache/
    hashes/
    embeddings/
    jobs/
  exports/
    csv/
    zip/
    folders/
  logs/
```

v2 应支持两种存储模式：

1. 复制模式：把原片复制进项目目录。
2. 引用模式：原片留在原地，只存储引用。

复制模式对自包含项目更安全。引用模式对大型照片库更高效。v2.0 可以先实现复制模式，并为稍后的引用模式设计数据模型。

### 10.4 处理流水线

v2 流水线应分阶段：

1. 扫描源文件。
2. 登记或更新照片记录。
3. 校验支持的文件类型。
4. 生成或复用缩略图。
5. 生成或复用预览。
6. 提取或更新元数据。
7. 计算或复用哈希。
8. 计算技术分数。
9. 计算可选 embedding。
10. 将相似照片分组。
11. 在组内对照片排序。
12. 生成解释。
13. 持久化结果并更新任务状态。

每个阶段应在适用时更新 `ProcessingJob.current_step`、`processed_items`、`total_items` 和 `error_message`。

### 10.5 后台处理策略

v2 不应立即引入沉重的分布式队列。

推荐的 v2.0 做法：

- 使用 FastAPI 后台任务或进程内 worker 抽象。
- 把任务记录保存在 SQLite。
- 由前端轮询任务状态。
- 在可能时使每个处理步骤幂等。
- 仅支持重新处理缺失或过期的派生数据。
- 通过快速返回任务 id 避免长时间请求超时。

上述 v2.0 原文之后已经交付：

- 本地 worker 入口：`npm run worker` / `python -m app.worker`（第六阶段）。
- 协作式**导入**取消（现有 cancel 路由）。
- 残留导入/处理作业的启动回收（第六阶段 6.1 默认开启）。
- 同一 cancel 路由上的协作式**处理**取消（第七阶段，J7.01–J7.06）。见 [docs/plans/2026-09-03-phase7-processing-cancel.zh.md](docs/plans/2026-09-03-phase7-processing-cancel.zh.md)。
- 本地 HEIC/HEIF 静帧预览（第八阶段，H8.01–H8.06）。见 [docs/plans/2026-09-04-heic-preview.zh.md](docs/plans/2026-09-04-heic-preview.zh.md)。

**下一步：** 第九阶段剩余 stretch 收口，每次运行一个 issue。见 [§1.1](#11-当前交付状态与下一切片)。不要发明第十阶段。

在对应 S9 issue 完成前仍推迟：

- RQ、Dramatiq 或 Celery（仅在有实测需要时；不在 S9 内）。
- 分组过程中暂停/恢复（S9.02 / J7.07；恢复仍是 clear-and-rerun）。
- 导出作业取消（S9.01）与导出回收（不在 S9 内）。
- RAW 内嵌预览（S9.04）、AVIF（S9.03）、XMP（S9.05）、签名就绪 CI（S9.11）。

## 11. 前端架构

### 11.1 框架

继续使用：

- Next.js
- React
- TypeScript
- Tailwind CSS
- TanStack Query
- 用于本地工作区状态的 Zustand 或 Jotai

### 11.2 主要页面

v2 应提供：

1. 首页。
2. 项目仪表盘。
3. 项目创建页。
4. 导入和扫描页。
5. 处理监视页。
6. 筛选工作区。
7. 导出页。
8. 设置页。
9. 帮助和键盘快捷键页。

### 11.3 筛选工作区要求

筛选工作区是最重要的 v2 前端区域。

它应包括：

- 带有分组、过滤和项目进度的左侧边栏。
- 中央预览区。
- 底部虚拟化胶片条。
- 右侧分数和解释面板。
- 带有状态、导出和视图控件的顶部工具栏。
- 快速键盘导航。
- 感知组的导航。
- 缩放控件。
- 相似帧的对比模式。
- 清晰的 Pick、Maybe、Reject 和 Unreviewed 指示。
- 星级支持。
- 批量操作。
- 持久化的复核进度。

### 11.4 键盘快捷键

必需快捷键：

- Left arrow：上一张照片。
- Right arrow：下一张照片。
- Up arrow：上一组。
- Down arrow：下一组。
- P：标记 Pick。
- M：标记 Maybe。
- X：标记 Reject。
- U：标记 Unreviewed。
- 1 to 5：指定星级。
- 0：清除星级。
- Space：切换大预览。
- Z：切换缩放。
- C：对比模式。
- G：分组视图。
- F：过滤菜单。
- E：导出。

### 11.5 大批量 UI 要求

对于 2,000+ 张照片，前端必须避免一次渲染全部内容。

要求：

- 使用虚拟化列表或网格。
- 懒加载预览。
- 缓存活动组数据。
- 避免每次状态变更后重新获取全部照片。
- 对状态和评分变更使用乐观更新。
- 提供清晰的加载和错误状态。

## 12. 算法策略

### 12.1 确定性优先

v2 应把确定性算法作为基线，因为它们透明、快速且可测试。

必需的确定性信号：

- 锐度分数。
- 模糊风险分数。
- 曝光分数。
- 对比度分数。
- 噪声风险分数。
- 感知哈希。
- 时间和文件名邻近。
- 元数据相似性。

### 12.2 相似分组 v2

分组策略应结合：

- 拍摄时间邻近。
- 文件名序列邻近。
- 感知哈希距离。
- 图像尺寸。
- 相机型号。
- 镜头和焦距。
- 可选 embedding 相似度。

推荐的首个 v2 算法：

1. 按拍摄时间排序，缺失时回退到文件名。
2. 用时间和文件名邻近构建候选窗口。
3. 在候选窗口内计算感知哈希距离。
4. 用 union-find 把照片合并成组。
5. 若时间间隔过大则拆分组。
6. 按组内排序选择代表照片。
7. 持久化分组置信度和解释。

### 12.3 排序 v2

排序应可配置且可解释。

初始公式：

```text
final_score =
    0.30 * sharpness_score
  + 0.20 * exposure_score
  + 0.15 * contrast_score
  + 0.10 * noise_quality_score
  + 0.15 * face_signal_score
  + 0.10 * aesthetic_score
```

公式必须按照片类型调整：

- 类人像照片：提高人脸信号权重，但除非使用真实模型，否则将其标为实验性。
- 类风景照片：提高曝光、对比度和锐度权重。
- 低置信度组：避免激进的 Reject 推荐。

### 12.4 推荐解释

解释应基于规则且保守。

示例：

```text
Recommended because it is the sharpest image in this similar-photo group and has balanced exposure.
```

```text
Marked as Maybe because it is a single-image group with acceptable sharpness but low contrast.
```

```text
Rejected because it is visually similar to a sharper frame and has a higher blur risk.
```

```text
Face signal is experimental and should be reviewed manually.
```

### 12.5 可选 AI 模型

可选 AI 模型只能在确定性 v2 稳定之后加入。

可能的模型领域：

- 图像 embedding。
- 人脸检测。
- 睁眼检测。
- 美感评分。
- 主体检测。

规则：

- 不要把大模型文件提交到仓库。
- 模型必须是可选下载或单独配置的资源。
- 仅本地推理。
- 提供 CPU 回退。
- 清楚记录模型来源、许可证、体积和预期性能。

ONNX Runtime Web 以后可用于浏览器端推理，而后端侧 ONNX Runtime 对 v2.0 可能更简单。ONNX Runtime Web 通过 `onnxruntime-web` 包支持浏览器内推理。

## 13. 导出与互操作

### 13.1 必需的 v2 导出模式

v2 应支持：

1. CSV 导出。
2. ZIP 导出。
3. 把所选照片复制到文件夹。
4. CSV 和 ZIP 导出的下载端点。
5. UI 中的导出状态摘要。

### 13.2 未来导出模式

规划：

- XMP sidecar 评分。
- 兼容 Lightroom 的选择工作流。
- 兼容 Capture One 的元数据工作流。
- 仅导出所选文件名。
- 导出被拒绝的文件名，供在 FramePilot 之外手工删除。

FramePilot 必须永不自动删除原片。如果以后加入删除支持，它必须是带确认的、明确分离的手工工作流。

## 14. 测试策略

### 14.1 后端单元测试

测试：

- 元数据解析。
- 分数归一化。
- 感知哈希生成。
- 相似距离。
- 分组创建。
- 分组拆分。
- 排序公式。
- 推荐解释。
- 导出文件生成。
- 文件安全。

### 14.2 后端集成测试

使用临时目录和生成的合成图像。

测试：

- 项目创建。
- 导入。
- 缩略图生成。
- 预览生成。
- 处理任务创建。
- 任务状态轮询。
- 照片列表。
- 分组列表。
- 状态更新。
- CSV 导出。
- ZIP 导出。
- 导出下载端点。
- 不支持文件处理。
- 原始文件不可变性。

### 14.3 前端测试

测试：

- 项目创建 UI。
- 导入 UI。
- 处理进度 UI。
- 筛选工作区过滤。
- 键盘快捷键。
- 状态更新。
- 导出面板。
- 错误和空状态。

### 14.4 E2E 测试

保留两种 E2E 测试：

1. 用于快速 UI 回归的 mocked E2E。
2. 用于完整前端/后端工作流验证的真实本地 smoke E2E。

真实 smoke E2E 应仅使用生成的合成照片。

### 14.5 性能测试

为以下规模增加脚本级性能检查：

- 100 张照片。
- 500 张照片。
- 2,000 张照片。

第一个目标不是极致速度；第一个目标是不崩溃、内存不爆炸、进度可见、错误可恢复。

## 15. 文档计划

v2 应创建或更新这些文档：

```text
docs/v1_review_for_v2.md
docs/v2_product_requirements.md
docs/v2_architecture.md
docs/v2_milestones.md
docs/v2_algorithm_strategy.md
docs/v2_testing_strategy.md
docs/v2_migration_plan.md
docs/api.md
docs/scoring.md
README.md
AGENTS.md
```

文档必须保持实用且面向实现。

## 16. 开发里程碑

本节是历史 Goal Mode 排序（v2.0–v2.6）。现行下一步指针是 [§1.1](#11-当前交付状态与下一切片)。不要从本列表重开已交付项。交付上的第七阶段是处理作业取消（已交付），不是 §16.7。HEIC 静帧预览是交付第八阶段（`docs/plans/2026-09-04-heic-preview.zh.md`）并且已经交付。交付第九阶段是剩余 stretch S9.00–S9.13（`docs/plans/2026-09-04-remaining-stretch.zh.md`）。不要发明第十阶段。

### 16.1 v2.0 Foundation

目标：

使仓库可维护，并准备好结构化的 v2 开发。

任务：

- 审阅并保留 v1 功能。
- 确保格式化、lint、类型检查和测试可用。
- 创建或更新 v2 规划文档。
- 稳定开发者命令。
- 确认本地运行说明。

验收标准：

- `npm run test` 通过。
- `npm run test:e2e` 有文档，并在可行时通过。
- 格式化和 lint 命令有文档。
- v2 规划文档存在。

### 16.2 v2.1 Processing and Progress

目标：

用基于任务的处理和进度轮询替换面向用户的同步处理。

任务：

- 增加快速返回的任务启动端点。
- 增加处理阶段和进度更新。
- 增加任务轮询 UI。
- 增加可恢复的处理状态。
- 跳过已处理或未变更的文件。
- 增加错误恢复行为。

验收标准：

- 500 张照片的项目显示阶段进度。
- 失败项被记录，且不会让整个任务崩溃。
- 重新处理不会不必要地重做未变更工作。
- 集成测试覆盖任务进度和失败路径。

### 16.3 v2.2 Culling Workspace Upgrade

目标：

使复核工作区对真实筛选快速且舒适。

任务：

- 增加虚拟化胶片条或网格。
- 增加缩放模式。
- 增加对比模式。
- 改进分组导航。
- 增加批量操作。
- 改进键盘快捷键。
- 改进分数和解释面板。
- 增加持久化复核进度。

验收标准：

- 用户可以主要用键盘复核照片。
- UI 在 2,000 条照片记录下仍保持响应。
- 状态变更是乐观且可靠的。
- mocked 和真实 E2E 测试覆盖筛选操作。

### 16.4 v2.3 Export and Interoperability

目标：

使导出可靠，并对下游后期工具有用。

任务：

- 改进 CSV 导出。
- 改进 ZIP 导出。
- 改进文件夹复制导出。
- 增加下载端点。
- 增加导出历史。
- 增加所选数量和状态摘要。
- 规划 XMP sidecar 导出。

验收标准：

- 可以从浏览器下载 CSV 和 ZIP。
- 文件夹导出清楚显示本地输出路径。
- 导出测试验证文件存在和内容。
- 原始文件永不被修改。

### 16.5 v2.4 Algorithm Quality Upgrade

目标：

改进确定性分组、排序和解释。

任务：

- 增加感知哈希存储。
- 增加 union-find 分组。
- 增加基于元数据的分组拆分。
- 增加置信度分数。
- 改进排序公式。
- 改进解释规则。
- 为模糊、曝光和连拍类序列增加测试数据集。

验收标准：

- 相似连拍照片更可靠地分到一组。
- 更清晰的图像排在模糊的相似图像之上。
- 过曝或欠曝帧被惩罚。
- 解释匹配实际分数差异。

### 16.6 v2.5 Performance and Reliability

目标：

验证大批量行为。

任务：

- 增加合成性能数据集生成。
- 测试 100、500 和 2,000 张照片工作流。
- 剖析处理瓶颈。
- 改进数据库查询模式。
- 改进前端渲染性能。
- 为中断的处理增加恢复测试。

验收标准：

- 2,000 张照片工作流不崩溃。
- UI 保持响应。
- 处理进度保持可见。
- 内存用量对本地机器可接受。

### 16.7 v2.6 Optional RAW, HEIC, and AI Model Support

历史 stretch。**HEIC 静帧预览已作为独立的第八阶段交付**（H8.01–H8.06）。RAW、AVIF 和 XMP 已排期为 S9.03–S9.05；可选模型仍不在第九阶段。不要发明第十阶段。

目标：

仅在 v2 核心稳定之后加入高级格式和模型支持。

任务：

- 增加 HEIC 预览支持（已迁到第八阶段；见 `docs/plans/2026-09-04-heic-preview.zh.md`）。
- 增加 RAW 内嵌预览提取。
- 增加可选模型注册表。
- 增加可选的本地人脸检测模型。
- 增加可选 embedding 模型。
- 增加模型下载和许可证文档。

验收标准：

- 高级功能是可选的。
- 不提交大模型文件。
- 现有 JPEG 工作流保持稳定。
- 不支持的格式优雅失败。

## 17. 第一个 v2 迭代

第一个 v2 实现迭代应小而有意义。

### 目标

在不改变产品范围的前提下，实现基于任务的处理进度和真实集成覆盖。

### 推荐分支

```text
feature/v2-processing-progress
```

### 任务

1. 审阅当前处理代码。
2. 确保 `ProcessingJob` 记录所有阶段。
3. 若可行，使 `/process` 快速返回任务 id。
4. 增加或改进 `/jobs/{job_id}` 轮询。
5. 更新前端处理 UI 以显示真实进度。
6. 使用生成的合成图像增加后端集成测试。
7. 为失败或不支持的文件增加测试。
8. 记录更新后的处理流程。

### 可能变更的文件

```text
apps/api/app/api/routes.py
apps/api/app/models/entities.py
apps/api/app/services/processing.py
apps/api/app/services/importing.py
apps/api/app/services/exporting.py
apps/web/src/components/ProcessingPanel.tsx
apps/web/src/lib/api.ts
docs/architecture.md
docs/api.md
tests or apps/api tests
```

### 完成定义

- 处理进度在 UI 中可见。
- 可以轮询任务状态。
- 失败文件不会让整个任务崩溃。
- 现有 v1 工作流仍然可用。
- 后端集成测试通过。
- 文档已更新。
- 原始照片未被修改。

## 18. Codex 实现规则

使用 Codex 实现 v2 时，遵循这些规则：

1. 编码前阅读 `develop_plan.md`、`AGENTS.md` 和 v2 文档。
2. 不要从零重启项目。
3. 保持 FramePilot 本地优先。
4. 不要加入云上传、用户账户、支付或远程照片处理。
5. 不要修改或删除原始照片。
6. 不要提交大模型文件。
7. 所有代码、注释、测试和提交说明使用英文。活文档为双语（英文页面加上匹配的中文 `*.zh.md`）。
8. 在可选 AI 模型之前，优先使用小型、确定性、可测试的算法。
9. 为评分、分组、任务、导出和文件安全增加或更新测试。
10. 完成前运行相关测试。
11. 总结前审阅最终 diff。
12. 让每次迭代聚焦一个连贯的里程碑。

## 19. 风险与缓解

### 风险：v2 变得过大

缓解：

- 让 v2.0 聚焦处理、进度、导出和工作区可靠性。
- HEIC 静帧预览是第八阶段；推迟 RAW 和 AI 模型支持。

### 风险：本地浏览器文件访问不一致

缓解：

- 保留标准上传作为回退。
- 仅在受支持处使用 File System Access API。
- 清楚记录浏览器限制。

### 风险：AI 模型集成使部署变复杂

缓解：

- 把确定性算法作为基线。
- 让模型保持可选。
- 不捆绑大模型。

### 风险：大批量处理缓慢

缓解：

- 使用增量处理。
- 缓存生成的派生文件和分数。
- 增加性能测试。
- 使用后台任务和进度轮询。

### 风险：推荐质量被过度信任

缓解：

- 使用保守标签。
- 解释推荐。
- 把用户覆盖作为事实来源。
- 把启发式人脸信号标为实验性。

## 20. 参考与技术说明

以下技术事实影响 v2 方向：

- 浏览器应用可以通过 File System Access API 方法（例如文件和目录选择器）请求用户所选文件或目录访问，但必须检查生产浏览器兼容性。
- Chrome 文档把 File System Access API 描述为适合强大的本地文件 Web 应用（例如照片编辑器），前提是有明确的用户授权。
- ONNX Runtime Web 通过 `onnxruntime-web` 支持浏览器端推理，可能对未来可选的本地模型推理有用。
- 专业照片工作流通常依赖非破坏性元数据、评分和下游编辑器互操作；因此 v2 应规划 CSV 和未来的 XMP sidecar 导出，而不是修改原片。

## 21. v2.0 完成定义

FramePilot v2.0 在以下条件满足时完成：

- 用户可以创建或打开本地项目。
- 用户可以导入一个文件夹或大批量 JPEG/PNG/WebP 照片。
- 应用通过可见任务阶段处理照片。
- 处理可以恢复，或可以安全重跑而不做不必要的重复工作。
- 系统增量生成缩略图和预览。
- 系统计算确定性质量分数。
- 系统比 v1 更可靠地将相似图像分组。
- 系统以保守解释推荐代表照片。
- 筛选工作区对至少 2,000 条照片记录保持响应。
- 用户可以用键盘快捷键高效标记 Pick、Maybe、Reject 或 Unreviewed。
- 用户可以从浏览器导出 CSV 和 ZIP 结果。
- 文件夹导出清楚显示文件复制到何处。
- 原始照片永不被修改或删除。
- 真实后端集成测试通过。
- 真实本地 smoke E2E 可用或有清楚文档。
- README 和 v2 文档说明如何运行、测试和使用应用。
