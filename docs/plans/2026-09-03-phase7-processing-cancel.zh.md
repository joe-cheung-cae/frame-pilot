# 第七阶段实现计划 — 处理作业取消（2026-09-03）

> Language: **中文** | [English](2026-09-03-phase7-processing-cancel.md)

**总议题：** [#145](https://github.com/joe-cheung-cae/frame-pilot/issues/145)  
**本关卡：** [#146](https://github.com/joe-cheung-cae/frame-pilot/issues/146) — 实现 J7.01–J7.06（J7.07 暂停不在 DoD）  
**相关：** `develop_plan.md` §1.1、§10.5；导入取消 `apps/api/app/services/importing.py`；第六阶段回收 [2026-08-29-phase6-durable-jobs.zh.md](2026-08-29-phase6-durable-jobs.zh.md)；已知缺口 `docs/v2_known_limitations.zh.md`

Goal Mode：一次只实现**一个任务 id**。当前任务未完成实现、测试、评审与提交前，不得开始下一任务。

---

## 1. 为何做这一片

2026-09-03 选定的下一期产品切片：**处理作业取消**；暂停为可选 stretch。

导入作业已支持协作式取消（`POST /api/projects/{project_id}/jobs/{job_id}/cancel`、`cancellation_requested`、检查点、重试）。同一路由上的处理作业返回 **422** `"Only import jobs can be cancelled"`。因此桌面退出在分组/排序仍在跑时没有「退出并取消」；仍要退出会对 sidecar 发 SIGTERM，依赖 6.1 默认回收或 fail-and-retry 扫描。

用户可见缺口：长时间分组无法被主动停掉。暂停/恢复**不是**堵住这个缺口的必要条件。

---

## 2. 锁定决策

1. **仅本地优先。** 不引入 Redis、Celery、Dramatiq、云队列、登录或远程 worker。
2. **复用导入取消契约。** 同一路由、同一 `cancellation_requested` / `cancelled_at` 列、同一 HTTP 映射：
   - queued 或 running → 持久化标志，`202 Accepted`
   - 已终态（`complete`、`complete_with_errors`、`failed`、`cancelled`）→ 安全空操作，`200 OK`
   - `interrupted`（无在飞 worker）→ 立即终态为 `cancelled`，`200 OK`（对齐导入 #104 修复 4）
3. **协作式，不是硬杀进程。** worker 只在安全检查点看标志。当前 CPU 密集步骤（尤其 `group_similar_photos`，整批一次调用、无逐项回调）可以先跑完再退出。
4. **取消处理会清分组。** 终态化时调用已有 `reset_project_after_processing_failure`，再把作业标为 `cancelled`。不得把半成品或刚写入的分组留成可审阅结果。`processing` / `processed` 照片回到 `imported`。`user_status` 与 `star_rating` 保留。导入衍生件保留。**永不修改或删除原图。**
5. **重跑，不给处理作业加 `/retry`。** 取消后走现有「Run Grouping and Ranking」/ `POST /process`。不要把 `POST .../retry` 扩到非导入作业。
6. **导出作业仍不可取消**（`422`）。导出重启仍 fail-and-cleanup（第六阶段决策 6）。
7. **回收尊重已请求的取消。** interrupted 处理作业若已有 `cancellation_requested`，回收终态为 `cancelled` 并清分组，不得重新入队。与导入回收相同（#104 修复 3）。
8. **桌面退出增加「退出并取消处理」。** `CloseChoice::CancelAndQuit` + `CloseJobKind::Processing` 变为 `CancelThenTerminate`（POST cancel，最多等 10 秒，再 SIGTERM）。硬杀死仍不标成 `cancelled`。
9. **暂停/恢复不是第七阶段 DoD。** 任务 **J7.07** 保持 `[ ]` 或 `[-]`。仍然清分组再重跑的暂停只是多了状态的取消。保留半成品分组的暂停与第六阶段对分组的安全 clear-and-rerun 冲突。
10. **不在范围内：** HEIC/RAW、XMP（#117 `not_planned`）、签名、包装 GUI QA（#144）、托盘（D3.06）、自动更新、版本号、500/1000/2000 真实浏览器默认 CI。
11. **双语活文档**；代码、注释、测试、提交说明用英文。
12. **先写测试。** 改写 `test_processing_job_has_no_cancel_route_and_startup_sweep_resets_photos`，不要删掉启动扫描覆盖。

---

## 3. 状态板

第七阶段 — 处理作业取消（第六阶段 6.1 之后）

- [x] J7.01 取消路由接受处理作业
- [x] J7.02 协作检查点与取消终态化
- [x] J7.03 回收/interrupted 尊重处理取消
- [x] J7.04 处理页 UI 取消
- [x] J7.05 桌面退出取消处理
- [x] J7.06 文档收尾
- [x] J7.07 可选暂停/恢复 — 2026-09-05: S9.02 / #161; cooperative pause_requested; worker exits without cancelled finalize; resume is POST /process clear-and-rerun; not in-place.

---

## 4. 文件表

| 路径 | 新建 / 修改 | 任务 |
| ---- | ------------- | ----- |
| `apps/api/app/api/routes.py` | 改 `cancel_job_endpoint` | J7.01 |
| `apps/api/app/services/processing.py` | 取消请求辅助函数、检查点、终态化、回收分支 | J7.01–J7.03 |
| `apps/api/app/services/importing.py` | 不要把处理作业塞进导入辅助函数 | — |
| `apps/api/tests/test_job_reliability.py` | 改写 422 测试；保留关闭回收时的启动扫描 | J7.01–J7.03 |
| `apps/api/tests/test_import_process_export_api.py` | 处理取消持久化 / 空操作 / 导出仍 422 | J7.01–J7.02 |
| `apps/web/src/components/ProcessingPanel.tsx` | 取消按钮 + 进行中文案 | J7.04 |
| `apps/web/src/lib/processingProgress.ts`（+ 测试） | 如需 `isCancelling` 阻断文案 | J7.04 |
| `apps/web/src/lib/api.ts` | 复用 `cancelJob` | J7.04 |
| `tests/e2e/local-workflow.spec.ts` | 模拟处理取消 | J7.04 |
| `apps/desktop/src-tauri/src/sidecar.rs` | 对话框 + `close_decision` | J7.05 |
| `apps/desktop/README.md`（+ 中文若有） | 退出文案 | J7.05 |
| `docs/api.md`、`docs/architecture.md`、`docs/v2_known_limitations.md`、`docs/desktop_user_guide.md`、`docs/desktop_testing.md`（+ zh） | 行为说明 | J7.06 |
| `CHANGELOG.md`（+ zh） | Unreleased 第七阶段 | J7.06 |
| 本计划（+ 英文） | 每完成一个任务勾选 §3 | 各任务 |

---

## 5. 现状（不得回退）

| 行为 | 位置 |
| -------- | ----- |
| 仅导入可取消 | `cancel_job_endpoint`：`job_type != "import"` → 422 |
| 导入协作检查 | `importing.py` `_import_job_cancellation_requested` 每张照片前后 |
| interrupted 导入取消 | `_cancel_interrupted_import_job` 立即终态化 |
| 导入回收跳过已请求取消 | `prepare_interrupted_import_jobs_for_reclaim` |
| 处理分组重置 | `reset_project_after_processing_failure`（删除全部分组，`processed_images = 0`） |
| 处理 UI 已有 cancelled 恢复文案 | `processingRecoveryMessage`（`status === "cancelled"`） |
| 桌面处理退出 | `close_decision`：处理作业上 CancelAndQuit → Terminate；对话框无取消按钮 |
| 被测试钉死的限制 | `test_processing_job_has_no_cancel_route_and_startup_sweep_resets_photos` |

处理侧已有的安全检查点（`_save_job` / 租约心跳）：

- claim 之后 / `starting`
- `clearing stale groups`
- `validating generated files`（每 N 张心跳）
- `validating similarity data`
- `group_similar_photos` 前后
- 每个 `ranking group i of n` 提交后

本阶段**不要**给 `group_similar_photos` 加进度回调。

---

## 6. 任务说明

### J7.01 — 取消路由接受处理作业

**依赖：** 无

**契约（仅本任务；实现提交前 §3 J7.01 保持 `[ ]`）：**

路由：`POST /api/projects/{project_id}/jobs/{job_id}/cancel`

文件（仅 J7.01）：

- `apps/api/app/api/routes.py` — `cancel_job_endpoint` 允许 `job_type == "processing"`；导入走 `request_import_job_cancellation`，处理走 `request_processing_job_cancellation`。
- `apps/api/app/services/processing.py` — 只新增 `request_processing_job_cancellation(session, job)`。不要改 `process_project` 检查点。
- `apps/api/tests/test_job_reliability.py` — 改写 422 断言；保留关闭回收时、**没有**取消标志的 running 处理作业启动扫描（可改名或拆分）。
- `apps/api/tests/test_import_process_export_api.py` — queued/running 持久化、终态空操作、植入的非导入/非处理类型 422。
- 本计划（+ 英文）— 仅在实现提交中勾选 §3 J7.01。

`job_type == "processing"` 的 HTTP 映射：

| 作业状态 | 持久化 | HTTP |
| -------- | ------ | ---- |
| `queued` 或 `running` | `cancellation_requested=true`，`current_step="cancellation_requested"`；**不要**改 `status`（J7.02 才停 worker） | `202 Accepted` |
| `complete`、`complete_with_errors`、`failed`、`cancelled` | 空操作；成功完成的作业不要补设标志 | `200 OK` |
| `interrupted`（无在飞 worker） | 立即终态 `cancelled`（`status`、`current_step="cancelled"`、`cancellation_requested=true`、`cancelled_at`、`completed_at`，清 `worker_id` / `heartbeat_at` / `interrupted_at`）**并且** `reset_project_after_processing_failure` | `200 OK` |
| 作业不存在或 `project_id` 不匹配 | 不变 | `404` |
| `job_type` 不是 `import` 或 `processing` | 仍拒绝；422 文案可保留 `"Only import jobs can be cancelled"`，或写明两种允许类型 | `422` |

线上导出是 `ExportRecord`，不是 `ProcessingJob`。**不要**在生产代码里加 `job_type="export"`。422 测试植入 `ProcessingJob(job_type="export")`（或任何非导入/非处理类型）。用 `ExportRecord.id` 打这条取消路由仍是 `404`。

先写测试：

- 处理 queued/running 取消 → 202，标志为 true，`status` 不变，原图像素未动。
- 终态处理取消 → 200 空操作。
- 植入的 export（或其他）`ProcessingJob` 取消 → 422。
- interrupted 处理取消 → 200，`cancelled`，分组为空，照片 `imported`，原图未动。
- 现有导入取消测试仍绿（含 `test_import_process_export_api.py` 与 `test_job_review_fixes_104.py`）。
- 关闭回收时，无取消标志的 running 处理作业启动扫描仍会失败该作业并重置照片。

**J7.01 非目标：** 不加 worker 检查点（`process_project` / `_save_job` 观察 — J7.02）；不加回收分支（J7.03）；不改 `ProcessingPanel` / web / e2e（J7.04）；不改 `sidecar.rs` / 桌面退出（J7.05）；不收尾活文档 API/架构/CHANGELOG（J7.06）；不做暂停（J7.07）；不要把处理作业送进 `request_import_job_cancellation`；不要扩 `/retry`；不要改 `APP_VERSION`；不要签名或跑打包 NSIS/DMG。

**实现：**

- `cancel_job_endpoint`：允许 `job_type == "processing"`；`export` 及其他类型仍 422。
- 在 `processing.py` 增加 `request_processing_job_cancellation`（不要走 `request_import_job_cancellation`）。
- queued/running：设 `cancellation_requested`，`current_step = "cancellation_requested"`，提交，返回 202。此时不要改 `status`。
- 终态：200 空操作；成功完成的作业不要补设标志。
- `interrupted`：立即终态为 `cancelled`（status、`cancelled_at`、`completed_at`、清租约）**并且** `reset_project_after_processing_failure`。返回 200。

**测试（先写）：**

- 处理 queued/running 取消 → 202，标志为 true，原图未动。
- 终态处理取消 → 200 空操作。
- 导出取消仍 422。
- interrupted 处理取消 → 200，`cancelled`，分组已清，照片 `imported`。
- 现有导入取消测试仍通过。

**提交说明：** `v2: allow cooperative cancel on processing jobs`

---

### J7.02 — 协作检查点与取消终态化

**依赖：** J7.01

**契约（仅本任务；实现提交前 §3 J7.02 保持 `[ ]`）：**

J7.01 已在 queued/running 处理作业上持久化 `cancellation_requested`。J7.02 让在飞 worker 在安全检查点看到该标志，并终态为 `cancelled`（不是 `failed`）。

文件（仅 J7.02）：

- `apps/api/app/services/processing.py` — 增加 `_processing_job_cancellation_requested`（对齐 `_import_job_cancellation_requested`）、worker 终态化辅助函数，以及 `run_processing_job` / `process_project` / `_save_job` 的检查点。不要改 J7.01 的 `request_processing_job_cancellation` HTTP 映射。不要改 `prepare_interrupted_processing_jobs_for_reclaim`（J7.03）。
- `apps/api/tests/test_job_reliability.py` — 运行中作业检查点取消；保留崩溃处理为 `failed` 的覆盖，以及关闭回收、**没有**取消标志的启动扫描。
- `apps/api/tests/test_import_process_export_api.py` — 衍生件校验中取消仍保留已复制原图和导入缩略图（也可写在 reliability 测试里）。
- 本计划（+ 英文）— 仅在实现提交中勾选 §3 J7.02。

现场检查点（下列位置都必须看标志）。§5 里有几处今天**不是** `_save_job`：

| 位置 | 现场代码 | 说明 |
| ---- | --------- | ----- |
| 原子 claim 之后 | `run_processing_job` 在 `claim_job_atomic` + refresh 之后 | queued 取消必须终态化并返回；不要调用 `process_project` |
| `starting` 提交之后 | `process_project` 在 starting 提交之后、**`_complete_unchanged_job` 之前** | starting 是直接 commit，不是 `_save_job`；已请求取消时不得走 unchanged-complete 成功路径 |
| 每次 `_save_job` | `_save_job` 开头（先 `session.refresh`） | `clearing stale groups`、`validating generated files`、`validating similarity data`、`grouping photos`、`ranking group i of n` |
| 衍生件心跳 | 每 `DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL` 张，以及循环后的心跳提交 | 心跳是 `refresh_job_lease_heartbeat` + commit，不是 `_save_job` |
| `group_similar_photos` 前后 | 现有前后心跳 | **不要**给 `group_similar_photos` 加进度回调；当前这次 CPU 密集调用可以先跑完 |
| 每个 ranking 分组提交之后 | 写入已排序照片的每次 `session.commit()` 之后 | `_save_job("ranking group i of n")` 在 rank **之前**；提交后再查一次，刚写入的分组在取消时会被重置 |

退出路径（关键）：`process_project` 的 `except Exception` 会 rollback 再标 `failed`。协作取消**不得**把普通异常抛进这条路径（未提交的终态化也可能被 rollback 掉）。优先：检查辅助函数返回 bool；`_save_job` 在终态化取消后返回 `False`；调用方立即 `return job`。仅当专用取消异常在 `except Exception` **之前**被接住、且终态化已经 commit 时才允许用异常 —— 仍优先 bool 返回，以免漏接 except 把 `cancelled` 覆盖成 `failed`。

终态化（字段与 J7.01 interrupted 取消相同）：先 `reset_project_after_processing_failure`，再设 `status="cancelled"`、`current_step="cancelled"`、`cancellation_requested=True`、`cancelled_at` / `completed_at`，清 `worker_id` / `heartbeat_at`，提交。原因字符串可用 `"Processing job was cancelled by user request"`。不要设 `status="failed"`。永不修改或删除原图。导入衍生件保留。`user_status` / `star_rating` 保留。分组为空，`processed_images == 0`，在飞 `processing` / `processed` 照片回到 `imported`。

`_processing_job_cancellation_requested(session, job)`：`session.refresh(job)`；仅当 `job.cancellation_requested` 且 `job.status not in TERMINAL_JOB_STATUSES` 为 true（对齐 `_import_job_cancellation_requested`）。interrupted 对本辅助函数是终态；回收是 J7.03。

`run_processing_job` 崩溃处理仍是 `failed` + 重置。现有 `TERMINAL_JOB_STATUSES` 守卫对已 cancelled 的行会直接返回。崩溃不得改标为 `cancelled`。

先写测试：

- 运行中处理作业在 ranking 或 grouping 之后的检查点看到标志（monkeypatch `rank_group` / `group_similar_photos` / `_save_job` 来设置或 POST 标志）；作业结束为 `cancelled`（不是 `failed`）；分组为空；`processed_images == 0`；原图像素未变；若已设则保留 `user_status` / `star_rating`。
- 衍生件校验中取消：已复制原图和导入缩略图仍在；原图像素未变；作业为 `cancelled`。
- 现有 `run_processing_job` 崩溃测试仍结束为 `failed`。
- 关闭回收、无取消标志的启动扫描仍失败该作业（J7.01 覆盖）。
- 现有导入取消测试仍绿。

**J7.02 非目标：** 不加回收分支（`prepare_interrupted_processing_jobs_for_reclaim` — J7.03）；不改 `ProcessingPanel` / web / e2e（J7.04）；不改 `sidecar.rs` / 桌面退出（J7.05）；不收尾活文档 API/架构/CHANGELOG（J7.06）；不做暂停（J7.07）；不要给 `group_similar_photos` 加进度回调；不要扩 `/retry`；不要改 `APP_VERSION`；不要签名或跑打包 NSIS/DMG；不要做 #144。

**实现：**

- `_processing_job_cancellation_requested`（刷新作业行；仅非终态为 true）。
- 在上表检查点查看。为 true 时：`reset_project_after_processing_failure`，再标 `cancelled`（含 `cancelled_at` / `completed_at`），清 `worker_id` / `heartbeat_at`，返回。不要走把作业标成 `failed` 的通用失败路径。
- `run_processing_job` 崩溃处理仍是 `failed` + 重置；崩溃不得改标为 `cancelled`。

**测试（先写）：**

- 运行中作业在 ranking（或 grouping 之后）检查点看到标志，结束为 `cancelled`，分组为空，`processed_images == 0`，照片字节未变，若已设则保留 `user_status` / `star_rating`。
- 衍生件校验中取消仍保留已复制原图和导入缩略图。

**提交说明：** `v2: stop processing jobs at cooperative cancel checkpoints`

---

### J7.03 — 回收/interrupted 尊重处理取消

**依赖：** J7.02

**契约（仅本任务；实现提交前 §3 J7.03 保持 `[ ]`）：**

J7.01 的 interrupted HTTP 取消已在无在飞 worker 时终态为 `cancelled`。J7.03 覆盖重启路径：API/worker 回收一条已有 `cancellation_requested=true` 的 interrupted 处理行（queued/running 时已持久化取消，进程在 worker 终态化之前死掉）。回收不得把该行重新入队。

现场缺口：`prepare_interrupted_processing_jobs_for_reclaim` 总会清分组、设 `status="queued"` / `current_step="reclaim_queued"`、增加 `reclaim_count`、并把 id 加入再跑列表。导入回收在标志已设时已跳过续跑（`prepare_interrupted_import_jobs_for_reclaim` 在 claim 之后走 `_finalize_cancelled_reclaim_import`，#104 修复 3）。处理侧对齐该行为。

文件（仅 J7.03）：

- `apps/api/app/services/processing.py` — 在 `prepare_interrupted_processing_jobs_for_reclaim` 原子 claim + refresh 之后加取消分支。复用 `_finalize_cancelled_processing_job`（先清分组，再写 cancelled 字段）。同时清 `interrupted_at`（J7.01 interrupted HTTP 取消和导入回收都会清；J7.02 辅助函数目前不会 —— 可扩展该辅助函数，或在回收分支里清）。不要改 `request_processing_job_cancellation` 的 HTTP 映射。不要改 worker 检查点。
- `apps/api/tests/test_job_processing_reclaim.py` — interrupted + 标志不得重新入队；保留现有无标志回收测试。
- `apps/api/tests/test_job_reliability.py` — 保留 `test_processing_job_startup_sweep_resets_photos_without_cancel`（关闭回收、无标志）。不要改写它。
- `apps/api/tests/test_job_reclaim_startup.py` — 保留第六阶段 6.1 默认开启 / 显式关闭覆盖；不必为取消标志改它。
- 本计划（+ 英文）— 仅在实现提交中勾选 §3 J7.03。

关键：这里**不要**调用 `_processing_job_cancellation_requested`。`status == "interrupted"` 时该辅助函数为 false，因为 interrupted 属于 `TERMINAL_JOB_STATUSES`（J7.02）。在 `claim_job_atomic(..., from_statuses={"interrupted"})` + `session.refresh(job)` 之后，直接看 `job.cancellation_requested`（与导入回收相同）。

成功 claim 之后的分支：

| 条件 | 动作 | 再跑列表 |
| ---- | ---- | -------- |
| `job.cancellation_requested` | `_finalize_cancelled_processing_job`；同时清 `interrupted_at`。**不要**增加 `reclaim_count`。**不要**设 `status="queued"`。`continue`，让后面未取消的 interrupted 作业仍能填满 `limit`。 | 不加入 id |
| 标志为 false | 现有第六阶段 6.1 路径：`reset_project_after_processing_failure`，`status="queued"`，`current_step="reclaim_queued"`，增加 `reclaim_count`，加入 id | 加入 id |

`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` 在 `main.py` 的 `start_reclaimable_jobs`：它会跳过 `prepare_*`，启动扫描会失败 running 作业。**不要**改那条路径。没有取消标志的作业保持默认回收，以及关闭回收时的 fail-and-retry 扫描。

保持先 `release_stale_interrupted_lease` 再 `claim_job_atomic`。claim 失败仍 `continue`。取消路径不要二次重置（终态化辅助函数已经调用 `reset_project_after_processing_failure`）。永不修改或删除原图。导入衍生件保留。`user_status` / `star_rating` 保留。分组为空，`processed_images == 0`，在飞 `processing` / `processed` 照片回到 `imported`。不要设 `status="failed"`。

先写测试：

- interrupted 处理作业且 `cancellation_requested=true` → `prepare_*` 不包含该 id（只有这一条候选时为 `[]`）；作业为 `cancelled`，不是 `queued`/`failed`；分组为空；`processed_images == 0`；在飞照片为 `imported`；保留 `user_status`/`star_rating`；原图像素未变；`reclaim_count` 不变；`worker_id` 为 None；已设 `cancelled_at`。
- 现有 `test_prepare_interrupted_processing_clears_partial_groups` 与 `test_reclaim_reruns_interrupted_processing_job` 仍绿（无标志 → queued 回收）。
- `test_processing_job_startup_sweep_resets_photos_without_cancel` 在关闭回收时仍失败该作业。
- 可选：两条 interrupted 处理作业，第一条有标志、第二条没有，`limit=1` → 第一条 cancelled（不在列表），第二条 queued（返回 id）。取消不得占用回收名额。

**J7.03 非目标：** 不改 `ProcessingPanel` / web / e2e（J7.04）；不改 `sidecar.rs` / 桌面退出（J7.05）；不收尾活文档 API/架构/CHANGELOG（J7.06）；不做暂停（J7.07）；不要扩 `/retry`；不要改 `APP_VERSION`；不要签名或跑打包 NSIS/DMG；不要做 #144；不要改导入回收；不要改 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` 默认。

**实现：**

- `prepare_interrupted_processing_jobs_for_reclaim` 在原子 claim 之后：若 `cancellation_requested`，终态为 cancelled 并清分组；不要把 job id 加入再跑列表。
- 确认默认回收开启、以及 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` 时，**没有**取消标志的处理作业行为不变。

**测试（先写）：**

- 带 `cancellation_requested` 的 interrupted 处理作业不会被重新入队；作业为 `cancelled`；分组已清。
- 保留改名后的启动扫描测试：关闭回收时，无取消标志的 running 处理作业仍 fail-and-retry。

**提交说明：** `v2: finalize cancelled processing instead of reclaiming it`

---

### J7.04 — 处理页 UI 取消

**依赖：** J7.02

**契约（仅本任务；实现提交前 §3 J7.04 保持 `[ ]`）：**

J7.01/J7.02 已持久化 `cancellation_requested`，并在检查点终态为 `cancelled`。处理页没有取消控件。导入已有 UI 模式（`ImportPanel` 的 `api.cancelJob`、StopCircle、等待检查点文案）。J7.04 只给分组/排序加上同一模式。

现场缺口：

- `ProcessingPanel.tsx` 没有取消 mutation。`isProcessing` 已在 queued/running 时禁用 Run；POST 取消后作业在 worker 终态化前仍是 queued/running，所以 Run 仍禁用 —— 但没有 Cancel 按钮，也没有等待检查点文案。
- `processingRecoveryMessage` 已有 cancelled 文案；保持并显示。不要另写第二条 cancelled 字符串。
- `api.cancelJob` 已 POST `/jobs/{id}/cancel`。复用它。不要再加第二个客户端辅助函数。
- 共用模拟 E2E 的 `POST .../cancel` 把 `job_type` 写死为 `"import"`，并立即返回 `status: "cancelled"`。处理覆盖必须让处理作业在取消后仍是 `job_type: "processing"`（可在测试里特化取消路由，或改共用 mock 且不回归导入取消）。E2E 立即终态可以（与导入相同）；等待检查点文案用单元测试覆盖。

文件（仅 J7.04）：

- `apps/web/src/components/ProcessingPanel.tsx` — 通过 `api.cancelJob` 发取消 mutation；取消控件；等待检查点文案；活跃或正在取消时禁用 Run；显示已有 cancelled 恢复文案；显示取消错误。
- `apps/web/src/lib/processingProgress.ts`（+ `processingProgress.test.ts`）— `canCancelProcessing`（或等价函数）、等待取消文案辅助函数、`processingActionBlockMessage` 的 `isCancelling`。可选 `processingLoadRecoveryMessage("cancel")`。
- `apps/web/src/lib/api.ts` — 复用 `cancelJob`；不要新增函数。
- `apps/web/src/components/ProcessingPanel.test.tsx` — 可选；现有 mock 较粗。辅助函数 + 模拟 E2E 足够，除非面板断言成本很低。
- `tests/e2e/local-workflow.spec.ts` — 模拟处理取消请求 + cancelled 终态。不要跑 `test:e2e:real-browser:large`。
- 本计划（+ 英文）— 仅在实现提交中勾选 §3 J7.04。

UI 映射（对齐 `ImportPanel` 的 `canCancelImport` / 等待文案）：

| 展示的作业 | 控件 | 文案 |
| ---------- | ---- | ---- |
| processing，queued/running，标志为 false，mutation 未 pending | 显示 **Cancel Grouping and Ranking**（StopCircle，与导入相同的边框按钮） | 现有 `current_step` / 进度 |
| processing，queued/running，已有 `cancellation_requested` 或 mutation pending | 隐藏 Cancel | 等待：`Cancellation requested. FramePilot will stop after a safe checkpoint.`（与导入同一句） |
| processing，`cancelled` | 隐藏 Cancel；启用 **Run Grouping and Ranking**（`POST /process`，不是 `/retry`） | 现有 `processingRecoveryMessage` 的 cancelled 字符串 |
| import / export / 其他，或终态 complete/failed | 无处理取消控件 | 不变 |

`canCancelProcessing(job, isCancelPending)` 为 true 当且仅当：作业存在、`job_type === "processing"`、状态为 `queued` 或 `running`、`cancellation_requested` 为 false、且 `isCancelPending` 为 false。

`processingActionBlockMessage` 增加 `isCancelling`（默认 false）。若为 true，在现有 `isProcessing` 文案之前返回 `Cancellation is being requested. Wait for FramePilot to reach a safe checkpoint.`。面板用 `cancelMutation.isPending || (job.cancellation_requested && (queued 或 running))` 设 `isCancelling`。`isProcessing || isCancelling` 时 Run 保持禁用。`cancelled` 之后两者都为 false，Run 启用（标签仍是 “Run Grouping and Ranking”，不是 “Retry…”，后者只给 `failed`）。

轮询：状态为 queued/running 时保持 1000ms，包括已设标志。不要把 cancelled 当成可审阅结果。不要把 `interrupted` 加进前端作业状态联合类型。

取消 mutation：只对当前展示的处理作业调用 `api.cancelJob(projectId, job.id)`。onSuccess 使 `project`、`projects`、`jobs`、`job` 查询失效（与 process mutation 相同）。onError 显示错误；原图未改的恢复文案即可（若增加则用 `processingLoadRecoveryMessage("cancel")`）。不要给处理作业 POST `/retry`。不要从本面板取消导入作业。

先写测试：

- `canCancelProcessing` 仅对无标志的 processing queued/running 为 true；已设标志、mutation pending、cancelled、或导入作业为 false。
- `processingActionBlockMessage` 在 `isCancelling` 时返回等待检查点字符串，并仍阻断 Run。
- 等待文案辅助函数（若抽出）与导入等待句相同。
- 现有 cancelled 恢复字符串不变。
- 模拟 E2E：在 `/process` 植入 running 处理作业；Cancel 可见；Run 禁用；点击 Cancel；POST cancel；状态 Cancelled；恢复文案可见；Cancel 消失；**Run Grouping and Ranking** 启用（不是 Retry）。导入取消 E2E 仍绿。

**J7.04 非目标：** 不改 `sidecar.rs` / 桌面退出（J7.05）；不收尾活文档 API/架构/CHANGELOG（J7.06）；不做暂停（J7.07）；不要扩 `/retry`；不要改 `processing.py` / 路由 / 回收；不要改 `APP_VERSION`；不要签名或跑打包 NSIS/DMG；不要做 #144；不要跑 `test:e2e:real-browser:large`；不要勾选 J7.05–J7.07。

**实现：**

- `ProcessingPanel`：queued/running 且尚未设标志时显示取消；`cancellation_requested` 且尚未 `cancelled` 时显示等待检查点文案。
- 复用 `api.cancelJob`。
- 活跃或正在取消时禁用「Run Grouping and Ranking」。
- `cancelled` 恢复文案已存在，要显示出来。
- 模拟 E2E：处理取消请求 + cancelled 终态（对齐 `tests/e2e/local-workflow.spec.ts` 的导入取消覆盖）。

**测试（先写）：**

- 辅助函数覆盖 can-cancel / `isCancelling` 阻断 / 等待文案。
- 模拟 E2E 覆盖取消请求 + cancelled 终态；导入取消 E2E 仍绿。

**提交说明：** `v2: add cancel control to processing status UI`

---

### J7.05 — 桌面退出取消处理

**依赖：** J7.01（路由）；J7.02 应为 `[x]`，以便 10 秒等待能看到 `cancelled`

**契约（仅本任务；实现提交前 §3 J7.05 保持 `[ ]`）：**

J7.01 已接受处理取消。J7.02 已在检查点终态为 `cancelled`。桌面退出仍把处理作业当成不可取消。导入已走 `CancelThenTerminate` → `lib.rs` `handle_close_requested` 里的 `request_cancel_then_wait`（POST cancel，最多等 `CANCEL_WAIT` 10 秒）。J7.05 只把处理作业接到这条现有路径。

现场缺口：

- `close_decision`：`CloseChoice::CancelAndQuit` + `CloseJobKind::Processing` → `CloseDecision::Terminate`（`sidecar.rs`）。导入已经映射到 `CancelThenTerminate`。
- `quit_dialog_script_with_reclaim` 的 Processing 分支：`extra_button` 为 `""`；正文以 `"This job cannot be cancelled."` 开头。标题 `"Grouping and ranking is still running"` 以及 Keep working / Quit anyway 保持。
- sidecar 测试钉死了限制：`close_decision_cancels_import_only_and_maps_processing_to_terminate`、`quit_dialog_script_hides_cancel_for_processing_jobs`、`quit_dialog_script_processing_is_valid_javascript_without_cancel`，以及握手用例把处理作业的 `cancel_and_quit` 映射成 `Terminate`。
- `apps/desktop/README.md`「Quit while a job is running」：`Processing jobs cannot be cancelled; that dialog omits Quit and cancel.` 不存在 `apps/desktop/README.zh.md`。
- `lib.rs` 在决策为 `CancelThenTerminate` 时已经 POST cancel。`request_cancel_then_wait` 与作业类型无关。除非只改 `close_decision` 到不了 POST-cancel，否则不要改这两处。

文件（仅 J7.05）：

- `apps/desktop/src-tauri/src/sidecar.rs` — `close_decision`；`quit_dialog_script_with_reclaim` 的 Processing 分支；改写上述测试（同一 `#[cfg(test)]` 模块）。
- `apps/desktop/README.md` — 退出文案。J7.05 不要新建 `README.zh.md`（文件表：若有中文才改）。
- 本计划（+ 英文）— 仅在实现提交中勾选 §3 J7.05，且仅当已跑 `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib`。

决策映射：

| kind | choice | decision |
| ---- | ------ | -------- |
| Import 或 Processing | CancelAndQuit | CancelThenTerminate |
| None | CancelAndQuit | Terminate（不变；None 无对话框） |
| 任意 | Stay | Stay |
| 任意 | QuitAnyway | Terminate |

不要改 `close_job_kind`（未知类型已经映射到 Processing）。不要改 `find_active_job`、`request_cancel_then_wait`、`CANCEL_WAIT`、`parse_quit_choice`。SIGTERM / 5 秒后的硬杀仍不标成 `cancelled`。若 10 秒等待超时（例如 `group_similar_photos` 仍在跑），仍 SIGTERM；已持久化的 `cancellation_requested` 由 J7.03 回收尊重。

对话框（Processing；对齐导入的 `data-choice`）：

| 回收 | 标题 | extra_button | 正文（去掉 “This job cannot be cancelled.”） |
| ---- | ---- | ------------ | ------------------------------------------- |
| 开 | Grouping and ranking is still running | 与导入相同的未加引号 `data-choice=cancel_and_quit`，标签 **Quit and cancel processing** | `You can keep working, quit and cancel grouping and ranking, or quit anyway. Cancelled processing clears partial groups. Quit anyway SIGTERMs the sidecar; the next launch can interrupt and reclaim leftover processing (partial groups are cleared before rebuild). Original photos stay unchanged.` |
| 关 | 同上 | 同上 | `You can keep working, quit and cancel grouping and ranking, or quit anyway. Cancelled processing clears partial groups. Quit anyway SIGTERMs the sidecar; the next launch marks the job failed and keeps original photos unchanged (FRAMEPILOT_JOB_RECLAIM_ON_STARTUP is explicitly disabled).` |

Keep working / Quit anyway 保持。导入对话框文案和按钮不变。

README（仅 J7.05）：改掉 processing-cannot-cancel 那句，使活跃的分组/排序作业显示 Keep working / Quit and cancel processing / Quit anyway，取消路径与导入相同（POST cancel + 最多等 10 秒 + SIGTERM）。保留第六阶段 6.1 回收段落和 “original photos are never modified.”

先写测试（改写；不要删掉回收 / `node --check` 覆盖）：

- `close_decision(Processing, CancelAndQuit) == CancelThenTerminate`；QuitAnyway / Stay 不变；导入 CancelAndQuit 仍是 CancelThenTerminate。重命名 `close_decision_cancels_import_only_and_maps_processing_to_terminate`。
- 处理脚本包含 `Quit and cancel processing`、`data-choice=cancel_and_quit`、`Keep working`、`Quit anyway`；**不**包含 `cannot be cancelled`。重命名 `quit_dialog_script_hides_cancel_for_processing_jobs` 与 `quit_dialog_script_processing_is_valid_javascript_without_cancel`。
- 握手：processing + `cancel_and_quit` → CancelThenTerminate（今天是 Terminate）。
- `quit_dialog_script_mentions_reclaim_when_enabled` 仍能区分回收开启 vs `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP is explicitly disabled` / `marks the job failed`。
- 处理脚本仍通过 `node --check`。
- 导入取消按钮测试仍绿。

**J7.05 非目标：** 不收尾活文档 API / 架构 / CHANGELOG / `desktop_user_guide` / `desktop_testing`（J7.06）；不做暂停（J7.07）；不要改 `processing.py` / 路由 / 回收 / `ProcessingPanel`；不要改导入退出文案；不要改 `APP_VERSION`；不要签名或跑打包 NSIS/DMG；不要做 #144；不要勾选 J7.06–J7.07。若缺少 `rustc` / `cargo`，记录确切命令和错误，设 ok=false，**不要**勾选 §3 J7.05。

**实现：**

- `close_decision`：处理 + CancelAndQuit → `CancelThenTerminate`。
- `quit_dialog_script_with_reclaim`：增加 “Quit and cancel processing”；去掉 “This job cannot be cancelled.”
- 改写断言处理对话框没有取消按钮的 sidecar 测试。
- 更新 `apps/desktop/README.md`（仅当已有中文对照时改 zh）。

**测试（先写）：** 改写处理作业无取消按钮的断言；先看失败，再实现。

**验证：** `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib`

**提交说明：** `desktop: allow quit and cancel during processing`

---

### J7.06 — 文档收尾

**依赖：** J7.03、J7.04、J7.05（§3 均为 `[x]`）

**契约（仅本任务；实现提交前 §3 J7.06 与 §7 DoD 保持 `[ ]`）：**

J7.01–J7.05 已交付处理取消。活文档仍在描述第七阶段之前的缺口。J7.06 只改文档：双语活文档 + CHANGELOG Unreleased + 计划勾选。不要改生产取消逻辑。

现场缺口（2026-09-03 在 `feature/phase7-processing-cancel` @ `d037db88ad10ec9ec26bbbfec7510f927de722ed` 读到）：

| 文件 | 过时说法 |
| ---- | -------- |
| `docs/api.md` Jobs 引言 | 轮询处理直到 `complete` 或 `failed`（漏了 `cancelled`） |
| `docs/api.md` 取消段落（+ zh） | 路由仅导入 |
| `docs/architecture.md`（+ zh） | 只有导入取消；处理轮询到完成/失败 |
| `docs/v2_known_limitations.md` 取消语义（+ zh） | 「处理任务仍活动时关闭不能取消它（`POST .../cancel` 返回 422）」以及「处理任务仍然没有取消路由」 |
| `docs/desktop_user_guide.md` 退出一节（+ zh） | 「活跃**处理**任务无法取消」 |
| `docs/desktop_testing.md` 生命周期矩阵（+ zh） | 有「导入中退出」；没有「处理中退出」行 |
| `CHANGELOG.md` Unreleased（+ zh） | 没有第七阶段小节 |

文档必须与现场行为一致（不要编造；开发在写之前必须再读 `cancel_job_endpoint` 与 `sidecar.rs`）：

- `cancel_job_endpoint` 允许 `job_type` 为 `{import, processing}`；其他类型 422，现场 detail 仍是 `"Only import jobs can be cancelled"`。本任务**不要**改这条 422 字符串。植入的 `ProcessingJob(job_type="export")` 为 422。用 `ExportRecord.id` 打取消仍是 404。
- HTTP 映射：queued/running → 202 + 标志 / `current_step="cancellation_requested"`（worker 终态化前不改 status）；终态 → 200 空操作；interrupted → 200 终态 `cancelled` + 清分组。
- worker 终态：`_finalize_cancelled_processing_job` 再 `reset_project_after_processing_failure`；原因 `"Processing job was cancelled by user request"`。分组为空，`processed_images == 0`，在飞照片 `imported`；保留 `user_status` / `star_rating`；导入衍生件保留；永不修改或删除原图。不要给 `group_similar_photos` 加进度回调。
- 回收在已设标志时终态为 cancelled，不重新入队。`/retry` 仍仅导入。
- UI 文案（保持原句，若文档提到则照抄）：**Cancel Grouping and Ranking**；等待 `Cancellation requested. FramePilot will stop after a safe checkpoint.`；cancelled 恢复 `Processing stopped at a safe checkpoint. Run grouping and ranking again when you are ready.` 重跑走 `POST /process`，不是 `/retry`。
- 桌面：**Quit and cancel processing** → `CancelThenTerminate`（POST cancel，最多等 10 秒，再 SIGTERM）。硬杀死不标成 `cancelled`。文案已在 `apps/desktop/README.md`（无 `README.zh.md`）。
- 暂停/恢复**未实现**。

文件（仅 J7.06）：

- `docs/api.md` + `docs/api.zh.md`
- `docs/architecture.md` + `docs/architecture.zh.md`
- `docs/v2_known_limitations.md` + `docs/v2_known_limitations.zh.md`
- `docs/desktop_user_guide.md` + `docs/desktop_user_guide.zh.md`
- `docs/desktop_testing.md` + `docs/desktop_testing.zh.md`
- `CHANGELOG.md` + `CHANGELOG.zh.md`
- 本计划 + 英文 — 仅在**实现提交**中勾选 §3 J7.06 与 §7 DoD

各文件最小改动（保留双语链接；不要重写无关章节）：

- **api：** 轮询直到 `complete`、`failed` 或 `cancelled`。同一取消路由覆盖导入**和**处理（上表 HTTP 映射）。处理取消是协作式，然后清分组；原图不变；重跑走 `POST /process` 不是 `/retry`。导出/其他类型仍 422；注明现场 detail 仍写 `"Only import jobs can be cancelled"`（尽管处理已允许）——本任务不要「修好」该字符串。保留回收尊重取消的句子。
- **architecture：** 简短第七阶段说明：同一取消路由；协作式不是硬杀；取消清分组；照片回到 `imported`；原图 / 导入衍生件 / `user_status` / `star_rating` 保留；回收尊重已请求取消；导出仍不可取消。
- **known limitations：** 删掉两句「不能取消」/「仍无取消路由」。写明导入**和**处理均为协作式取消，桌面退出两者都可取消。保留导出 fail-and-cleanup / 导出取消 422。加一句：进行中分组的暂停/恢复未实现。
- **desktop user guide：** 对齐 `apps/desktop/README.md` — Keep working / Quit and cancel processing / Quit anyway；POST cancel + 最多 10 秒 + SIGTERM；取消处理会清部分分组；原图不变；保留 6.1 回收 vs `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0`。
- **desktop testing：** 在「导入中退出」后增加 **Quit + processing**（分组/排序进行中关闭；对话框见 README；取消处理清部分分组；源原图未改；手工 GUI）。
- **CHANGELOG Unreleased**（第一个小节）：`### Phase 7 — processing job cancel` / `### 第七阶段 — 处理作业取消`。条目：现有取消路由上的协作式处理取消；检查点 + 清分组 + 原图不变；处理 UI 取消；桌面退出并取消处理；回收尊重已请求取消；导出仍 422；暂停未实现；不升 `APP_VERSION`、不签名、不跑打包 GUI。

**本计划（仅实现提交）：** `[x]` J7.06；§7 每个 DoD 框 `[x]`（勾选 verify 框前开发必须已跑 `npm run verify`）。可选把 J7.07 标 `[-]`，并写 `2026-09-03: 非第七阶段 DoD；未实现（原地暂停 vs clear-and-rerun）。` 不要实现暂停。

**J7.06 非目标：** 不改生产代码；不做暂停；不扩 `/retry`；不改 `APP_VERSION`；不签名或跑打包 NSIS/DMG；不做 #144；不改 `develop_plan.md`、`desktop_deep_review.md`、`desktop_feasibility_notes.md`；不要用 Fixes 关闭 #145/#146；实现提交前不要勾选 §3 J7.06 或 §7。

**测试：** 无需改写。只改文档。

**验证：** 收尾提交上跑 `npm run verify`。不启动打包 GUI。

**提交说明：** `docs: close out Phase 7 processing job cancel`

---

### J7.07 — 可选暂停/恢复（非 DoD）

**依赖：** 若启动则在 J7.06 之后

默认第七阶段循环**不要**实现。

若以后拉入：需要非终态 `paused`、与取消不同的暂停标志、worker 退出时不把暂停当成 interrupt/reclaim、以及不会留下损坏分组的恢复。第六阶段已对分组选择 clear-and-rerun，原地暂停价值低。宁可带日期说明标 `[-]`，不要做一半暂停。

---

## 7. 第七阶段完成定义

- [x] `POST .../jobs/{id}/cancel` 可协作取消 queued、running、interrupted **处理**作业
- [x] 导出取消仍为 422
- [x] 取消处理后清分组，在飞照片回到 `imported`；原图不变
- [x] 处理 UI 可请求取消并显示检查点文案
- [x] 桌面退出可取消活跃处理作业，再 SIGTERM
- [x] 回收不会续跑已被请求取消的处理作业
- [x] 不要求暂停/恢复
- [x] 双语文档与新行为一致
- [x] 第七阶段分支尖上 `npm run test:api`、`npm run test:web`、`npm run verify` 为绿

---

## 8. 验证命令

```bash
npm run test:api
npm run lint:api
npm run test:web
npm run typecheck
npm run verify
```

迭代时的窄范围：

```bash
.venv/bin/pytest apps/api/tests/test_job_reliability.py apps/api/tests/test_import_process_export_api.py -q -k cancel
npm run test:web
```

不要启动打包后的 NSIS/DMG GUI。不要签名。不要把 #144 当成这一片。

---

## 9. 明确非目标

- 暂停/恢复（J7.07）
- 导出作业取消或导出回收
- 改变第六阶段 6.1 回收默认
- HEIC/RAW、XMP、本地模型
- 桌面 2.2（托盘、自动更新、独立预览、数据目录迁移）
- 签名商店发布 / `2.1.0-desktop` git tag
- 包装 GUI 生命周期 QA（[#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)）

---

## 10. 工作流执行

J7.01–J7.06 每个任务是**单独**工作流（工作流不能启动其他工作流）。不要实现 J7.07。

| 任务 | 工作流 | 启动 |
| ---- | -------- | ------ |
| J7.01 | `.grok/workflows/phase7-j7-01.rhai` | `/workflow phase7-j7-01` |
| J7.02 | `.grok/workflows/phase7-j7-02.rhai` | `/workflow phase7-j7-02` |
| J7.03 | `.grok/workflows/phase7-j7-03.rhai` | `/workflow phase7-j7-03` |
| J7.04 | `.grok/workflows/phase7-j7-04.rhai` | `/workflow phase7-j7-04` |
| J7.05 | `.grok/workflows/phase7-j7-05.rhai` | `/workflow phase7-j7-05` |
| J7.06 | `.grok/workflows/phase7-j7-06.rhai` | `/workflow phase7-j7-06` |

只按串行顺序。每次运行走六个阶段：需求拆解 → 评审 → 归档 → 开发 → 测试 → 上线。建议 `agent_budget`：16。在 `/workflows` 看进度。上一轮未 `complete` 且 `ok=true` 前，不要开始下一个 id。
