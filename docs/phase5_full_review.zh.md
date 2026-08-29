# Phase 5 完整评审（Bugbot + Security）

> Language: **中文** | [English](phase5_full_review.md)

评审日期：2026-08-29。

对 FramePilot 桌面版 `2.1.0-desktop` 的 **Phase 5 — 测试、文档与稳定化** 做合并工程评审，由 Bugbot 与 Security Review 子代理并行执行。

## 1. 结论

Phase 5 主要是在 Phase 0–4 之上的 **文档 / 版本 / 发布簿记**。可作为桌面 RC 收尾保留，但有 **一项中等严重度的正确性发现**（D5.03 证据标注）。

- **Bugbot：** 1 项发现（medium）。
- **Security：** 本 diff 无 medium+ 问题。
- **安全运维备注（未达上报门槛）：** 未签名安装包、本机 `/api/meta`、sidecar 日志中的 `data_dir` — 既有行为且已文档化；公开签名发布前继续跟踪。

## 2. 范围与方法

| 项 | 值 |
| ---- | ----- |
| 工作区 | `/home/joe/repo/frame-pilot` |
| 检出 tip | `main` @ `a3819dd`（`docs: close out Phase 5 DoD with evidence (#95)`） |
| Diff 基线 | `f4cee3d`（`Merge pull request #77…`），本地引用 `review/phase5-base` |
| Diff 模式 | 相对 `review/phase5-base` 的分支变更 |
| 范围 | 仅 Phase 5：D5.01–D5.05（含需求盘点 / 文档设计 / DoD 收尾） |
| 编排 | 并行 `bugbot` + `security-review` 子代理 |

### 范围内提交

| SHA | 摘要 |
| ---- | ------- |
| `45b13df` | docs: inventory Phase 5 requirements (#80) |
| `e0b4f82` | docs: design Phase 5 documentation plan (#83) |
| `38d7823` | docs: add desktop test matrix (#85) — **D5.01** |
| `66e42b3` | docs: add desktop install and data-dir instructions (#87) — **D5.02** |
| `3ce7f11` | docs: record desktop performance notes (#89) — **D5.03** |
| `97c03d9` | release: 2.1.0-desktop rc (#91) — **D5.04** |
| `a0b45e2` | docs: document desktop 2.1 known limitations (#93) — **D5.05** |
| `a3819dd` | docs: close out Phase 5 DoD with evidence (#95) |

### 变更面

文档（测试矩阵、用户指南、性能基线、已知限制、架构、打包计划、Phase 5 计划）、中英对照、README 入口、`CHANGELOG`，以及 `APP_VERSION` / `pyproject.toml` / 各 package / Tauri / Cargo 的版本对齐。本范围 **未** 新增 API 路由、中间件、Tauri capability 或 CI workflow。

## 3. Bugbot 发现

| Severity | Location (file:line) | Finding |
| -------- | -------------------- | ------- |
| medium | `docs/v2_performance_baseline.md:33` | D5.03 章节标题为 **Desktop path-import performance**，但记录的是 `npm run perf:api` 结果；该脚本走 multipart `POST /api/projects/{id}/import`，而非桌面 `POST .../imports/from-paths`。导入耗时 / 峰值 RSS 实为 API 上传路径证据，却被 Phase 5 收尾当作 D5.03 完成。 |

### Bugbot 细节

`apps/api/app/devtools/performance_smoke.py` 通过 `/import` 的 `files=…` 上传。基线文案写 “path-equivalent synthetic import”，弱化了措辞，但未消除与 D5.03 验收意图（「100 张 **路径导入** + process RSS」）及章节标题的不一致。打包计划 / 可行性说明重复了同一 `perf:api` 证据。

**建议跟进（本评审未改代码）：** (a) 增加 from-paths smoke 并重测，或 (b) 重命名/澄清 D5.03 文档与 DoD 表述，仅声明 multipart 导入下的 API/sidecar RSS，并将真路径导入标为 pending。

## 4. Security 发现

| Severity | Location (file:line) | Finding |
| -------- | -------------------- | ------- |
| — | — | 本 diff 无 medium / high / critical 问题。 |

### 已审区域（通过）

| 区域 | 结果 |
| ---- | ------ |
| 经 `/api/meta` 的路径 / `data_dir` 披露 | 既有；loopback Host；仅文档 |
| 测试矩阵中的 loopback / CORS / LAN 表述 | 与实现一致；无扩大放行指引 |
| 未签名 NSIS/DMG 说明 | 与签名 runbook 一致；可接受的 RC 姿态 |
| 文档/CI 中的密钥 | 无；仅有主机名标签 |
| 不安全的安装/测试指引 | 符合 local-first 威胁模型 |
| 版本 / menu / `tauri.conf.json`  bump | 无 CSP/capability 变更 |

### 未达上报门槛的运维备注

1. **未签名产物** — 完成 Authenticode + 公证前仍有替换风险（`docs/desktop_signing.md`）。
2. **本机 `GET /api/meta`** — 能连上端口的本机客户端可无鉴权读安装元数据；行为未变，用户指南中更可见。
3. **Sidecar ready 行 / 日志** — stdout 与 `{data_dir}/logs/sidecar.log` 含 `data_dir=`；同用户本机可见。

## 5. Phase 5 DoD 快照（评审视角）

| 关卡 | 评审备注 |
| ---- | ----------- |
| D5.01 测试矩阵 | 已有（`docs/desktop_testing.md` + zh）；命令与安全行连贯 |
| D5.02 用户文档 | 用户指南 + README 入口；copy-not-move / data-dir 已覆盖 |
| D5.03 性能说明 | 已记录，但 **证据路径 ≠ 路径导入**（Bugbot medium） |
| D5.04 版本 RC | `2.1.0-desktop` 各表面已对齐并有 changelog |
| D5.05 已知限制 | 桌面 2.1 条目齐全；未签名 / WSL GUI / 托盘延期已写明 |

## 6. 建议

1. 内部桌面 RC 轨道可继续把 Phase 5 收尾留在 `main`。
2. 在把「路径导入性能」视为已验证之前，先修正或明确收窄 D5.03 标注 — **[#96](https://github.com/joe-cheung-cae/frame-pilot/issues/96)**（文档澄清）与 **[#97](https://github.com/joe-cheung-cae/frame-pilot/issues/97)**（from-paths 实测跟进）。
3. **公开签名**发布前，完成签名/公证，并考虑在用户指南中补充校验和 / 出处说明 — **[#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98)**。

---

由 Bugbot + Security Review 子代理于 2026-08-29 并行生成。Diff 基线：`f4cee3d` … tip：`a3819dd`。

### 本评审已开跟踪议题

| Issue | Type | Title |
| ----- | ---- | ----- |
| [#96](https://github.com/joe-cheung-cae/frame-pilot/issues/96) | Bug | 澄清 D5.03 证据为 multipart `perf:api`，非 `from-paths` |
| [#97](https://github.com/joe-cheung-cae/frame-pilot/issues/97) | Feature | 测量桌面 `from-paths` 路径导入 sidecar RSS |
| [#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98) | Task | 公开签名发布加固（Phase 5 安全评审运维项） |


## 处理状态

| Issue | 状态 | 处理 |
| ----- | ---- | ---- |
| [#96](https://github.com/joe-cheung-cae/frame-pilot/issues/96) | 已解决 | 文档澄清 multipart 与 `from-paths` |
| [#97](https://github.com/joe-cheung-cae/frame-pilot/issues/97) | 已解决 | `perf:api --import-mode from-paths` + 100 张 RSS 行 |
| [#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98) | 已解决（文档） | 公开出处 + 签名清单；证书仍属组织密钥 |

