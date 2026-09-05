# FramePilot v2 发布候选检查清单

> 语言：[English](v2_release_candidate_checklist.md) | **中文**

本检查清单是 FramePilot v2.0 的发布候选决策记录。它总结已实现内容、已验证内容、仍未验证内容，以及打 v2.0 标签之前必须成立的条件。

## 发布状态摘要

FramePilot v2.0 是面向 JPEG、PNG 和 WebP 照片筛选的本地优先 MVP-plus 发布候选。核心工作流已实现：本地项目创建、本地导入、可查询的导入和处理任务、确定性评分、分组、排序、以键盘为先的复核、手工状态/评分覆盖、CSV 导出、ZIP 导出、文件夹导出，以及本地导出历史。

当前 RC 决策：真实世界/手工算法验证笔记记录在 `docs/v2_real_world_validation_notes.zh.md`（2026-08-17，pass with notes）。无限定条件的 `v2.0.0` 标签仍要求在待打标签的提交上运行 `npm run check:pretag`。

本文件仍是 **v2.0 RC 决策记录**（验证运行日期 2026-06-05）。它不是现行下一步指针。rc2 之后，`main` 还交付了：

- `2.1.0-desktop` 未签名 Tauri sidecar RC（桌面封装第 0–5 阶段）
- 第六 / 6.1 阶段本地作业回收（`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` 默认开启）
- 第七阶段协作式处理作业取消（J7.01–J7.06）
- 未签名 Windows NSIS GUI lifecycle QA（[#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)，仅 Windows）
- 第八阶段本地 HEIC/HEIF 静帧预览（H8.01–H8.06）

**`main` 上的下一步：** 第九阶段剩余 stretch 收口（S9.00–S9.13），每次运行一个 GitHub issue。S9.00–S9.12 已落地；从 S9.13 开始。不要发明第十阶段。下文关于作业持久性、桌面打包、处理取消和 HEIC 预览的条目描述的是 2026-06-05 rc2 产品，除非另有后续切片说明。见 `develop_plan.zh.md` §1.1 与 `docs/plans/2026-09-04-remaining-stretch.zh.md`。

## 已实现的 v2.0 功能

- 带托管或自定义本地项目存储的本地项目创建。
- JPEG、PNG 和 WebP 导入。
- 对延后的 HEIC 和 RAW 格式报告不支持格式。
- upload/register 导入阶段，随后是进程内后台衍生件阶段。
- 导入任务轮询，含进度、终态、重试、过期检测和协作式取消。
- 处理任务轮询，含进度、活动导入冲突拒绝、过期检测、过期失败后的部分组清理，以及对未变更项目的幂等重跑。
- 本地缩略图和预览生成。
- 元数据提取、确定性评分、感知哈希和轻量 embedding。
- 确定性分组，使用拍摄时间或文件名候选窗口、元数据兼容性、感知哈希距离、embedding 回退、union-find 和时间跨度拆分。
- 带保守推荐解释的确定性排序。
- 实验性本地人脸和睁眼启发式信号。
- 以键盘为先的筛选工作区，含筛选器、组、对比模式、缩放、状态和星级。
- 面向更大项目的有界照片、组、胶片条和对比渲染。
- CSV、ZIP 和文件夹导出，含导出历史、本地路径安全检查，以及 ZIP/文件夹源文件限制在项目 `originals/` 下。
- 面向发布的根、web、API package、lockfile 根和 FastAPI OpenAPI 元数据对齐到 `2.0.0-rc2`。

## 已验证工作流

- 当前 rc2 工作树已记录 `npm run verify` 通过。
- 活动导入、过期处理清理、导出来源包含性和项目路由回归，由后端、前端单元和 E2E 测试覆盖。
- 默认 100 张生成照片的真实浏览器-后端工作流已验证。
- 500 张生成大图真实浏览器-后端工作流已验证，并在重复运行中稳定。
- 1,000 张生成真实浏览器-后端工作流已对小型生成 JPEG 验证。
- 1,000 张生成 3000x2000 真实浏览器-后端工作流已作为可选慢速验证通过。
- 2,000 张种子化元数据筛选工作区验证已通过。
- 确定性分组、排序、评分、导出、重试、取消、过期任务和状态更新测试已记录为通过。

## 当前 RC 验证运行

运行日期：2026-06-05。

| 命令 | 结果 | 备注 |
| ------- | ------ | ----- |
| `git status --short` | passed | 当时存在有意的 rc2 源码、测试、元数据、工具和文档变更。 |
| `npm run verify` | passed | 143 个后端测试、83 个前端单元测试、lint、typecheck、发布脚本测试和 Next 生产构建通过。 |
| `npm run check:artifacts` | passed | 未发现已跟踪的生成或私人发布产物。该检查现已包含在 `npm run verify` 中。 |
| `npm run test:e2e` | passed | rc2 加固期间 44 个 Playwright 测试通过，包括活动导入守卫、真实本地工作流、默认真实浏览器-后端 smoke，以及 2,000 张种子化筛选工作区 smoke。 |
| `npm run test:e2e -- tests/e2e/local-workflow.spec.ts -g "creates a project and opens the import step" --project=chromium` | passed | 定向 E2E 确认了 Node 颜色和 Next `allowedDevOrigins` 警告清理。 |
| `npm run test:e2e:real-browser` | passed | rc2 加固期间，100 张生成 JPEG 真实浏览器-后端工作流通过。 |
| `npm run test:e2e:real-browser:large` | passed | rc2 加固期间，500 张生成 3000x2000 JPEG 真实浏览器-后端工作流通过。 |

观察到的非阻断警告：FastAPI/TestClient Starlette 弃用警告仍然可见。Node `NO_COLOR`/`FORCE_COLOR` 警告噪声，以及 `/_next/*` 资源的 Next 开发跨源警告，已在 rc2 工作树中清理。

## 必需的测试命令

打 v2.0 标签之前运行这些命令：

```bash
git status --short
npm run check:pretag
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
```

`npm run check:pretag` 包含 `npm run verify`、已跟踪产物检查，以及 rc2 验证决策门槛。2026-08-17 的决策已关闭该门槛；`scripts/check-validation-decision.sh` 在当前 main 上为绿。`npm run verify` 现已包含 `check:validation-decision`，因此若决策文件在没有完成证据或明确豁免的情况下重新打开，默认 PR+main CI 作业会失败。workflow YAML 不需要单独的 `check:pretag` 作业。`npm run check:pretag` 仍是发布时间命令。

在可行时运行完整浏览器 E2E，尤其是前端工作流变更之后：

```bash
npm run test:e2e
```

如果因为太慢或被本地浏览器环境阻断而跳过完整 E2E，在发布说明中记录原因，并改为运行相关的定向 E2E 命令。

## 可选基准命令

将这些用于可选的本地规模验证：

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
FRAMEPILOT_BROWSER_PERF_COUNT=1000 npm run test:e2e:real-browser
FRAMEPILOT_BROWSER_PERF_COUNT=1000 FRAMEPILOT_BROWSER_PERF_WIDTH=3000 FRAMEPILOT_BROWSER_PERF_HEIGHT=2000 FRAMEPILOT_BROWSER_PERF_QUALITY=88 npm run test:e2e:real-browser
```

不要把 2,000 张照片的真实浏览器-后端工作流作为 v2.0 发布门槛，除非它在发布窗口期间被手工运行并记录。

## 安全与隐私检查清单

- 原始源照片永远不会被修改。
- 原始源照片永远不会被自动删除。
- 导入的照片在生成衍生件之前被复制进本地项目存储。
- 同一项目存在活动导入衍生件任务时，处理不能开始。
- ZIP 和文件夹导出要求所选源文件解析到项目 `originals/` 目录内。
- 生成的缩略图、预览、缓存、日志、导出、项目数据库、浏览器 trace、生成照片和测试产物不得提交。
- v2.0 不需要云上传、登录、支付、遥测要求、远程照片处理或协作服务。
- 不提交大模型文件。
- HEIC、RAW、可选 AI 模型、桌面打包和 XMP sidecar 写入在本 **rc2** 记录中被延后。桌面打包后来作为 `2.1.0-desktop` 交付。HEIC 静帧预览后来作为第八阶段交付。RAW、可选模型和 XMP 仍延后。

## 任务系统限制

以下条目是 **2026-06-05 rc2** 的任务合同。当前 `main` 上，残留的活动导入/处理任务默认会被回收（第六阶段 6.1），处理任务可协作取消（第七阶段）。导出任务仍不可取消。

- FastAPI `BackgroundTasks` 在本地 API 进程中运行，不能在 API 进程退出后持久存活。
- 过期任务检测会在配置的过期窗口之后，把被中断的排队或运行中任务标记为失败。
- 过期处理清理会清除部分组、移除照片组分配、把已处理或进行中的照片恢复为可重试的已导入状态，并把项目已处理计数重置为零。
- 活动导入任务会把用户路由回导入进度，并使直接处理请求返回 `409 Conflict`。
- 导入取消是协作式的，不是硬进程杀死。
- 取消在安全检查点停止，保留已完成衍生件，让剩余照片可重试，并且不删除原片。
- 导入重试保留 Photo IDs、`user_status` 和 `star_rating`。
- 重试复用现有有效衍生件，并在可能时从本地已复制原片重新生成缺失衍生件。

## 性能验证状态

- 100、500 和 1,000 张生成真实浏览器-后端验证通过。
- 重复的 500 张大图验证稳定。
- 2,000 张种子化元数据筛选验证通过。
- 2,000 张真实浏览器-后端导入/处理/复核验证尚未完成，不是默认发布门槛。
- 大批量导入仍然计算密集，尤其是衍生件生成和评分，但 upload/register 响应不再被全部衍生件工作阻塞。
- 浏览器内存数字只是 smoke 信号；它们不测量完整进程 RSS、已解码图像内存、GPU 内存或操作系统内存压力。

## 算法验证状态

- 确定性测试覆盖连拍分组、缺失元数据、不应合并的相似项、模糊/曝光惩罚、保守单图推荐和解释。
- 生成的合成基准不能证明真实摄影师质量的排序。
- 来自非私人 Openverse CC0/PDM 照片集的真实世界/手工算法验证笔记记录在 `docs/v2_real_world_validation_notes.zh.md`（2026-08-17，pass with notes）。
- `docs/v2_rc2_validation_decision.zh.md` 是该证据的发布负责人记录。2026-06-05 的 rc2 豁免仅作历史。
- 任何阈值、评分、分组、排序或解释变更都需要聚焦测试。

## 延后功能

历史 rc2 列表。`main` 上的后续切片在括号中注明。

- HEIC 支持。（第八阶段，H8.01–H8.06；已交付）
- RAW 及内嵌 RAW 预览提取。
- XMP sidecar 导出。
- 可选本地 AI 模型。
- 持久化的外部或独立本地 worker 进程。（第六阶段已交付本地 SQLite 轮询 worker 与进程内回收；不是外部队列）
- 桌面打包。（已作为未签名 `2.1.0-desktop` RC 交付）
- 云同步、账户、支付、远程处理和协作。
- 自动删除原始源照片。

## 发布阻断项

- 必需的验证命令失败。
- Git 跟踪了生成或私人照片、项目数据库、导出、ZIP 文件、浏览器 trace 或大产物。
- 文档声称已实现 RAW、HEIC、XMP、云工作流、持久化任务或专业人脸/眼睛检测。
- 已知限制未从 README.zh.md 链接。
- 发布负责人无法说明已实现、已验证、未验证、已延后以及本地安全的内容。
- 缺少手工非私人真实世界算法验证笔记，且发布负责人未记录替代证据或明确豁免。

## 打标签前检查清单

- 复核 `README.zh.md`、`docs/architecture.zh.md`、`docs/api.zh.md`、`docs/scoring.zh.md`、`docs/v2_performance_baseline.zh.md`、`docs/v2_known_limitations.zh.md` 和本检查清单。
- 确认 `docs/v2_rc2_validation_decision.zh.md` 记录了已完成的验证证据或明确的发布负责人豁免。
- 运行 `npm run check:pretag`。
- 确认 `npm run check:artifacts` 通过，或通过 `npm run verify` 依赖同一检查。
- 运行完整 E2E，或明确跳过并记录原因。
- 确认 `git status --short` 只包含有意的发布变更。
- 确认未跟踪生成图像、私人数据集、导出、ZIP 文件、trace、数据库、缓存目录、virtualenv 或 `node_modules` 文件。
- 记录最终发布决策以及任何被跳过的可选基准。

## 发布后后续步骤

- 可选：在后续里程碑之前准备许可清晰的摄影师连拍/场次集，以及一次 2,000 张真实浏览器-后端运行。
- 用已测量的失败模式重新审视持久化本地 worker 架构。
- 仅通过聚焦、带测试的抽取继续筛选工作区可维护性。
- XMP sidecar 导出和 RAW 预览是第九阶段 issue S9.05 与 S9.04（`docs/plans/2026-09-04-remaining-stretch.zh.md`）。HEIC 静帧预览已作为第八阶段交付（`docs/plans/2026-09-04-heic-preview.zh.md`）。不要发明第十阶段。
