# 第九阶段实现计划 — 剩余 stretch 收口（2026-09-04）

> 语言：[English](2026-09-04-remaining-stretch.md) | **中文**

**总览：** [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160)（S9.00 排期）  
**相关：** `develop_plan.zh.md` §1.1；第七阶段 [2026-09-03-phase7-processing-cancel.zh.md](2026-09-03-phase7-processing-cancel.zh.md)；第八阶段 [2026-09-04-heic-preview.zh.md](2026-09-04-heic-preview.zh.md)；XMP 历史 [#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117)

Goal Mode 与 `/workflow remaining-stretch`：**每次运行只实现一个 GitHub issue**。传入 `args.slice`（`s901`…`s913`）。当前 issue 未实现、测试、评审、提交并推送之前，不要开始下一个 id。

---

## 1. 为什么做这一刀

到第八阶段为止的编号交付已在 `main`。§1.1 里剩下的是未排期 stretch，不是可以随便开工的许可。本计划把该清单**排期**为第九阶段（S9.00–S9.13）。不要发明第十阶段。

S9.00 是本文档、§1.1 指针、GitHub issue 和工作流文件。产品工作从 S9.01 开始。

---

## 2. 锁定决策

1. **本地优先。** 不上传原片，无登录、支付或捆绑神经网络模型。
2. **永不修改或删除原片。** 衍生件、导出物、XMP sidecar 和缓存都不写进源文件。
3. **每个 workflow `phase()` / 每次运行只对应一个 GitHub issue。** 不要把 S9.01–S9.13 塞进一次 开发。
4. **J7.07：** 在现有处理检查点上协作式 `pause_requested`；worker 退出时不 finalize 为 `cancelled`，也不留下可审阅的半成品分组。**恢复 = 经 `POST /process` 的 clear-and-rerun。** 不要保留半成品分组。
5. **导出取消：** 现有 cancel 路由允许 `job_type == "export"`。协作式检查点。不完整的 ZIP/文件夹走 fail-and-cleanup。修正 `"Only import jobs can be cancelled"`。桌面退出可取消进行中的导出。
6. **AVIF：** 把 `.avif` 加进现有静帧导入/导出管线。用 Pillow 自带的 `AvifImagePlugin` 解码（现场 `pillow-heif` 1.6 已去掉 AVIF；不要让 HEIF opener 宣称 `.avif`）。测试里进程内生成小文件。不是 RAW。
7. **RAW：** 原样拷贝字节；只抽**内嵌预览**。没有 thumb → 用明确本地消息跳过。不 demosaic。不把相机文件提交进 git。LibRaw 许可说明比照 libheif。
8. **XMP：** 在 [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165) 上实现。只在导出目录写 `.xmp`。永不写入 `originals/` 或相机原片旁。可选，默认关。
9. **并发旋钮：** 默认仍是一个导入/处理 worker。设置可将导入 worker 升到 2–4（opt-in）。每个项目一个处理作业。不要 Redis/Celery。
10. **检查更新：** 仅菜单点击；GitHub Releases；启动时不联网；清单缺失为非致命。
11. **签名：** CI 按 secrets 门控；未签名回退必须保持绿灯。DoD 是 signing-ready，不是商店发行。
12. **macOS QA：** skip ≠ pass。没有 Mac 主机时用 ISO-8601 时间戳记录 skip。
13. **不改 `APP_VERSION`。** 只写 CHANGELOG 未发布。
14. **活文档双语**；代码、注释、测试、提交说明用英文。
15. **测试先行。** 每次 上线 前 `npm run verify`。
16. **不做：** D4.03、完整 RAW 显影、保留半成品分组的原地暂停、云、Dramatiq/RQ、发明第十阶段。

---

## 3. 状态板

第九阶段 — 剩余 stretch（第八阶段之后）

- [x] S9.00 排期切片、GitHub issue、§1.1 指针、workflow — [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160)
- [x] S9.01 导出作业取消 — [#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164)
- [x] S9.02 J7.07 处理暂停/恢复 — [#161](https://github.com/joe-cheung-cae/frame-pilot/issues/161)
- [x] S9.03 AVIF 静帧预览 — [#163](https://github.com/joe-cheung-cae/frame-pilot/issues/163)
- [x] S9.04 RAW 内嵌预览 — [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162)
- [x] S9.05 XMP sidecar 导出 — [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165)（历史 [#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117)）
- [x] S9.06 可选系统托盘（D3.06） — [#169](https://github.com/joe-cheung-cae/frame-pilot/issues/169)
- [x] S9.07 独立预览窗口 — [#166](https://github.com/joe-cheung-cae/frame-pilot/issues/166)
- [ ] S9.08 可选导入并发旋钮 — [#168](https://github.com/joe-cheung-cae/frame-pilot/issues/168)
- [ ] S9.09 更改数据目录 — [#170](https://github.com/joe-cheung-cae/frame-pilot/issues/170)
- [ ] S9.10 可选检查更新 — [#167](https://github.com/joe-cheung-cae/frame-pilot/issues/167)
- [ ] S9.11 签名就绪 CI — [#171](https://github.com/joe-cheung-cae/frame-pilot/issues/171)
- [ ] S9.12 macOS DMG GUI 生命周期 QA — [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)
- [ ] S9.13 文档残留修复 — [#173](https://github.com/joe-cheung-cae/frame-pilot/issues/173)

---

## 4. Issue 对照

| ID | GitHub | 提交说明 |
| -- | ------ | -------- |
| S9.00 | [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160) | `docs: schedule remaining stretch S9.00–S9.13` |
| S9.01 | [#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164) | `v2: allow cooperative cancel on export jobs` |
| S9.02 | [#161](https://github.com/joe-cheung-cae/frame-pilot/issues/161) | `v2: cooperative pause for processing jobs` |
| S9.03 | [#163](https://github.com/joe-cheung-cae/frame-pilot/issues/163) | `v2: import AVIF still previews` |
| S9.04 | [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) | `v2: extract RAW embedded previews` |
| S9.05 | [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165) | `v2: write XMP sidecars in export directory` |
| S9.06 | [#169](https://github.com/joe-cheung-cae/frame-pilot/issues/169) | `desktop: optional system tray` |
| S9.07 | [#166](https://github.com/joe-cheung-cae/frame-pilot/issues/166) | `desktop: detached preview window` |
| S9.08 | [#168](https://github.com/joe-cheung-cae/frame-pilot/issues/168) | `desktop: opt-in import worker concurrency` |
| S9.09 | [#170](https://github.com/joe-cheung-cae/frame-pilot/issues/170) | `desktop: change data directory with path rewrite` |
| S9.10 | [#167](https://github.com/joe-cheung-cae/frame-pilot/issues/167) | `desktop: optional check for updates` |
| S9.11 | [#171](https://github.com/joe-cheung-cae/frame-pilot/issues/171) | `ci: sign desktop installers when secrets exist` |
| S9.12 | [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172) | `docs: macOS DMG GUI lifecycle QA` |
| S9.13 | [#173](https://github.com/joe-cheung-cae/frame-pilot/issues/173) | `docs: close out remaining stretch S9` |

---

## 5. 各 issue 合同

### S9.00 — 排期（本提交）

文档 + GitHub issue + `.grok/workflows/remaining-stretch.rhai`。不改产品行为。

### S9.01 — 导出取消

**现场空洞：** `create_export_endpoint` 只写 `ExportRecord` + `run_export_job`。`cancel_job_endpoint` 查的是 `ProcessingJob`，`job_type` 不是 `import`/`processing` 就 422，detail 为 `"Only import jobs can be cancelled"`（`apps/api/app/api/routes.py`）。`test_cancel_export_job_is_still_rejected` 植入 `ProcessingJob(job_type="export")`。用 `ExportRecord.id` 打取消是 404。桌面 `find_active_job` 列的是 `/jobs` 不是 `/exports`；`close_job_kind` 把未知类型映射成处理退出文案（`apps/desktop/src-tauri/src/sidecar.rs`）。

**身份：** 创建导出时同时持久化 `ProcessingJob`，`job_type="export"`，**id 与 `ExportRecord` 相同**，状态 `running`。complete / fail / cancel / stale 时两行保持同步。不要把导出送进持久 worker 队列。启动时仍对残留 `ExportRecord` 做 fail-and-cleanup，并把非导入/处理的 `ProcessingJob` 标失败；**不要回收导出**。

**路由：** `POST /api/projects/{project_id}/jobs/{job_id}/cancel` 允许 `{import, processing, export}`。导出分发到 `request_export_job_cancellation`（不要复用导入/处理 helper）。422 detail 改成点名这三种允许类型。其他 `job_type` 仍 422。

HTTP（比照处理）：

| 作业状态 | 持久化 | HTTP |
| -- | -- | -- |
| queued 或 running | `cancellation_requested`；`current_step=cancellation_requested`；status 不变 | `202` |
| 终态（`complete`、`complete_with_errors`、`failed`、`cancelled`） | 空操作 | `200` |
| interrupted（没有在飞 worker） | 立即 finalize | `200` |

**检查点：** 协作式，在 `write_selection_csv` / `copy_selected_files` / `zip_selected_files` 现有 `progress_callback` 处按照片检查。不是硬杀。见到标志：中止，然后 `_remove_partial_export`（只删项目导出根下的 csv/zip/文件夹）。根外路径保留。**永不修改或删除原片。**

**Finalize：** `ProcessingJob` → `cancelled` + `cancelled_at`。对应 `ExportRecord` → 现有 fail-and-cleanup（`failed`，不加新的导出状态，无持久恢复）。再导出走新的 `POST /export`。

**桌面：** 增加 `CloseJobKind::Export`。`job_type=="export"` 不得复用处理对话框。CancelAndQuit → CancelThenTerminate（POST 同一取消路由，最多等 10 秒，再 SIGTERM）。按钮：退出并取消导出 / 继续工作 / 仍要退出。文案：不完整导出物会清理；原片不变；下次启动仍 fail-and-cleanup（不回收）。

**文件：** `apps/api/app/api/routes.py`（`cancel_job_endpoint`、`create_export_endpoint`、`run_export_job`）；`apps/api/app/services/exporting.py` 检查点；`apps/api/app/services/jobs.py`（导出仍不回收）；倒转 `apps/api/tests/test_import_process_export_api.py`；`apps/desktop/src-tauri/src/sidecar.rs`。当前仍写导出 422 的文档（`docs/api.md`、`docs/v2_known_limitations.md`、桌面 README / 用户指南、CHANGELOG Unreleased；及中文对应页）。只在实现提交里勾选 §3 S9.01。

**测试先行：** 倒转 `test_cancel_export_job_is_still_rejected`。queued/running → 202 + 标志；终态 → 200 no-op；原片未动。真实 csv/zip/folder 取消会删掉导出根下的不完整产物且不碰原片。导入/处理取消测试仍绿。桌面 Rust：export kind + cancel-and-quit。

**非目标：** S9.02–S9.13；导出持久恢复 / worker 回收；ExportPanel 取消按钮（UI 是桌面退出）；`APP_VERSION`；签名。

### S9.02 — J7.07 暂停

**现场空洞：** 没有 `pause_requested` 列。`ProcessingJob` / `_ensure_processing_job_columns` 只有 `cancellation_requested`。`cancel_job_endpoint` 把处理作业分给 `request_processing_job_cancellation`（`apps/api/app/api/routes.py`）。`_save_job`、`run_processing_job`（`claim_job_atomic` 之后）和 `process_project`（`starting` 之后、衍生心跳、`group_similar_photos` 前后、ranking 提交后）只观察 `_processing_job_cancellation_requested`，并调用 `_finalize_cancelled_processing_job`（`apps/api/app/services/processing.py`）。`prepare_interrupted_processing_jobs_for_reclaim` 在 `cancellation_requested` 时按取消终态，否则重新入队。`POST /process` 在 `BLOCKING_JOB_STATUSES`（`queued`/`running`/`interrupted`）时返回现有行。`ProcessingPanel` 只有取消（`api.cancelJob`）。前端 `ProcessingJob.status` 没有 `paused`。第七阶段 J7.07 为 `[-]`。`docs/v2_known_limitations.zh.md` 与 CHANGELOG Unreleased 仍写进行中分组的暂停/恢复未实现。

**身份：** 独立的 `pause_requested` BOOLEAN NOT NULL DEFAULT 0。**不要**复用 `cancellation_requested`、`cancelled_at` 或 `request_processing_job_cancellation`。新增 `POST /api/projects/{project_id}/jobs/{job_id}/pause`。在 `JobRead` 和前端 `ProcessingJob` 上暴露 `pause_requested`。

**状态：** 本行终态为 `paused`（不是 `cancelled`、`failed`、`interrupted`）。`paused` 是**对本行的终态**：加入 `TERMINAL_JOB_STATUSES`，让过期扫描和崩溃处理空操作。**不要**加入 `ACTIVE_JOB_STATUSES` 或 `BLOCKING_JOB_STATUSES`，以便 `POST /process` 能创建**新**作业。这覆盖第七阶段「非终态原地 `paused`」草稿。原地从半批次哈希继续是非目标。

**路由：** `POST /api/projects/{project_id}/jobs/{job_id}/pause` 只允许 `job_type == "processing"`。导入 / 导出 / 其他 → 422。作业缺失或 `project_id` 不符 → 404。分发到 `processing.py` 中新的 `request_processing_job_pause`。不要把暂停送进取消 helper。取消仍走 `POST .../cancel`。

HTTP（比照处理取消，标志不同）：

| 作业状态 | 持久化 | HTTP |
| -- | -- | -- |
| queued 或 running | `pause_requested`；`current_step=pause_requested`；**status 不变** | `202` |
| 终态（`complete`、`complete_with_errors`、`failed`、`cancelled`、`paused`） | 空操作；不要给已成功完成的作业打标志 | `200` |
| interrupted（没有在飞 worker） | 立即暂停终态（清分组，`status=paused`，不是 `cancelled`） | `200` |

**取消优先：** 若已有 `cancellation_requested`，不要把 `current_step` 改成 pause；继续由取消负责。Worker 检查点先看取消，再看暂停。

**检查点：** 协作式，与 J7.02 同一批站点。不是硬杀。每处：取消标志 → 现有取消终态；否则暂停标志 → 暂停终态；否则继续。`_save_job` 用 bool 返回（暂停或取消终态后返回 False）；调用方 `return job`。**不要**抛进 `process_project` / `run_processing_job` 的 `except Exception`（那会标 `failed`）。**不要**在 `group_similar_photos` 内加进度回调。

当前只观察取消、必须同时观察暂停的现场站点：

| 站点 | 现场代码 |
| -- | -- |
| 原子 claim 之后 | `run_processing_job` 在 `claim_job_atomic` + refresh 之后 |
| `starting` 提交之后 | `process_project` 在 starting 提交之后、`_complete_unchanged_job` **之前** |
| 每次 `_save_job` | `_save_job` 开头（先 `session.refresh`） |
| 衍生心跳 | 每 `DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL` 张以及循环后心跳 |
| `group_similar_photos` 前后 | 现有 pre/post 心跳 |
| 每个 ranking 分组提交之后 | 写入已排序照片的 per-group `session.commit()` 之后 |

**暂停 Finalize：** 先调用 `reset_project_after_processing_failure`，再设 `status="paused"`、`current_step="paused"`、`pause_requested=True`、`completed_at`，清空 `worker_id` / `heartbeat_at` / `interrupted_at`，commit。原因可用 `"Processing job was paused by user request"`。**不要**设 `status="cancelled"`。**不要**设 `cancellation_requested` 或 `cancelled_at`。分组为空，`processed_images == 0`，在飞 `processing` / `processed` 照片回到 `imported`。`user_status` / `star_rating` 保留。导入衍生件保留。**永不修改或删除原片。** 不可审阅。

**回收：** 在 `prepare_interrupted_processing_jobs_for_reclaim` 中，原子 claim + refresh 之后直接看标志（不要用 `_processing_job_cancellation_requested`；`interrupted` 时它为 false）。若 `cancellation_requested` → 现有取消终态（取消优先）。Elif `pause_requested` → 暂停终态；**不要**重新入队；**不要**增加 `reclaim_count`。无标志路径仍走第六阶段 6.1 入队回收。`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` 的 fail-and-retry 对无暂停/取消标志的作业不变。

**恢复：** paused 行进入终态后，`POST /process` 创建**新**处理作业并重建分组（`create_processing_job` + `run_processing_job`）。不要原地恢复该 paused 行。不要把 `POST .../retry` 扩到处理作业。

**UI：** `ProcessingPanel` 的暂停控件，与取消分开。新增 `api.pauseJob` → POST `/pause`。不要把暂停送进 `cancelJob`。

| 展示的作业 | 控件 | 文案 |
| -- | -- | -- |
| 处理，queued/running，两标志皆 false | 显示 **Pause Grouping and Ranking** 以及现有取消 | 现有 `current_step` / 进度 |
| queued/running，`pause_requested` 或暂停 mutation pending | 隐藏暂停 | `Pause requested. FramePilot will stop after a safe checkpoint.` |
| queued/running，`cancellation_requested` | 隐藏暂停；现有取消 pending 文案 | 取消 pending 不变 |
| `paused` | 隐藏暂停/取消；启用 **Run Grouping and Ranking**（`POST /process`，不是 `/retry`） | 暂停恢复：在安全检查点停下；半成品分组已清；准备好再跑；原片不变 |
| 导入 / 导出 / 其他，或终态 complete/failed/cancelled | 无暂停控件 | 不变 |

`canPauseProcessing(job, isPausePending)` 为真当且仅当作业存在、`job_type === "processing"`、状态为 `queued` 或 `running`、`pause_requested` 为 false、`cancellation_requested` 为 false、且 `isPausePending` 为 false。`pause_requested` 时 `canCancelProcessing` 为 false。`processingJobHasReviewableResults("paused")` 为 false。queued/running（含暂停 pending）仍 1000ms 轮询。一旦 `paused`，`isProcessing` 为 false，因而 Run 可用（标签仍是 “Run Grouping and Ranking”，不是 Retry）。

**文档：** 替换 `docs/v2_known_limitations.md`（+ zh）和 S9.01 CHANGELOG Unreleased 条目中的「进行中分组的暂停/恢复未实现」。在 `docs/api.md`（+ zh）写暂停路由：协作式、独立标志、`paused` 终态、清分组、经 `POST /process` 恢复。若 architecture 仍暗示无暂停，补一句。CHANGELOG Unreleased 增加 S9.02 小节。不改 `APP_VERSION`。

**第七阶段计划（仅实现提交）：** 勾选 J7.07 `[x]`，附注：`2026-09-05: S9.02 / #161; cooperative pause_requested; worker exits without cancelled finalize; resume is POST /process clear-and-rerun; not in-place.` 中文页同样。不要取消 J7.01–J7.06 的勾。

**本计划（仅实现提交）：** 勾选 §3 S9.02 `[x]`（中英）。不要勾 S9.03–S9.13。

**文件：** `apps/api/app/models/entities.py`（`pause_requested`）；`apps/api/app/db/session.py`（`_ensure_processing_job_columns`）；`apps/api/app/schemas/api.py`（`JobRead`）；`apps/api/app/api/routes.py`（暂停端点、`_job_read`）；`apps/api/app/services/processing.py`（请求 helper、检查点、暂停终态、回收）；`apps/api/app/services/jobs.py`（只把 `paused` 放进 `TERMINAL_JOB_STATUSES`）；`apps/api/tests/test_import_process_export_api.py`；`apps/api/tests/test_job_reliability.py`；`apps/api/tests/test_job_processing_reclaim.py`；`apps/api/tests/test_job_checkpoint.py`；`apps/web/src/lib/api.ts`（`pauseJob`、status 联合、`pause_requested`）；`apps/web/src/lib/processingProgress.ts`（+ 测试）；`apps/web/src/components/ProcessingPanel.tsx`；`tests/e2e/local-workflow.spec.ts` 模拟暂停；`docs/api.md`、`docs/v2_known_limitations.md`、若 architecture 仍否认暂停则改之、CHANGELOG Unreleased（+ zh）；第七阶段计划（+ zh）J7.07 勾选；本计划（+ zh）§3 S9.02 勾选。

**测试先行：** queued/running 处理暂停 → 202，`pause_requested` 为 true，`cancellation_requested` 为 false，`status` 不变，原片未动。Worker 在 ranking 或分组后检查点看到暂停 → 作业为 `paused` 不是 `cancelled`/`failed`；分组为空；`processed_images == 0`；原片未动；`user_status` / `star_rating` 保留。终态暂停 → 200 no-op。Interrupted 暂停 → 200，`paused`，分组为空。导入/导出暂停 → 422。`paused` 之后 `POST /process` 创建新作业（不是 409 / 不复用 paused id）。回收 interrupted + `pause_requested` → `paused`，不入队，不标 cancelled。取消测试仍绿（两标志同时存在时取消优先）。`canPauseProcessing` / pending 文案 / `processingJobHasReviewableResults("paused")` 为 false。模拟 E2E：Pause 可见；POST pause；状态 Paused；Run 可用。现有导入/处理/导出取消测试仍绿。

**非目标：** 原地从半批次哈希继续；保留半成品分组；导出或导入暂停；桌面退出并暂停（退出仍走取消）；扩展 `/retry`；S9.01 或 S9.03–S9.13；`APP_VERSION`；签名。

### S9.03 — AVIF

**现场空洞：** `.avif` 不在 `SUPPORTED_EXTENSIONS`（`apps/api/app/services/importing.py`）也不在 `STORED_IMAGE_EXTENSIONS`（`apps/api/app/services/exporting.py`）。`ensure_heif_opener()` 只调用 `pillow_heif.register_heif_opener()`，文档写明不注册 AVIF（`apps/api/app/image/heif_support.py`）。现场 `pillow-heif` 1.6.0 已去掉 AVIF：`register_heif_opener` 把 `.heic`/`.heif`/… 注册成 `"HEIF"`，`_is_supported_heif` 拒绝 `avif`/`avis` brand。没有 `register_avif_opener`。HEIF wheel 带的是 libheif/libde265/libx265，没有 AV1 编解码器。`test_supported_extensions_include_heic_not_avif` 与 `test_heif_opener_does_not_claim_avif` 把这一跳过写进测试。ImportPanel 的 `IMPORT_IMAGE_ACCEPT` / `IMPORT_FORMAT_COPY` 以及桌面 `IMAGE_EXTENSIONS` 都没有 avif。PyInstaller 列了 `PIL.JpegImagePlugin` / `PngImagePlugin` / `WebPImagePlugin` 和 `pillow_heif`，没有 `PIL.AvifImagePlugin`。文档写「不接受 AVIF」。Pillow 12 已自带 `PIL.AvifImagePlugin` + `_avif`，在 `_avif` 存在时把 `.avif` 注册成 `"AVIF"`。

**身份：** 比照 HEIC 静帧预览，不是 RAW。只把 **`.avif`**（不要 `.avifs` 序列）加进 `SUPPORTED_EXTENSIONS` 和 `STORED_IMAGE_EXTENSIONS`。原片 AVIF 字节原样拷进 `{root_path}/originals/`。用 **Pillow 自带的 `AvifImagePlugin`**，走现有 `Image.open` / `ImageOps.exif_transpose` / `.convert("RGB")`。缩略图和预览仍是 **WebP**。在该 RGB 上评分/分组。ZIP/文件夹导出带上**原始 AVIF 字节**（`ZIP_STORED`）。只要主静帧。HDR/gain-map：解码 Pillow 给出的主图 RGB；不做色调映射。**不要**让 HEIF opener 宣称 `.avif`。**不要**加 `pillow-avif-plugin`。**不要**调用不存在的 `register_avif_opener`。**不要**为 AVIF 升 `pillow-heif`。HEIC/HEIF 仍走 `ensure_heif_opener()`。wheel 缺 `_avif` 是失败，不是 skip。

**UI：** `ImportPanel` 的 `accept` 加上 `image/avif,.avif`。格式文案在 JPEG/PNG/WebP/HEIC/HEIF 旁点名 AVIF；RAW 仍跳过。更新仍写 “JPEG, PNG, WebP, or HEIC/HEIF” 的空状态 / 处理文案（`shellCopy.ts`、`processingProgress.ts`）。桌面 `apps/desktop/src/lib/nativeFs.ts` 的 `IMAGE_EXTENSIONS` 加上 `"avif"`。路径导入仍用 API 列表。

**打包：** `framepilot-api.spec` hiddenimports 加上 `PIL.AvifImagePlugin` 和 `_avif`（与 WebP 同类）。HEIC 仍收集 pillow-heif。冻结 sidecar 冒烟：进程内生成小 AVIF，经冻结二进制做 path-import（保留现有 HEIC 冒烟）。保持在 400 MB 未打包 D4.06 阈值以下。不签名。

**文档（仅实现提交）：** 当前否认 AVIF 的活文档要写上静帧 AVIF：`docs/api.md`、`docs/architecture.md`、`docs/v2_known_limitations.md`（支持格式；从延后清单去掉 AVIF）、`README.md`、`docs/desktop_user_guide.md`（+ zh）。CHANGELOG Unreleased 增加 S9.03 小节。不改 `APP_VERSION`。不要声称 RAW、XMP、gain-map HDR、`.avifs` 或已签名构建。

**本计划（仅实现提交）：** 勾选 §3 S9.03 `[x]`（中英）。不要勾 S9.04–S9.13。

**文件：** `apps/api/app/services/importing.py`；`apps/api/app/services/exporting.py`；`apps/api/tests/heic_helpers.py` 或小的 `tiny_avif_bytes()` helper；`apps/api/tests/test_heif_support.py`；`apps/api/tests/test_import_process_export_api.py`；`apps/api/tests/test_import_from_paths.py`；`apps/api/tests/test_import_path_expansion.py`；`apps/api/tests/test_path_import_process_export_workflow.py`；`apps/api/tests/test_export_hardening.py`；`apps/web/src/components/ImportPanel.tsx`（+ 测试）；`apps/web/src/lib/shellCopy.ts`（+ 测试）；`apps/web/src/lib/processingProgress.ts`（+ 测试）；`apps/desktop/src/lib/nativeFs.ts`（+ 测试）；`packaging/pyinstaller/framepilot-api.spec`；`scripts/sidecar-smoke.sh`；上文文档 + CHANGELOG Unreleased（+ zh）；本计划（+ zh）§3 S9.03 勾选。

**测试先行：** 倒转 `test_supported_extensions_include_heic_not_avif`，让 `.avif` 属于 `SUPPORTED_EXTENSIONS`。保留 `test_heif_opener_does_not_claim_avif`（`.avif` 是 `"AVIF"`，不是 `"HEIF"`）。用 Pillow `Image.save(..., format="AVIF")` 在进程内生成小 AVIF——不要把相机 AVIF 提交进 git。Multipart 与 from-paths：有效小 AVIF 拷进 `originals/`，WebP 衍生件，源文件 size/mtime/bytes 不变；RAW 仍跳过。垃圾 `.avif`（`b"not-a-real-avif"`）是拷贝后的失败导入项，不是不支持扩展名跳过。路径导入 + 处理 + CSV/ZIP/文件夹：ZIP 成员是原始 AVIF 字节且 `ZIP_STORED`。ImportPanel accept + 文案；桌面选择器扩展名含 `avif`。现有 JPEG/HEIC/RAW 跳过测试仍绿。

**非目标：** RAW；XMP；gain-map HDR；`.avifs` 序列；Live Photo `.mov`；新的解码器包；`APP_VERSION`；签名；S9.04–S9.13。

### S9.04 — RAW 内嵌预览

**现场空洞：** `.arw` / `.cr3` / `.dng` / `.nef` 只在 `PLANNED_RAW_EXTENSIONS`，不在 `SUPPORTED_EXTENSIONS`（`apps/api/app/services/importing.py`）也不在 `STORED_IMAGE_EXTENSIONS`（`apps/api/app/services/exporting.py`）。`unsupported_image_reason` 返回 `"RAW files are not supported yet; import JPEG, PNG, or WebP files for this release"`。`expand_import_paths` 与 `register_import_file` 按扩展名在**拷贝前**跳过。衍生路径（`process_registered_import_photo`、`import_image_file`、`ensure_photo_derivatives`）对拷贝后的原片调用 `Image.open`——Pillow 不能解码 RAW。`apps/api/pyproject.toml` 没有 `rawpy` / LibRaw。PyInstaller 列了 JPEG/PNG/WebP/AVIF 插件和 `pillow_heif`，没有 `rawpy`。Sidecar 冒烟只覆盖 HEIC 与 AVIF。ImportPanel 的 `IMPORT_IMAGE_ACCEPT` / `IMPORT_FORMAT_COPY` 以及桌面 `IMAGE_EXTENSIONS` 都没有 RAW；文案写 RAW 跳过。测试把跳过写死：`test_import_accepts_heic_and_still_skips_raw`、`test_import_accepts_avif_and_still_skips_raw`、`test_import_from_paths_accepts_avif_and_still_skips_raw`、`test_expand_includes_avif_and_still_skips_raw`、`test_expand_nested_jpegs_and_skips`（`frame.dng` / `b"not-raw"` 从不拷贝）。文档（`docs/api.md`、`docs/architecture.md`、`docs/v2_known_limitations.md` 延后格式、README、桌面用户指南、`docs/v2_algorithm_strategy.md`）仍写 RAW 跳过。已知限制写了 LGPL libheif，没有 LibRaw。

**身份：** 比照 HEIC 静帧预览的拷贝与 WebP 路径，**不是** RAW 显影器。只把 **`.arw`、`.cr3`、`.dng`、`.nef`** 加进 `SUPPORTED_EXTENSIONS` 和 `STORED_IMAGE_EXTENSIONS`。把 `PLANNED_RAW_EXTENSIONS` 改名为 `RAW_EXTENSIONS`（仍是这四个）。原片 RAW 字节原样拷进 `{root_path}/originals/`。用 **`rawpy.extract_thumb()`**（LibRaw 内嵌预览）得到 Pillow `Image`，再走现有 `ImageOps.exif_transpose` / `.convert("RGB")`。JPEG thumb：`Image.open(BytesIO(thumb.data))`。BITMAP thumb：`Image.fromarray(thumb.data)`。缩略图和预览仍是 **WebP**。在该**预览 RGB** 上评分/分组（不是 demosaic 后的 CFA）。ZIP/文件夹导出带上**原始 RAW 字节**（`ZIP_STORED`）。元数据来自预览图 EXIF（若有）；不解析 RAW maker notes；不写 XMP。

**解码器：** 把 `rawpy` 加进 `apps/api/pyproject.toml`（MIT 包装；wheel 带 LibRaw）。选带 CPython 3.11 manylinux / macOS / win_amd64 wheel 的版本。新建 `apps/api/app/image/raw_preview.py`，提供 `extract_raw_preview_image(path) -> Image.Image`。只调用 **`extract_thumb`**。**不要**调用 `raw.postprocess`、`raw.raw_image` 或任何 demosaic。把 `rawpy.LibRawNoThumbnailError`、`rawpy.LibRawUnsupportedThumbnailError` 以及 LibRaw 打开失败映射成「无预览」。**不要**对 RAW 文件 `Image.open`。**不要**把 RAW 送进 `ensure_heif_opener()` / `AvifImagePlugin`。缺 `rawpy` / 自带 LibRaw 是**失败**，不是 skip（与缺 Pillow `_avif` 同类）。

**跳过 vs 失败：** 没有内嵌预览 → 用明确本地原因**跳过**，**不是**拷贝后的失败 Photo（那是垃圾 HEIC/AVIF 的路径）。没有 Photo 行。`originals/` 下不留拷贝。用户源文件 bytes/mtime/size 不变。锁定原因（helper；替换旧的 “not supported yet” 字符串）：

`RAW file has no embedded preview; FramePilot does not demosaic`

`expand_import_paths` 对 RAW 源做**只读**探测，无预览的文件在拷贝前进入 `skipped`。`register_import_file` / `import_image_file` 做纵深防御：若 RAW 拷贝抽不出 thumb，`_cleanup_paths` 该拷贝并抛出同一原因（multipart 进入 `skipped[]`）。`process_registered_import_photo` 与 `ensure_photo_derivatives` 对 `RAW_EXTENSIONS` 必须走 extract helper，以便 retry/reclaim 能从已拷原片重建 WebP。

**UI：** `ImportPanel` 的 `accept` 加上 `.dng,.arw,.cr3,.nef`（若现有 accept 风格含 MIME，则同时加 `image/x-adobe-dng` / `image/x-sony-arw` / `image/x-canon-cr3` / `image/x-nikon-nef`）。格式文案在 JPEG/PNG/WebP/HEIC/HEIF/AVIF 旁点名带内嵌预览的 RAW；无预览的 RAW 跳过。更新空状态 / 处理文案（`shellCopy.ts`、`processingProgress.ts`）。桌面 `apps/desktop/src/lib/nativeFs.ts` 的 `IMAGE_EXTENSIONS` 加上 `"dng"`、`"arw"`、`"cr3"`、`"nef"`。路径导入仍用 API 列表。

**打包：** `framepilot-api.spec` hiddenimports 加上 `rawpy`；新增 `packaging/pyinstaller/hooks/hook-rawpy.py`，比照 `hook-pillow_heif.py`（`collect_all` + `collect_dynamic_libs`）。保留 pillow-heif / AVIF 收集。冻结 sidecar 冒烟：进程内生成带内嵌 JPEG 预览的小 DNG，经冻结二进制做 path-import（保留 HEIC 与 AVIF 冒烟）。保持在 400 MB 未打包 D4.06 阈值以下。不签名。

**许可证（仅实现提交）：** 在 `docs/v2_known_limitations.md`（+ zh）比照 libheif 写明：`rawpy` 为 MIT；其 wheel 在 API/sidecar 运行时内带 **LGPL-2.1 / CDDL** 的 LibRaw。FramePilot 不把 LibRaw 源码塞进本 MIT 树。CHANGELOG Unreleased 增加 S9.04 小节。不改 `APP_VERSION`。

**文档（仅实现提交）：** 当前否认 RAW 的活文档要写上内嵌预览导入：`docs/api.md`、`docs/architecture.md`、`docs/v2_known_limitations.md`（支持格式；完整 RAW 显影仍延后）、`README.md`、`docs/desktop_user_guide.md`、`docs/v2_algorithm_strategy.md`（+ zh）。不要声称 demosaic、XMP、额外 RAW 扩展名或已签名构建。评分/分组使用内嵌预览 RGB。

**本计划（仅实现提交）：** 勾选 §3 S9.04 `[x]`（中英）。不要勾 S9.05–S9.13。

**文件：** `apps/api/pyproject.toml`；`apps/api/app/image/raw_preview.py`（新建）；`apps/api/app/services/importing.py`；`apps/api/app/services/exporting.py`；`apps/api/tests/raw_helpers.py`（新建，`tiny_dng_bytes`）；`apps/api/tests/test_raw_preview.py`（新建）或扩展 `test_heif_support.py`；`apps/api/tests/test_import_process_export_api.py`；`apps/api/tests/test_import_from_paths.py`；`apps/api/tests/test_import_path_expansion.py`；`apps/api/tests/test_path_import_process_export_workflow.py`；`apps/api/tests/test_export_hardening.py`；`apps/web/src/components/ImportPanel.tsx`（+ 测试）；`apps/web/src/lib/shellCopy.ts`（+ 测试）；`apps/web/src/lib/processingProgress.ts`（+ 测试）；`apps/desktop/src/lib/nativeFs.ts`（+ 测试）；`packaging/pyinstaller/framepilot-api.spec`；`packaging/pyinstaller/hooks/hook-rawpy.py`；`scripts/sidecar-smoke.sh`；上文文档 + CHANGELOG Unreleased（+ zh）；本计划（+ zh）§3 S9.04 勾选。

**测试先行：** 倒转 RAW 跳过测试，让 `.arw/.cr3/.dng/.nef` 属于 `SUPPORTED_EXTENSIONS`。进程内生成带内嵌 JPEG 预览的小 DNG（`tiny_dng_bytes` 用标准库 + Pillow；必要时补上极小 CFA + `DNGVersion`，直到 `rawpy.extract_thumb` 成功）。**不要把相机文件提交进 git。** 单元：`extract_raw_preview_image` 返回预期尺寸的 RGB；不调用 `raw.postprocess`。Multipart 与 from-paths：有效小 DNG 拷进 `originals/`，WebP 衍生件，源文件 size/mtime/bytes 不变。同一载荷存成 `.arw`/`.cr3`/`.nef` 要么能导入（若 LibRaw 按内容识别），要么在 LibRaw 拒绝该合成 DNG 扩展名时仍属于 `SUPPORTED_EXTENSIONS`，而垃圾字节跳过。垃圾 `.dng`（`b"not-a-real-raw"`）以及没有预览 IFD 的 DNG 以无预览原因**跳过**，**不是**拷贝后 `processing_state=failed`；不得存在 `originals/frame.dng`。路径导入 + 处理 + CSV/ZIP/文件夹：ZIP 成员是原始 DNG 字节且 `ZIP_STORED`；相机卡源文件不变。ImportPanel accept + 文案；桌面选择器扩展名含 `dng`/`arw`/`cr3`/`nef`。现有 JPEG/HEIC/AVIF 测试仍绿。

**非目标：** 完整 demosaic / `postprocess`；XMP；额外 RAW 扩展名（`.cr2`、`.raf`、`.orf`、`.rw2` 等）；把相机样张提交进 git；把 LibRaw 源码塞进仓库；`APP_VERSION`；签名；S9.05–S9.13。

### S9.05 — XMP

**现场空洞：** `ExportCreate` 只有 `mode`（`csv`/`folder`/`zip`）和 `statuses`（`apps/api/app/schemas/api.py`）。`create_export_endpoint` / `run_export_job` 不接受也不持久化 XMP 标志（`apps/api/app/api/routes.py`）。`copy_selected_files` / `zip_selected_files` 只拷原片字节，没有 `.xmp` 成员（`apps/api/app/services/exporting.py`）。`ExportRecord` / `ExportRead` 没有 `include_xmp`。`ExportPanel` POST `{ mode, statuses }`，没有勾选（`apps/web/src/components/ExportPanel.tsx`，`api.exportSelection`）。路径导入 ZIP 测试断言 `namelist() == ["hero.jpg"]`。文档写 XMP 已规划但未实现（`docs/api.md`、`docs/export_interoperability.md`、`docs/v2_known_limitations.md` 导出限制、README）。没有 `xmp` 测试。`_ensure_export_record_columns` 只在已经跑过的 migrations 1 和 3 里调用（`CURRENT_SCHEMA_VERSION` 为 5）；现有 v5 数据库不会自动加上新的导出列，除非再跑一次迁移。

**身份：** 在 `ExportCreate` 上可选 **`include_xmp: bool = False`**（JSON 省略该键 = false）。**不是**第四种导出模式。模式仍是 `{csv, folder, zip}`。在 `ExportRecord` 上持久化 `include_xmp` BOOLEAN NOT NULL DEFAULT 0。在 `ExportRead` 和前端 `ExportRecord` 上暴露。`create_export_endpoint` 把 `payload.include_xmp` 存到记录上。`run_export_job` 读 `record.include_xmp`。`copy_selected_files` / `zip_selected_files` 接受 `include_xmp: bool = False`，方便单元测试传入。sidecar 只是导出派生物。

**Schema：** `_ensure_export_record_columns` 增加 `include_xmp INTEGER NOT NULL DEFAULT 0`。把 `CURRENT_SCHEMA_VERSION` 升到 **6**，新增 `_migrate_to_6` 调用该 ensure（比照 S9.02 的 `_migrate_to_5`）。同时在 `init_db` 里、`_ensure_processing_job_columns` 旁边调用 `_ensure_export_record_columns`，让残留库也能 ALTER。`test_init_db_adds_missing_export_record_columns_to_existing_sqlite_table` 必须断言 `include_xmp`。

**位置：** `.xmp` **只**写在项目导出根下（`{root_path}/exports/...`）。文件夹：每个拷贝旁 `{exported_filename}.xmp`，位于 `exports/folders/selected-{id}/`。ZIP：在 `exports/zip/selected-{id}.zip` 内加入同样的 `{exported_filename}.xmp` 成员（XML 用 `ZIP_DEFLATED`；图像仍 `ZIP_STORED`）。CSV：接受并存储 `include_xmp`；**不写任何 `.xmp` 文件**（CSV 已有 `status` / `star_rating`；CSV 旁的额外文件在取消时会泄漏，因为 `remove_partial_export` 只删 `output_path`）。**永不**写入 `{root_path}/originals/`、`original_path`（相机卡）旁，或写入图像字节（不嵌 XMP 包）。

**文件名：** `{exported_file.name}.xmp`（在已唯一化的导出 basename 后追加 `.xmp`，例如 `hero.jpg.xmp` / `hero-1.jpg.xmp`）。**不要**把图像扩展名替换成 `.xmp`（`hero.xmp`）：JPEG+RAW 成对共享 stem，会冲突。把 sidecar 名加入 ZIP `used_names`。写明 Lightroom Classic 自动发现 sidecar 常常找 `{stem}.xmp`；本切片保证无歧义配对和 Lightroom 可读的**字段**，不保证自动发现。不要声称已对 Lightroom/Capture One GUI 往返做过测试。

**包（只用标准库）：** 新建 `apps/api/app/services/xmp_sidecar.py`。UTF-8 RDF/XML（`xml.etree.ElementTree` 或同等标准库；做 XML 转义）。包装：`x:xmpmeta` / `rdf:RDF` / `rdf:Description`。**不要**加 `python-xmp-toolkit` / libxmp / ExifTool。锁定映射（Reject **不要**写 `xmp:Rating = -1`——那会丢掉星级）：

| `user_status` | `xmp:Rating` | `xmp:Label` | `dc:subject`（`rdf:Bag` / `rdf:li`） |
| -- | -- | -- | -- |
| Pick | `star_rating` 限制在 0–5 | Green | Pick |
| Maybe | `star_rating` 限制在 0–5 | Yellow | Maybe |
| Reject | `star_rating` 限制在 0–5 | Red | Reject |
| Unreviewed | `star_rating` 限制在 0–5 | 省略 `xmp:Label` | Unreviewed |

同时写 `dc:title` = 导出文件名，`dc:identifier` = 项目照片 id。命名空间：`x` `adobe:ns:meta/`，`xmp` `http://ns.adobe.com/xap/1.0/`，`dc` `http://purl.org/dc/elements/1.1/`，`rdf` `http://www.w3.org/1999/02/22-rdf-syntax-ns#`。`xmp:Rating` 是文档化的 Lightroom 兼容评分字段（#165）。`xmp:Label` 用 Adobe 色标字符串，让 Pick/Maybe/Reject 可检查且不覆盖星级。不要把相机 EXIF、GPS 或分数拷进 sidecar。

**检查点：** 在拷贝/zip 成员的**同一按照片循环**里写 sidecar，然后走现有 `progress_callback`。取消/失败仍对 `output_path` 做 `remove_partial_export`（文件夹 rmtree 和 zip unlink 已会带走 sidecar）。永不修改或删除原片。

**UI：** `ExportPanel` 勾选 **Write XMP sidecars**，默认**不勾**，只用 React state（**不要**写入 `localStorage`；导出状态偏好仍分开）。导出进行中与其他控件一起禁用。说明：sidecar 写在文件夹拷贝旁和 ZIP 内；永不写到原片旁；CSV 已含状态和星级。`api.exportSelection(projectId, mode, statuses, includeXmp = false)`。未勾选的 POST 省略该标志或发送 `false`（两者都必须默认关）。历史在 `include_xmp` 为 true 时可显示 `XMP`。`ExportRecord` 类型和 ExportPanel 测试 mock 增加 `include_xmp?: boolean`。模拟 E2E 的导出 POST 可发送 `include_xmp`。

**文档（仅实现提交）：** 当前写 XMP 未实现的活文档要改成这种可选的导出目录 sidecar：`docs/export_interoperability.md`、`docs/api.md`、`docs/v2_known_limitations.md`（导出限制；XMP 仍不写入导入/`originals/`）、`docs/architecture.md`、`README.md`、`docs/desktop_user_guide.md`（+ zh）。CHANGELOG Unreleased 增加 S9.05 小节。不改 `APP_VERSION`。不要声称 Lightroom/Capture One GUI 认证、内嵌 XMP，或写回相机文件旁。

**本计划（仅实现提交）：** 勾选 §3 S9.05 `[x]`（中英）。不要勾 S9.06–S9.13。

**文件：** `apps/api/app/services/xmp_sidecar.py`（新建）；`apps/api/app/services/exporting.py`；`apps/api/app/schemas/api.py`（`ExportCreate`/`ExportRead`）；`apps/api/app/models/entities.py`（`ExportRecord.include_xmp`）；`apps/api/app/db/session.py`（`_ensure_export_record_columns`、`init_db`）；`apps/api/app/db/migrations.py`（`CURRENT_SCHEMA_VERSION` 6、`_migrate_to_6`）；`apps/api/app/api/routes.py`（`create_export_endpoint`、`run_export_job`）；`apps/api/tests/test_xmp_sidecar.py`（新建）或扩展 `test_ranking_export.py`；`apps/api/tests/test_db_session.py`；`apps/api/tests/test_import_process_export_api.py`；`apps/api/tests/test_path_import_process_export_workflow.py`；`apps/api/tests/test_export_hardening.py`；`apps/web/src/lib/api.ts`；`apps/web/src/components/ExportPanel.tsx`（+ 测试）；`tests/e2e/local-workflow.spec.ts` 模拟 `include_xmp`；上文文档 + CHANGELOG Unreleased（+ zh）；本计划（+ zh）§3 S9.05 勾选。

**测试先行：** 省略 `include_xmp` 以及 `include_xmp: false` → 项目根下没有 `.xmp`；ZIP namelist 仍只有图像；原片（项目拷贝**以及**相机卡 `original_path`）size/mtime/bytes 不变。文件夹 + `include_xmp: true` 在每个拷贝旁写 `{name}.xmp`；包按表映射 Pick/Maybe/Reject/Unreviewed 以及星级 0 和 5；`originals/` 和相机卡目录下没有 `.xmp`。ZIP + `include_xmp: true` 含匹配的 `.xmp` 成员；图像成员字节等于原片；原片不变。CSV + `include_xmp: true` 不写 `.xmp` 文件；CSV 仍有状态/星级；原片不变。重复文件名得到匹配的 `{unique-name}.xmp`。Schema v5 → v6 加上 `include_xmp`。对启用 `include_xmp` 的进行中 folder/zip 取消会清掉导出根下的不完整产物且不碰原片。ExportPanel 勾选默认关；勾选后 POST 发送 `include_xmp: true`。现有 csv/zip/folder/取消测试仍绿。

**非目标：** 写到 `originals/` 旁或相机卡上；把 XMP 嵌进图像字节；第四种 `mode="xmp"`；`python-xmp-toolkit` / ExifTool / libxmp；Lightroom/Capture One GUI 往返 CI；Reject 用 `xmp:Rating = -1`；导入/审阅时写回；S9.06–S9.13；`APP_VERSION`；签名。

### S9.06 — 托盘

**现场空洞：** 没有托盘模块，也没有 `TrayIconBuilder`。`apps/desktop/src-tauri/Cargo.toml` 为 `tauri = { version = "2", features = [] }`（没有 `tray-icon`）。`lib.rs` 只建主窗口、原生菜单、sidecar 监督和关闭决策对话框。File Close 是 `window.close()`；File Quit 是 `app.exit(0)` → `ExitRequested` → `handle_close_requested`（`menu.rs`、`lib.rs`）。`ActiveJobRef` 只有 `{project_id, job_id, job_type, status}`，没有 `progress_percent` / `current_step`（`sidecar.rs`）。`first_active_job_from_projects_json` / `first_active_job_from_jobs_json` 忽略这些 `JobRead` 字段。状态栏已经用 `firstActiveJob` 把 queued/running 格式化成 `{type} · {step} · {percent}%`（`statusBarModel.ts`）。Capabilities `default.json` 是 `core:default` + 窗口 show/unminimize/focus + `window-state:default` + `dialog:default` + `opener:allow-reveal-item-in-dir`。**没有** `fs:` 或 `shell:`（生成的 `capabilities.json` 也没有）。`core:default` 在 ACL 清单里已经包含 `core:tray:default`。打包计划 §5.1 的 D3.06 为 `[-]`，推迟于 2026-08-28。`docs/v2_known_limitations.md` Desktop 2.1 仍写托盘已延期。桌面用户指南没有托盘小节。

**身份：** 仅桌面系统托盘（D3.06 / #169）。「可选」表示它不是 2.1 DoD，且在无头/Linux 上创建可能失败；**不是**设置页勾选，也**不是**关闭即藏到托盘。桌面壳启动时总是尝试创建托盘。在 `setup` 里用 **Rust** `TrayIconBuilder` 实现。**不要**从 webview 或 `@tauri-apps/api/tray` 调托盘 API。**不要**加通知插件。进度只走 tooltip（以及主机若显示的托盘 title）。

**特性：** `tauri = { version = "2", features = ["tray-icon"] }`。图标用现有 `icons/` 的 `app.default_window_icon()`。不加新图片资源。

**菜单（锁定 D3.06）：** 只有 **Show**（`tray-show`）和 **Quit**（`tray-quit`）。英文标签，与 File → Quit 同类。不要加 Import/Export/Process。不要加速键（不要抢走 P/M/X）。

| 事件 | 行为 |
| -- | -- |
| Show，或左键单击图标 | 与单实例聚焦相同：对窗口 `main` 做 `unminimize` + `show` + `set_focus`。不要隐藏。 |
| Quit | 与 File → Quit / `WindowEvent::CloseRequested` 同一条关闭决策路径（`handle_close_requested`）。**不要**用裸 `app.exit(0)` 跳过对话框。进行中的导入 / 处理 / 导出仍是 Keep working / Quit and cancel … / Quit anyway。 |
| 窗口关闭（X）、File → Close、File → Quit | 现有关闭对话框不变。**不要**把关闭改成藏到托盘（那会跳过取消）。 |
| 最小化 | 不变（仍在任务栏/程序坞）。不是藏到托盘。 |

**进度：** 复用 `find_active_job`。给 `ActiveJobRef` 增加 `progress_percent: i32`（JSON 浮点四舍五入再限制在 0–100；缺失 → 0）和 `current_step: String`（trim；空则按 `status` 写成 `Running` 或 `Queued`）。解析器从项目 `active_import_job` 和 `/jobs` 读这些字段。Tooltip 对齐状态栏 `jobLabel`：

| 作业 | Tooltip |
| -- | -- |
| 无 | `No active job` |
| 导入 queued/running | `Import · {step} · {n}%` |
| 处理 queued/running | `Grouping and ranking · {step} · {n}%` |
| 导出 queued/running | `Export · {step} · {n}%` |

有作业时 1000 ms 轮询，空闲 5000 ms（比照 `jobsRefetchIntervalMs`）。更新 tooltip 不得碰照片文件。

**Capabilities：** **不要**加 `fs:` 或 `shell:`（不要 `fs:allow-*`、`shell:allow-open`、`opener:default`）。保留 `opener:allow-reveal-item-in-dir`。托盘在 Rust 侧；不要额外加 JS 托盘权限行（`core:default` 已含 `core:tray:default`）。现有 `core:window:allow-show` / `allow-unminimize` / `allow-set-focus` 保留。

**失败：** 创建托盘失败为**非致命**。记日志后继续；主窗口和 sidecar 仍启动。无头 CI 和部分 Linux 桌面可能没有托盘。`npm run verify` 保持无 Rust，不得编译 `src-tauri`。

**文档（仅实现提交）：** 替换 `docs/v2_known_limitations.md`（+ zh）里的「系统托盘已延期」。用户指南（+ zh）补短小节：托盘显示作业进度；Show 恢复窗口；Quit 走同一套进行中作业对话框；关窗口仍是退出，不是藏到托盘。若桌面 README（+ zh）仍未提托盘则补一句。CHANGELOG Unreleased 增加 S9.06 小节。打包计划 §5.1 的 D3.06 从 `[-]` 改为 `[x]`，附注 `2026-09-05: S9.06 / #169; tray Show+Quit; tooltip job progress; no fs:/shell:`。中文页同样。不要改写 D3.01–D3.05 / D3.07 的勾。不改 `APP_VERSION`。

**本计划（仅实现提交）：** 勾选 §3 S9.06 `[x]`（中英）。不要勾 S9.07–S9.13。

**文件：** `apps/desktop/src-tauri/Cargo.toml`（`tray-icon`）；`apps/desktop/src-tauri/src/tray.rs`（新建：菜单 id/标签、tooltip 格式化、show/quit 分发）；`apps/desktop/src-tauri/src/lib.rs`（`mod tray`；在 setup 建托盘；轮询；Quit → `handle_close_requested`）；`apps/desktop/src-tauri/src/sidecar.rs`（`ActiveJobRef` + JSON 解析）；`apps/desktop/src-tauri/capabilities/default.json`（必须仍无 `fs:` / `shell:`）；`tray.rs` 与 sidecar 解析器的 Rust 测试；`docs/v2_known_limitations.md`、`docs/desktop_user_guide.md`、必要时 `apps/desktop/README.md`、CHANGELOG Unreleased（+ zh）；打包计划（+ zh）D3.06 勾选；本计划（+ zh）§3 S9.06 勾选。

**测试先行：** 托盘菜单项是 Show + Quit（`tray-show` / `tray-quit`）。空闲 tooltip → `No active job`。处理 `current_step="Building groups"`、`progress_percent=42.4` → `Grouping and ranking · Building groups · 42%`。导入空 step + `130` → `Import · Running · 100%`。JSON 解析器读 `progress_percent` / `current_step`；缺 percent → 0。Capabilities 文件没有 `fs:` / `shell:`。现有关闭决策 / 导入 / 处理 / 导出取消的 Rust 测试仍绿（`ActiveJobRef` 字面量补上新字段）。在 `apps/desktop/src-tauri` 跑 `cargo test --lib`。`npm run verify` 仍无 Rust。托盘不读不写原片。

**非目标：** 关闭或最小化时藏到托盘；设置页开关；操作系统通知；额外托盘命令；`fs:` / `shell:` / `opener:default`；webview 托盘 API；独立预览（S9.07）；并发旋钮（S9.08）；检查更新（S9.10）；`APP_VERSION`；签名；S9.07–S9.13。

### S9.07 — 独立预览

**现场空洞：** 只有一个标签为 `main` 的 WebView（`tauri.conf.json` 的 `app.windows[]` 是 `{ label: "main", ..., create: false }`；`lib.rs` `WebviewWindowBuilder::new(..., "main", WebviewUrl::App("index.html"))`）。Capabilities `default.json` 的 `windows` 只有 `["main"]`。`on_window_event` 把**每一个** `CloseRequested` 当成 `AppQuitEvent::WindowCloseRequested`，把**每一个** `Destroyed` 当成 sidecar `request_shutdown`（`lib.rs`）——第二个窗口会退出应用并杀掉 sidecar。File → Close（`"close"`）和 View → Fullscreen 总是 `get_webview_window("main")`（`menu.rs`）。View 菜单只有 Fullscreen。本 crate **没有** `invoke_handler` / `generate_handler`。`tauri_plugin_window_state::Builder::default().build()` **没有** denylist。`initialization_script(port)` 只注入 `__FRAMEPILOT_API_BASE__` 和 `__FRAMEPILOT_DESKTOP__`。桌面 Vite 只别名 `nativeFs`（`apps/desktop/vite.config.ts`）。筛选选中活在内存 Zustand `useReviewStore` 以及 `localStorage` `framepilot.reviewProgress.v1.{projectId}`（`reviewStore.ts`、`reviewProgress.ts`、`CullingWorkspace.tsx`）。Space / Eye 切换壳内 `largePreview`。键盘只是筛选工作区上的 `window` `keydown`（`reviewShortcutCommandFromEvent`）。前端 `Photo` 有 `preview_path` / `project_copy_path`，没有 `original_path`（后端仍有 `original_path`）。`docs/v2_known_limitations.md` Desktop 2.1：「**没有**主窗口之外的独立预览窗。」产品计划 §5.6 / #166：第二个 WebView、共享选中、键盘焦点；WebView 失败则保持壳内预览。

**身份：** 仅桌面的第二个 WebView，标签 **`preview`**，显示当前筛选照片（compare 打开时显示 compare 集合，走现有 `windowedCompareRefs` / `COMPARE_WINDOW_SIZE` 6）。选中与主筛选工作区共享。**加法：** 壳内预览、Space、Eye 保留。浏览器/web 壳不变。**若创建 WebView 失败，保持壳内预览**（记日志，不崩溃，不改 sidecar）。一个 sidecar。此窗口永不读写原片。

**窗口（Rust 拥有）：** 新建 `apps/desktop/src-tauri/src/preview.rs`。在 Rust 里创建/销毁（与托盘同类）。**不要**从 JS 的 `@tauri-apps/api/webviewWindow` 创建窗口。常量 `PREVIEW_WINDOW_LABEL = "preview"`。标题 `FramePilot Preview`。约 960×720，最小 480×320，可缩放。与 main 相同的 `initialization_script(port)`，**再加上** `window.__FRAMEPILOT_WINDOW__ = "preview"`（main 设 `"main"`；保持 `initialization_script_injects_literal_boolean_and_unslash_base` 绿灯）。URL：`WebviewUrl::App("index.html".into())`（同一 SPA）。**不要**再起一个 sidecar。**不要**启动时自动打开。**不要**在 `tauri.conf.json` 里加启动即创建的窗口（可选 `{ label: "preview", create: false }`）。Window-state：`tauri_plugin_window_state::Builder::default().with_denylist(&["preview"])`，以免上次会话保存或恢复它（只 `skip_initial_state` 仍会在关闭时保存）。共用切换：`#[tauri::command] fn toggle_detached_preview` 返回 `Result<bool, String>`（`true` = 已打开，`false` = 已关闭）。创建失败为 `Err`，JS 因而保持壳内预览。用本 crate 的第一个 `invoke_handler` / `generate_handler` 注册。原生 View 菜单调用同一 Rust toggle（不是 JS 路由）。

**打开 / 关闭：**

| 事件 | 行为 |
| -- | -- |
| View → Detached preview（`detached-preview`，无加速键） | 切换：没有则创建，有则关闭。创建失败非致命。 |
| 筛选工具栏按钮（仅桌面）**Toggle detached preview** | 同一切换。**不**替换 Eye / Space。 |
| 预览窗 X，或预览窗聚焦时 File → Close | 只关预览。**不要**跑 `handle_close_requested`。**不要** `request_shutdown`。发出 `framepilot-preview-closed`，让 main 清掉 `aria-pressed`。 |
| 主窗口聚焦时 File → Close | 现有对 `main` 的退出路径。 |
| File → Quit、托盘 Quit、主窗口 X | 现有应用退出；预览随应用销毁。 |
| 主窗口离开 `/projects/:id/cull` | 关闭预览窗。 |
| 托盘 Show / 单实例 | 仍只聚焦 `main`。 |

`window_close_targets_app_quit(label)` **仅**对 `"main"` 为 true。用该 helper 门控 `CloseRequested` 和 `Destroyed`。File → Close 看聚焦 webview 标签：preview → 关预览；否则（包括没有聚焦窗）关 `main`。

**共享选中：** Main 拥有 Zustand + `localStorage` + 照片变更。Preview 是卫星。走 Tauri 事件（不要 BroadcastChannel，不要第二份 store）：

| 事件 | 方向 | 载荷 |
| -- | -- | -- |
| `framepilot-review-sync` | main → preview（preview 请求时再同步） | `{ projectId, activePhotoId, activeGroupId, filename, previewPath, compareMode, compare: [{ photoId, filename, previewPath }], previewZoom }` |
| `framepilot-review-sync-request` | preview → main | 无 |
| `framepilot-review-command` | preview → main | 现有 `ReviewShortcutCommand` JSON |
| `framepilot-preview-opened` | Rust → main | 无 |
| `framepilot-preview-closed` | preview/Rust → main | 无 |

同步只带**衍生件** `preview_path`（现有 `assetUrl`）。消毒函数（`toReviewSyncPayload` 或同等）**丢掉** `originalPath` / `original_path` / `project_copy_path` / `source_identity`。Preview 用 `assetUrl` 渲染；不要用 `fs:` 读原片。Compare 行来自现有 `windowedCompareRefs`。

**键盘焦点（写进 Help + 用户指南）：** 裸筛选键（P/M/X/U、1–5、0、方向键、Space、Z、+/−、C、G、F、E）只进入**聚焦**的 WebView。未聚焦窗口收不到。Preview 用 `reviewShortcutCommandFromEvent` 并把命令**转发给** main（`framepilot-review-command`）；main 跑现有 `CullingWorkspace` 分支（标记/评分/导航/缩放/compare/导出）。Preview **自己不**调用 `api.updatePhoto`。原生菜单组合键（CmdOrCtrl+N/W/Q）仍是应用全局。Detached preview **不要**新加速键（不要抢走 Space/P/M/X）。main 里的 Space 仍切换壳内 `largePreview`。preview 里的 Space 转发 `toggle_large_preview`（只影响壳内布局；不关闭独立窗）。扩展现有 Help 桌面句（`HelpShortcuts.tsx` / `menuRoutes.ts`）说明聚焦窗口的筛选键。

**预览 UI：** 若 `__FRAMEPILOT_WINDOW__ === "preview"`，桌面 `App` 渲染仅预览面板（图像或 compare 网格、文件名、来自 sync 的缩放）。不要 Shell 框、项目列表、第二套导入/导出 UI。Web 的 `isDesktopShell()` 为 false 时永不打开窗口。现有 CSP `img-src` 已允许 sidecar `assetUrl`。

**JS 适配：** 比照 `nativeFs`：`apps/web/src/lib/detachedPreview.ts` 类型 + 桩 `requestDetachedPreviewToggle()` → `{ ok: false, reason: "not-desktop" }`。桌面 Vite 别名 `apps/desktop/src/lib/detachedPreview.ts`（`vite.config.ts`，与 `aliasNativeFs` 同类插件）经 `@tauri-apps/api/core` 调用 `toggle_detached_preview`。`CullingWorkspace` 仅在 `isDesktopShell()` 时显示额外按钮。

**锁定残留：** `apps/web` 不得 import `@tauri-apps/*`（现有 `nativeFs.test.ts` 守卫）。invoke 与事件 I/O 只放在别名后的 `detachedPreview` 模块（`CullingWorkspace` 和预览面板只从 `@/lib/detachedPreview` 导入）。Web 桩：`requestDetachedPreviewToggle()` → `{ ok: false, reason: "not-desktop" }`；`requestDetachedPreviewClose()` 是**空操作且绝不能 toggle**（`{ ok: true, open: false }` 或 `{ ok: false, reason: "not-desktop" }`）；emit helper 空操作；subscribe helper 返回空 unlisten。桌面别名：经 `@tauri-apps/api/core` 调用 `invoke("toggle_detached_preview")` 与 `invoke("close_detached_preview")`；经 `@tauri-apps/api/event` 做 `emit`/`listen`（应用级，与 `framepilot-quit-choice` 同类）。按 `__FRAMEPILOT_WINDOW__` 过滤：main 忽略 `framepilot-review-sync`；preview 忽略 `framepilot-review-command`。再注册 `#[tauri::command] fn close_detached_preview` → `Result<bool, String>`，幂等（缺失则 `Ok(false)`；**不要创建**）。离开 `/projects/:id/cull` 必须 **close**，不能 toggle。View 菜单和工具栏共用 toggle。File Close / 预览窗 X / 离开 cull 共用 close。创建成功后 Rust 发 `framepilot-preview-opened`；`preview` 的 `Destroyed` 发 `framepilot-preview-closed`。工具栏 `aria-pressed` 跟这些事件（View 菜单不经过 JS）。File Close 看聚焦 webview 标签；`preview` → 关预览；否则（包括没有聚焦窗）关 `main`。`initialization_script` 注入 JS 字符串 `__FRAMEPILOT_WINDOW__`（仅常量 `"main"` / `"preview"`；保持布尔 `__FRAMEPILOT_DESKTOP__ = true`）。写入 `apps/web/src/types/globals.d.ts`。Preview 的 `App` 在 `AppRoutes` / `NativeMenuListener` **之前**分支。空 sync（没有 `activePhotoId`）渲染空面板，不是项目列表。

**Capabilities：** 把 `"preview"` 加进 `default.json` 的 `windows`，让第二个 WebView 能 emit/listen。保留 `core:window:allow-show` / `allow-unminimize` / `allow-set-focus`。**不要**加 `fs:` 或 `shell:`（`opener:default` 仍不要）。`core:default` 已含 events。

**失败：** `WebviewWindowBuilder::build` / 打开失败为**非致命**。记日志；壳内预览仍在；`npm run verify` 保持无 Rust。

**文档（仅实现提交）：** 替换 `docs/v2_known_limitations.md`（+ zh）里的「没有独立预览」。用户指南（+ zh）补短小节：View → Detached preview；共享选中；快捷键作用于聚焦窗口；创建失败则保持壳内预览；关预览 ≠ 退出。Help 桌面句说明焦点。若桌面 README（+ zh）仍未提则补一句。CHANGELOG Unreleased 增加 S9.07 小节。**不要**把 `docs/desktop_development_plan.md` §2.2 / §5.6 改写成已交付（留给 S9.13）。不改 `APP_VERSION`。

**本计划（仅实现提交）：** 勾选 §3 S9.07 `[x]`（中英）。不要勾 S9.08–S9.13。

**文件：** `apps/desktop/src-tauri/src/preview.rs`（新建：标签、标题、打开/关闭/切换、`close_detached_preview`、`window_close_targets_app_quit`）；`apps/desktop/src-tauri/src/lib.rs`（`mod preview`；第一个 `invoke_handler`；门控 CloseRequested/Destroyed；window-state `with_denylist`）；`apps/desktop/src-tauri/src/menu.rs`（View `detached-preview`；File Close → 聚焦窗口）；若 init script 增加窗口标签 helper 则改 `apps/desktop/src-tauri/src/sidecar.rs`；`apps/desktop/src-tauri/capabilities/default.json`（`windows` 含 `preview`；仍无 `fs:`/`shell:`）；`apps/desktop/src/App.tsx`（预览面板在 `AppRoutes` **之前**分支）；`apps/desktop/src/lib/detachedPreview.ts`（新建，Vite 别名）；`apps/desktop/vite.config.ts`（比照 `nativeFs` 别名）；`apps/web/src/lib/detachedPreview.ts`（新建：载荷消毒、toggle/close 桩、空操作事件）；`apps/web/src/types/globals.d.ts`（`__FRAMEPILOT_WINDOW__`）；`apps/web/src/components/CullingWorkspace.tsx`（桌面切换按钮 + 发出 sync / 处理命令）；`apps/web/src/components/HelpShortcuts.tsx` 或 `menuRoutes.ts` 桌面 Help 句；`preview.rs` 的 Rust 测试；载荷/桩与菜单加速键的 web/desktop 测试；上文文档 + CHANGELOG Unreleased（+ zh）；本计划（+ zh）§3 S9.07 勾选。

**测试先行：** `PREVIEW_WINDOW_LABEL == "preview"`。`window_close_targets_app_quit("preview")` 为 false；`"main"` 为 true。预览聚焦时 File Close 不是应用退出。Destroyed preview 不意味着 sidecar shutdown。View 项 id `detached-preview` 无加速键；`menu.rs` 仍无裸 P/M/X/Space 加速键。Capabilities 的 `windows` 含 `preview` 且无 `fs:`/`shell:`。Sync 载荷往返保留 `previewPath` 并丢掉 `originalPath` / `project_copy_path`。桩 `requestDetachedPreviewToggle` 为 `{ ok: false, reason: "not-desktop" }`。桩 `requestDetachedPreviewClose` 不 toggle。现有 `apps/web source does not import Tauri plugins` 仍绿。缺失窗口时 `close_detached_preview` 为 `Ok(false)`。现有关闭决策 / 托盘 / 导入 / 处理 / 导出取消的 Rust 测试仍绿。`initialization_script` 仍注入布尔 `__FRAMEPILOT_DESKTOP__`。在 `apps/desktop/src-tauri` 跑 `cargo test --lib`。`npm run verify` 仍无 Rust。独立预览不读不写原片。

**非目标：** 替换壳内预览；启动时自动重开；藏到托盘；always-on-top / 独占全屏预览；第二个 sidecar；`fs:` / `shell:` / `opener:default`；设置页开关；把 detached-open 写入 `reviewProgress`；把 §2.2 改写成已完成；并发旋钮（S9.08）；数据目录（S9.09）；检查更新（S9.10）；`APP_VERSION`；签名；S9.08–S9.13。

### S9.08 — 并发旋钮

设置 1–4 个导入 worker，默认 1。处理仍是每项目一个作业。

### S9.09 — 数据目录

显式授权（D2.00 允许名单）。改写已存项目路径。永不改写相机卡上的原片。

### S9.10 — 检查更新

仅菜单。GitHub Releases。启动不联网。

### S9.11 — 签名就绪 CI

`desktop.yml` 步骤按 secrets 门控。未签名路径保持绿灯。更新 `docs/desktop_signing.zh.md` 中的 secret 名。git 里不要证书。

### S9.12 — macOS DMG QA

遵循 `docs/desktop_testing.zh.md`。没有 Mac → 带时间戳 skip，不是 pass。

### S9.13 — 文档残留修复

对齐 `docs/desktop_development_plan.zh.md` §2.2；已知限制；README；CHANGELOG；`implement_goals.zh.md`。在对应框变成 `[x]` 之前，不要声称 2.2 项已完成。PR 正文只在本 issue 之后才可写 `Fixes`。

---

## 6. 完成定义（整项）

- [x] §1.1 点名 S9.00–S9.13，并禁止发明第十阶段
- [ ] S9.01–S9.13 各自 `[x]`，且带 §4 的提交说明
- [ ] 测试中原片从未被修改
- [ ] S9.13 上线 前分支尖上 `npm run verify` 绿灯
- [ ] `feature/remaining-stretch` 只有一份草稿 PR；`Refs #160` 加子编号；S9.13 之前不要 `Fixes`
- [ ] 不改 `APP_VERSION`，无证书，无相机文件，无模型权重

---

## 7. 工作流执行

工作流不能启动其他工作流。一个带参数的文件：

| 运行 | 命令 |
| --- | --- |
| 下一个产品 issue | `/workflow remaining-stretch` 传入 `{"slice":"s901"}`（然后 `s902`…） |
| 文件 | `.grok/workflows/remaining-stretch.rhai` |

每次运行的仪表盘 `phase()` 标题就是该 issue id。phase 内部：需求拆解 → 评审（+ skeptic）→ 归档 → 开发 → 测试 → 上线。

**分支：** 从 `origin/main` 拉出的 `feature/remaining-stretch`。每个 issue 后推送。永远不要第二份 PR。工作流不要合并进 `main`。不要 squash。不要 force-push。

**幂等：** 若 §3 已是 `[x]` 且 `git log origin/main..HEAD` 已有该提交说明，返回 `ok=true`，不要重做。

**失败即停：** `ok=false` 或 skeptic `real=false` → 停止。不要开始下一个切片。

建议 `agent_budget`：32.
