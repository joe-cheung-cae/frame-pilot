# FramePilot

> 语言：[English](README.md) | **中文**

FramePilot 是一款本地优先的 AI 辅助照片筛选 Web 应用。当前 v2 本地 MVP-plus 基础把原片留在用户机器上，生成本地预览，计算可解释的技术分数，将相似帧分组，在每组中推荐最强图像，并让用户覆盖每一个决定。

## 当前 v2 基础

- Next.js、React、TypeScript、Tailwind CSS 前端。
- FastAPI、Pydantic、SQLModel、SQLite 后端。
- 本地项目文件夹，包含原片、缩略图、预览、结构化的导出/缓存子目录和日志。
- 导入 JPEG、PNG、WebP、HEIC/HEIF、AVIF 以及带内嵌预览的 RAW 静帧。原片原样拷贝；缩略图和预览为 WebP；评分和分组在解码后的 RGB 上运行（HEIC/HEIF 用本地 `pillow-heif`，AVIF 用 Pillow 自带的 `AvifImagePlugin`，RAW 只走 LibRaw `extract_thumb`）。没有内嵌预览的 RAW 以明确的本地消息跳过。
- 导入任务在完成本地上传/登记工作后返回，并在可查询、可协作取消的本地后台任务中继续生成派生文件。
- 导入派生工作仍在进行时会阻止处理，项目导航会把用户带回导入进度，直到导入任务到达终态。
- 处理（分组和排序）以及导出作业也可通过同一取消路由协作取消。桌面退出可以取消活动处理或导出任务，再 SIGTERM sidecar。
- 确定性缩略图和预览生成。
- 基本元数据提取和可解释的图像质量评分。
- 实验性的本地人脸与睁眼启发式信号。
- 用于近重复分组的轻量 embedding 近似。
- 以组为中心的筛选，按推荐优先的复核顺序。
- Pick、Maybe、Reject 和 Unreviewed 状态。
- 键盘复核快捷键：方向键、P、M、X、U、1-5、0、Space、Z、C、G、F 和 E。
- CSV、文件夹和 ZIP 导出模式，具有唯一的本地导出输出、导出历史、文件导出对项目原片的来源约束，以及可选的 XMP sidecar 勾选（默认关），只在项目导出目录下写 `.xmp`。

已知的 v2.0 限制：

- DNG、ARW、CR3、NEF 等 RAW 文件在有内嵌预览时导入（原样拷贝字节；用预览 RGB 生成 WebP；不 demosaic）。没有预览的 RAW 以明确的本地消息跳过。HEIC/HEIF 与 AVIF 静帧可本地导入；不实现 Live Photo 配套 `.mov` 或 HDR gain-map 色调映射。可选 XMP sidecar 只写在导出目录（永不写到原片旁或图像字节内）。
- 导入和处理任务运行在本地 API 进程或可选本地 worker（`npm run worker`）中。进度、协作式导入/处理/导出取消、过期任务检测、活动导入处理保护、安全导入重试和过期处理清理可用。默认情况下，下次启动会把残留的活动导入/处理任务标为 `interrupted` 并回收（`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` 默认开启；设为 `0`/`false`/`no`/`off` 则回到失败并重试）。导出任务可取消，不会被回收（fail-and-cleanup）。
- 实验性人脸与睁眼信号是确定性本地启发式，不是专业人脸检测、眼睛状态检测、身份识别或生物特征分析。
- 分组和排序仍是推荐辅助。用户通过手工状态和星级保留最终控制。

## 安装

```bash
npm run install:all
```

## 本地运行

```bash
npm run dev
```

Web 应用运行在 `http://localhost:3000`。本地 API 运行在 `http://127.0.0.1:8000`。

后端数据默认写入 `.framepilot-data`。设置 `FRAMEPILOT_DATA_DIR` 可使用其他本地项目数据位置。

## 桌面应用

可安装的 Windows（NSIS）与 macOS（DMG）构建会为你启动 UI 与本地 API sidecar。安装、数据目录、路径导入（只复制不移动）与导出揭示见 [桌面用户指南](docs/desktop_user_guide.zh.md)。贡献者日常可继续用 `npm run dev`（上方的 web + API）。桌面壳开发用 `npm run dev:desktop`（需要 Rust）；见 [apps/desktop/README.zh.md](apps/desktop/README.zh.md)。

典型工作流：

1. 创建项目。
2. 导入 JPEG、PNG、WebP、HEIC/HEIF、AVIF 或带内嵌预览的 RAW 静帧。有效文件在本地登记，预览生成通过可见的导入任务继续，运行中的导入可在安全检查点取消，而不会删除原片或已完成的预览。同一文件再次导入或导入重试可以复用现有本地记录和已生成预览。没有预览的 RAW 会跳过。
3. 导入任务完成后再运行处理。若导入仍在运行，FramePilot 会把项目留在导入进度上，并拒绝直接的处理请求。
4. 按组复核照片，并标记 Pick、Maybe、Reject 或 Unreviewed。
5. 将一个或多个所选状态导出为 CSV、文件夹或 ZIP。CSV 和 ZIP 导出可从浏览器下载，此前的导出仍显示在导出历史中。

## 验证

```bash
npm run verify
```

这会运行 API lint、web lint、TypeScript 检查、后端测试、前端单元测试和前端生产构建。
它还会运行 `npm run check:artifacts`，若 Git 跟踪了生成或私人发布产物则失败；
并运行 `npm run check:validation-decision`，这样默认 PR+main 门禁会在
`docs/v2_rc2_validation_decision.md` 中的发布负责人决策仍为待处理、豁免字段不全、或缺少笔记文件时失败。
该子集在当前 main 上为绿，不需要单独的 GitHub Actions 作业。

GitHub Actions（`.github/workflows/verify.yml`）会跑 `npm run verify`、独立的 Playwright 作业（`npm run test:e2e`：mocked E2E 加上 `tests/e2e/real-local-smoke.spec.ts`）、独立的 100 张真实浏览器作业（`npm run test:e2e:real-browser`）、独立的冻结 sidecar 作业（先 `npm run packaging:sidecar`，再 `npm run test:sidecar`，确保 `GET /health` 在没有 `PYTHONPATH` 时通过），以及独立的桌面 HTTP 冒烟（`npm run test:desktop:smoke`：`/health`、`/api/projects`、桌面 Origin CORS、攻击者 `Host` → 403）。这些作业不安装 Rust、不签名、不启动打包 GUI，也不跑 `test:e2e:real-browser:large`。workflow YAML 不需要单独的 `check:pretag` 作业；`npm run verify` 已包含验证决策检查。

在给发布候选打标签之前，运行打标签前门槛：

```bash
npm run check:pretag
```

这是发布时间命令：`npm run verify` 加上 `npm run check:validation-decision`（后半段已包含在 `verify` 中）。

更短的仅测试路径：

```bash
npm run test
```

CI 已在 pull request 与 `main` 上跑浏览器 E2E。当你改动项目创建、导入、处理、筛选或导出流程时，本地跑同一覆盖：

```bash
npm run test:e2e
```

CI 也会在 pull request 与 `main` 上跑 100 张真实浏览器-后端 smoke。本地可用同一命令验证该工作流：

```bash
npm run test:e2e:real-browser
```

默认真实浏览器-后端 smoke 使用 100 张生成 JPEG，使常规本地验证保持可行。更大的运行是可选的，**不**纳入默认 CI 门禁：

```bash
npm run test:e2e:real-browser:large
FRAMEPILOT_BROWSER_PERF_COUNT=1000 npm run test:e2e:real-browser
FRAMEPILOT_BROWSER_PERF_COUNT=1000 FRAMEPILOT_BROWSER_PERF_WIDTH=3000 FRAMEPILOT_BROWSER_PERF_HEIGHT=2000 FRAMEPILOT_BROWSER_PERF_QUALITY=88 npm run test:e2e:real-browser
```

这些命令在被忽略的测试输出目录下生成非私人本地测试图像和项目数据。不要提交生成的照片、项目数据库、导出、ZIP 文件、浏览器 trace 或私人数据集。

为性能验证生成确定性本地图像集：

```bash
npm run generate:synthetic -- --output /tmp/framepilot-500 --count 500
```

生成的文件是本地测试夹具，不应提交。

运行本地合成导入/处理性能 smoke：

```bash
npm run perf:api -- --output /tmp/framepilot-perf-500 --count 500
```

该 smoke 命令报告生成、上传/登记导入时间、导入派生完成时间、处理时间和本地进程峰值内存。
它还会默认把合成照片标为 Pick，并记录 CSV、ZIP 和文件夹导出耗时。

将 v2.5 大批量目标作为显式本地验证步骤运行：

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
```

每个数量会在单独的 `count-*` 子目录下写入生成的源、本地元数据和导出。

参见 [FramePilot v2 产品需求](docs/v2_product_requirements.zh.md) 了解目标用户、范围、工作流和发布边界。
参见 [架构](docs/architecture.zh.md) 了解当前后端、前端、存储、处理、桌面 sidecar 和导出边界。
参见 [FramePilot v2 架构](docs/v2_architecture.zh.md) 了解较早的 v2.0 形态架构快照。
参见 [FramePilot v2 里程碑](docs/v2_milestones.zh.md) 了解发布检查点和验证门槛。
参见 [FramePilot v2 测试策略](docs/v2_testing_strategy.zh.md) 了解预期的单元、集成、E2E 和性能验证层。
参见 [FramePilot v2 性能基线](docs/v2_performance_baseline.zh.md) 了解最近记录的合成大批量 smoke 结果。
参见 [FramePilot v2 发布候选清单](docs/v2_release_candidate_checklist.zh.md) 了解当前发布就绪清单、必需命令、发布阻塞项和打标签前检查。
参见 [FramePilot v2 已知限制](docs/v2_known_limitations.zh.md) 了解已接受的本地 MVP-plus 限制。
参见 [FramePilot v2 真实世界算法验证](docs/v2_real_world_validation.zh.md) 了解非私人照片集的手工验证协议。
参见 [FramePilot v2 真实世界验证笔记](docs/v2_real_world_validation_notes.zh.md) 了解 2026-08-17 非私人 Openverse 照片复核。
参见 [FramePilot v2 验证决策](docs/v2_rc2_validation_decision.zh.md) 了解该证据的当前发布负责人记录（更早的 rc2 豁免仅作历史）。
参见 [FramePilot v2 迁移计划](docs/v2_migration_plan.zh.md) 了解 schema、存储、API 和项目数据迁移规则。
参见 [FramePilot v2 算法策略](docs/v2_algorithm_strategy.zh.md) 了解分组、排序、解释和可选模型策略。

## 桌面打包

CI 可能上传**未签名**的 Windows NSIS 与 macOS DMG 安装包供内部测试。请预期 SmartScreen / Gatekeeper 警告；不要把未签名包当作公开发布。详见 [桌面代码签名手册](docs/desktop_signing.zh.md) 与 [桌面用户指南](docs/desktop_user_guide.zh.md)。缺少证书不得阻塞第一个桌面 RC。手工检查见 [桌面测试矩阵](docs/desktop_testing.zh.md)。

## 隐私

v2 基础不会把原片或生成的预览上传到任何远程服务。导入的图像被复制到本地项目目录，因此原片永不被修改。

实验性人脸与睁眼分数用确定性的颜色和亮度启发式在本地计算。它们是本地排序提示，不是捆绑的专业人脸检测或生物特征模型。

## 许可证

FramePilot 以 [MIT License](LICENSE) 发布。
