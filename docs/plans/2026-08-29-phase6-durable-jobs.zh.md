# 第六阶段实现计划 — 本地持久作业回收（2026-08-29）

> Language: **中文** | [English](2026-08-29-phase6-durable-jobs.md)

**总议题：** [#100](https://github.com/joe-cheung-cae/frame-pilot/issues/100)  
**本关卡：** [#102](https://github.com/joe-cheung-cae/frame-pilot/issues/102) — 接受前仅设计  
**调研输入：** [2026-08-29-phase6-requirements.zh.md](2026-08-29-phase6-requirements.zh.md)  
**相关：** `develop_plan.md` §4.1 #3、§10.5、§16.2；`docs/architecture.md` 作业决策（2026-06-04）

Goal Mode：一次只实现**一个任务 id**。当前任务未完成实现、测试、评审与提交前，不得开始下一任务。

---

## 1. 锁定决策

1. **仅本地优先。** 第六阶段不引入 Redis、Celery、Dramatiq、云队列、登录或远程 worker。  
2. **默认仍为失败并重试**，直至回收路径被证明。自动回收先由 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=1`（J6.02）开启；默认翻转须在 J6.03/J6.04 变绿后单独提交。  
3. **每机初期仅一个活跃导入或处理 worker。** 不对同一 SQLite 并行跑多个衍生 worker。  
4. **永不修改或删除原图。** 回收只改写衍生件、元数据、分组、作业行与项目存储下的导出。  
5. **回收不在 `GET /api/projects` 上执行。** 由启动 lifespan 或显式 reclaim runner 负责恢复写。  
6. **导出在第六阶段仍重启失败**（不完整产物已有清理）。导出持久续跑不在范围。  
7. **生活文档双语**；代码、注释、测试、提交说明用英文。  
8. **本轨道不做 HEIC/RAW/XMP/模型。**

---

## 2. 状态板

第六阶段 — 本地持久作业回收（`2.1.0-desktop` 之后）

- [x] J6.01 检查点字段与助手  
- [x] J6.02 特性开关下的可回收启动中断  
- [x] J6.03 中断导入作业的进程内回收  
- [x] J6.04 中断处理作业的进程内回收  
- [x] J6.05 本地 SQLite 轮询 worker 入口  
- [ ] J6.06 租约 / 心跳  
- [ ] J6.07 桌面 sidecar 退出对齐  
- [ ] J6.08 文档收尾  

---

## 3. 文件地图

| 路径 | 新建 / 编辑 | 任务 |
| ---- | ----------- | ---- |
| `apps/api/app/models/entities.py` | 编辑 | J6.01、J6.06 |
| `apps/api/app/services/jobs.py` | 编辑 | J6.01–J6.06 |
| `apps/api/app/db/session.py` | 编辑 | J6.01、J6.06 迁移 |
| `apps/api/app/schemas/api.py` | 编辑 | J6.01（及后续租约字段） |
| `apps/api/app/api/routes.py` | 编辑 | J6.01 `_job_read`；J6.05 入队切换 |
| `apps/api/app/core/config.py` | 编辑 | J6.02 开关 |
| `apps/api/app/main.py` | 编辑 | J6.02–J6.04 回收钩子 |
| `apps/api/app/services/importing.py` | 编辑 | J6.01 写检查点；J6.03 回收 |
| `apps/api/app/services/processing.py` | 编辑 | J6.01/J6.04 |
| `apps/api/app/worker.py`（或等价模块） | 新建 | J6.05 |
| `apps/api/tests/test_job_checkpoint.py` | 新建 | J6.01 |
| `apps/api/tests/test_job_reliability.py` | 编辑 | J6.02–J6.04 |
| `apps/desktop/src-tauri/...` | 编辑 | J6.07 |
| `docs/architecture.md`（+ zh）、`docs/api.md`（+ zh）、`docs/v2_known_limitations.md`（+ zh） | 编辑 | J6.08 |
| 本计划（+ zh） | 编辑 | 每完成一任务勾选 §2 |

---

## 4. 任务规格

### J6.01 — 检查点字段与助手

**依赖：** 无  

**实现：**

- 在 `ProcessingJob` 增加可空列：`checkpoint_photo_id`、`checkpoint_stage`、`interrupted_at`、`reclaim_count`（默认 0）  
- 经现有 `_ensure_processing_job_columns` 做 SQLite `ALTER TABLE`  
- 在 `jobs.py` 提供 `JobCheckpoint`、`read_job_checkpoint`、`apply_job_checkpoint`  
- 在 `JobRead` / `_job_read` 暴露可选字段  
- **暂不**改变 `fail_active_jobs_on_startup`  
- 导入/处理 worker 写检查点可放到 J6.03（本任务以助手 + 迁移 + 测试为主）  

**测试：** round-trip；旧库迁移加列；JobRead 默认 null。  

**提交：** `v2: add processing job checkpoint fields`

---

### J6.02 — 特性开关下的可回收中断

**依赖：** J6.01  

**实现：**

- 设置项：`job_reclaim_on_startup`，来自 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP`  
- 关闭（默认）：保持今日 `fail_active_jobs_on_startup`  
- 开启：活跃导入/处理作业标为 `status="interrupted"`、`current_step="interrupted - restart"`、写入 `interrupted_at`；导出仍失败并清理  
- **锁定词表：** `interrupted` 为可回收状态；勿当作 `complete`  

**提交：** `v2: add optional reclaimable job interrupt on startup`

---

### J6.03 — 回收中断的导入作业

**依赖：** J6.02  

**实现：** 开关开启时启动后调度衍生续跑；每张成功照片写检查点；协作取消优先；全局一次只回收一个导入作业。  

**提交：** `v2: reclaim interrupted import jobs on startup`

---

### J6.04 — 回收中断的处理作业

**依赖：** J6.03  

**锁定策略：** 清理不完整分组后自动重新排队处理（与失败清理 + 新跑相同），不做复杂中段续跑。  

**提交：** `v2: reclaim interrupted processing jobs on startup`

---

### J6.05 — 本地 worker 入口

**依赖：** J6.04  

**实现：** `python -m app.worker` 轮询 SQLite；数据目录下单 worker 锁；切换完成前 API BackgroundTasks 仍可用。  

**提交：** `v2: add local SQLite job worker entrypoint`

---

### J6.06 — 租约 / 心跳

**依赖：** J6.05  

**提交：** `v2: add local job lease and heartbeat`

---

### J6.07 — 桌面退出对齐

**依赖：** J6.06（或在 J6.03 之后仅做文档/退出语义对齐）  

**提交：** `desktop: align quit with durable job reclaim`

---

### J6.08 — 文档收尾

**依赖：** 回收路径可用（J6.03+）  

**提交：** `docs: close out Phase 6 durable job reclaim`

---

## 5. 第六阶段完成定义

- [ ] 检查点字段存在且有测试  
- [ ] 默认仍为失败并重试，**或**仅在显式翻转提交且测试全绿后默认回收  
- [ ] 回收开关开启时，中断**导入**可在 API 重启后不重新上传而完成  
- [ ] 回收开关开启时，中断**处理**不会留下损坏却显示为完成的分组  
- [ ] 原图永不修改  
- [ ] 无云/队列依赖  
- [ ] 双语文档说明新行为与剩余限制  
- [ ] 分支 tip 上 `npm run verify` 通过  

---

## 6. 验证命令

```bash
npm run test:api
npm run lint:api
npm run verify
```

迭代时：

```bash
.venv/bin/pytest apps/api/tests/test_job_checkpoint.py apps/api/tests/test_job_reliability.py -q
```
