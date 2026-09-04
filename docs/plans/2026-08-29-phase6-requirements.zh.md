# 第六阶段需求清单 — 本地持久作业回收（2026-08-29）

> Language: **中文** | [English](2026-08-29-phase6-requirements.md)

**总议题：** [#100](https://github.com/joe-cheung-cae/frame-pilot/issues/100)  
**本关卡：** [#101](https://github.com/joe-cheung-cae/frame-pilot/issues/101) — 仅需求调研  
**任务 id 真源：** [2026-08-29-phase6-durable-jobs.zh.md](2026-08-29-phase6-durable-jobs.zh.md)

本文档盘点桌面版 `2.1.0-desktop` RC 之后第六阶段应交付的内容。它**不**改变运行时行为、不翻转启动策略、不勾选 J6.01–J6.08。

---

## 1. 为何现在做第六阶段

桌面第五阶段与议题 [#96](https://github.com/joe-cheung-cae/frame-pilot/issues/96)–[#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98) 已在 `main` 关闭。`develop_plan.md` 中仍未满足「可恢复」门槛的工作：

| 计划要求 | 当前 `main` |
| -------- | ----------- |
| 可恢复的后台处理与可见进度（`develop_plan` §4.1 #3、§16.2） | 进度 + 过期失败 + **手动**导入重试；进程退出后**不能自动续跑** |
| 未来轻量 worker（`develop_plan` §10.5） | 明确延后；仅 FastAPI `BackgroundTasks` |
| 已知限制诚实表述 | 已文档化：重启失败（`docs/v2_known_limitations.md`） |

发布评审与架构文档都将**本地持久 worker / 重启安全回收**列为 v2.0 之后首要架构跟进项。桌面 2.2 UI 打磨（托盘、自动更新、分离预览）与 v2.6 HEIC/RAW/XMP/模型**不属于**本阶段。

---

## 2. 当前架构盘点

| 路径 | 今日职责 |
| ---- | -------- |
| `apps/api/app/models/entities.py` | `ProcessingJob` 进度字段；仅导入可 `retryable` |
| `apps/api/app/services/jobs.py` | 过期窗口（10 分钟）；`fail_active_jobs_on_startup` |
| `apps/api/app/services/importing.py` | 衍生作业、取消、重试、中断后照片重置 |
| `apps/api/app/services/processing.py` | 处理作业；失败时清理不完整分组 |
| `apps/api/app/api/routes.py` | 调度 `BackgroundTasks`；取消/重试路由 |
| `apps/api/app/main.py` | 启动扫描 → 将残留活跃作业标为失败 |
| `apps/api/tests/test_job_reliability.py` | 重启 / 取消 / 重试语义 |
| 项目 `cache/jobs/` | 目录存在；**未用作队列** |

**生命周期摘要：** 导入同步登记后在进程内跑衍生；处理入队后在进程内执行；重启将活跃作业标为 `failed - restart` 并重置照片/分组，避免 UI 被卡满 10 分钟。用户须重试导入或重新 `POST /process`。

---

## 3. J6.01–J6.08 验收意图

| Id | 意图 | 依赖 | 主要文件 | 提交说明 |
| ---- | ---- | ---- | -------- | -------- |
| **J6.01** | 在 `ProcessingJob` 上持久化工作游标（照片 id + 阶段 + 助手）；schema 迁移；apply/read 单测；**不改变启动行为** | — | `entities.py`、`jobs.py`、迁移、`schemas/api.py`、测试 | `v2: add processing job checkpoint fields` |
| **J6.02** | 特性开关下的启动中断：开启时标为可回收而非失败；默认仍为失败并重试 | J6.01 | `jobs.py`、`config.py`、`main.py`、测试 | `v2: add optional reclaimable job interrupt on startup` |
| **J6.03** | 中断**导入**作业的进程内回收（对可重试照片重入衍生 worker） | J6.02 | `importing.py`、`jobs.py`、启动路径、测试 | `v2: reclaim interrupted import jobs on startup` |
| **J6.04** | 中断**处理**作业的进程内回收（安全阶段续跑或清理不完整分组后继续） | J6.03 | `processing.py`、`jobs.py`、测试 | `v2: reclaim interrupted processing jobs on startup` |
| **J6.05** | 本地 worker 入口：轮询 SQLite 排队作业并调用同一服务函数；切换完成前 API 仍可调度 BackgroundTasks | J6.04 | `app/worker.py`（或模块）、文档 | `v2: add local SQLite job worker entrypoint` |
| **J6.06** | 租约 / 心跳（`worker_id`、`heartbeat_at`），使过期 = 租约到期，而非「任意重启即失败」 | J6.05 | `entities.py`、`jobs.py`、测试 | `v2: add local job lease and heartbeat` |
| **J6.07** | 桌面 sidecar 启停与可回收退出文档对齐；保持协作式导入取消 | J6.06 | 桌面 Rust 生命周期、README、已知限制 | `desktop: align quit with durable job reclaim` |
| **J6.08** | 文档收尾：架构、已知限制、API；勾选第六阶段 DoD | J6.03+（完整回收路径） | 双语架构 / 限制 / api | `docs: close out Phase 6 durable job reclaim` |

可选后续（非第六阶段 DoD）：处理取消路由；暂停/恢复；仅在有实测需要时再考虑 Dramatiq/RQ。

**后续（2026-09-03）：** 处理取消现为第七阶段 — [2026-09-03-phase7-processing-cancel.zh.md](2026-09-03-phase7-processing-cancel.zh.md)。暂停/恢复仍不在该阶段 DoD。不要在第六阶段任务 id 下实现这些项。

---

## 4. 相对 develop_plan「可恢复」的缺口

| 目标 | 状态 |
| ---- | ---- |
| 作业记录 + 阶段进度 | 已完成 |
| 快速返回 job id；UI 轮询 | 已完成 |
| 幂等跳过衍生件 / 已处理照片 | 大体完成 |
| 单项失败不拖垮整作业 | 已完成 |
| 中断后手动重试 | 导入有；处理靠重新 process |
| 进程退出后继续 | **未完成** |
| 独立本地 worker / 队列 | 已延后 |
| 暂停/恢复 | 未实现（第七阶段可选 J7.07，非 DoD） |
| 处理取消 | 下一切片：第七阶段（[2026-09-03-phase7-processing-cancel.zh.md](2026-09-03-phase7-processing-cancel.zh.md)） |
| 自动续跑中断作业 | 相反：启动即失败残留活跃作业 |

---

## 5. 非目标（第六阶段）

- HEIC / RAW 解码、XMP sidecar、捆绑神经网络模型  
- 云队列、Redis、Celery、多机 worker  
- 桌面 2.2：托盘、自动更新、分离预览、并发 UI 旋钮、更换数据目录  
- 在 J6.02+J6.03 未在开关后变绿之前，不把默认行为改成自动回收  
- 不把已关闭的桌面第五阶段 DoD 重新标为未完成  

---

## 6. 建议关卡顺序

1. 本调研（关卡 1 / #101）→ 合并  
2. 设计计划（关卡 2 / #102）→ 评审至接受  
3. 开发 PR：J6.01 → J6.02 → J6.03 → …（尽量一任务一提交）  
4. 收尾：J6.08 + 总议题 #100  

---

## 7. 风险（仅盘点）

- 第二进程 + SQLite WAL 争用 → 初期保持单活跃 worker  
- 桌面 SIGTERM 今日依赖启动失败策略；自动续跑不得把半成品分组显示为完成  
- 编码中途硬杀仍需现有幂等衍生检查  
- `GET` 项目列表不得承担重回收副作用（回收放在 lifespan / 显式 runner，不在列表端点）
