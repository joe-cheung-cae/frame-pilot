# FramePilot v2.0 RC2 发布评审

> 语言：[English](v2_release_review.md) | **中文**

评审日期：2026-06-05。

本文件是 2026-06-05 的 rc2 工程评审快照。它不是当前发布结论。
已完成的 2026-08-17 真实世界算法置信度门槛记录在 `docs/v2_rc2_validation_decision.zh.md`。

## 1. 发布结论

快照（2026-06-05）：仅准备好供产品负责人手工验证。

在 rc2 加固之后，本地 MVP-plus 范围的自动化发布门槛为绿：`npm run verify`、针对最终本地工具清理的定向 E2E、默认真实浏览器-后端 smoke、500 张大图真实浏览器-后端 smoke，以及完整 Playwright E2E 均在本分支通过。仓库已记录本地优先模型、JPEG/PNG/WebP 支持、延后的 RAW/HEIC 工作、进程内任务限制、协作式取消、重试行为、合成基准注意事项，以及启发式人脸/睁眼信号。

评审当时，无限定条件的 `v2.0.0-rc2` 标签被阻断，直到发布负责人记录来自非私人真实世界照片集的手工验证笔记，或在 `docs/v2_rc2_validation_decision.zh.md` 中明确豁免该证据。该算法置信度门槛后来于 2026-08-17 完成；参见 `docs/v2_rc2_validation_decision.zh.md`。

## 2. 当前分支与 Git 状态

- 分支：`codex/v2-next-iteration`。
- 本次 rc2 评审期间的 Git 状态：存在有意的 rc2 源码、测试、元数据、工具和文档变更。
- 当前基准提交：`0415a87`（`v2.0.0-rc1`、`main`、`origin/main`）。
- 最近提交：
  - `0415a87 (HEAD -> codex/v2-next-iteration, tag: v2.0.0-rc1, origin/main, main) docs: prepare real-world validation package`
  - `4ff3332 docs: add v2 release review`
  - `6238a75 docs: add v2 release candidate checklist`
  - `f03cd49 v2: add cooperative import job cancellation`
  - `8ce1d11 v2: add stale import job retry flow`
  - `1e9425c (origin/main, origin/HEAD) docs: record import worker validation`
  - `170385a test: cover background import readiness`
  - `ade5d4c feat(web): poll import derivative jobs`
  - `00d18a5 feat(api): run import derivatives in background`
  - `a1b4cca (codex/v2-current-tasks-review) Merge pull request #1 from joe-cheung-cae/feature/v2-performance-iteration`
- Git 中的生成产物：`git ls-files | rg "(node_modules|\\.venv|exports|cache|\\.zip$|\\.jpe?g$|\\.png$|\\.webp$|\\.arw$|\\.cr3$|\\.nef$|\\.dng$|\\.heic$|\\.sqlite$|\\.db$)"` 未发现。
- 本次评审后的预期工作树：仅有意的 rc2 代码、测试、元数据、工具和文档变更。

## 3. 已实现的 v2.0 能力

- 带托管或自定义本地项目存储的本地项目工作流。
- JPEG、PNG 和 WebP 导入，并对延后的 HEIC 和 RAW 文件给出明确的不支持格式消息。
- 导入拆分为 upload/register 与进程内后台衍生件任务。
- 导入和处理任务的进度轮询。
- 过期导入和处理任务检测。
- 同一项目存在活动导入衍生件任务时，直接处理请求以 `409 Conflict` 被阻断。
- 项目路由、处理 UI 和筛选 UI 会把有活动导入的项目送回导入进度，而不是显示不完整的处理或复核状态。
- 过期处理清理会清除部分组，并把已处理或进行中的照片重置为可重试的已导入状态。
- 协作式导入取消。
- 对失败、`complete_with_errors`、过期失败和已取消导入任务的重试。
- 重试保留 Photo IDs、`user_status` 和 `star_rating`，并复用有效衍生件。
- 确定性技术评分、感知哈希、轻量 embedding、分组、排序和解释。
- 以键盘为先的筛选工作区，含筛选器、组、对比、缩放、状态更新、评分、有界渲染和 load-all 控件。
- CSV、ZIP 和文件夹导出，含导出历史、本地路径安全检查，以及 ZIP/文件夹源文件限制在项目 `originals/` 下。
- 根 package、web package、API package、npm lockfile 根条目和 FastAPI OpenAPI 元数据对齐到 `2.0.0-rc2`。
- 后端、前端单元、浏览器 E2E、真实浏览器-后端、合成性能，以及种子化大规模筛选覆盖。

## 4. 已验证工作流

2026-06-05 运行的命令：

| 命令 | 结果 | 证据 |
| ------- | ------ | -------- |
| `git status --short` | passed | 当时存在有意的 rc2 源码、测试、元数据、工具和文档变更。 |
| `git branch --show-current` | passed | `codex/v2-next-iteration`。 |
| `git log --oneline --decorate -n 8` | passed | 当前基准提交是 `0415a87 docs: prepare real-world validation package`。 |
| `npm run verify` | passed | Ruff API lint、web ESLint、TypeScript、143 个后端测试、83 个前端单元测试、发布脚本测试和 Next 生产构建通过。 |
| `npm run check:artifacts` | passed | 未发现已跟踪的生成或私人发布产物。该检查现已包含在 `npm run verify` 中。 |
| `npm run test:e2e` | passed | rc2 加固期间 44 个 Playwright 测试通过，包括真实本地工作流、默认真实浏览器-后端 smoke、活动导入守卫覆盖、导入进度/取消/重试 UI 覆盖，以及 2,000 张种子化筛选工作区 smoke。 |
| `npm run test:e2e -- tests/e2e/local-workflow.spec.ts -g "creates a project and opens the import step" --project=chromium` | passed | 本地工具清理后定向 E2E 通过，且没有 Node 颜色或 Next `allowedDevOrigins` 警告噪声。 |
| `npm run test:e2e:real-browser` | passed | rc2 加固期间，1 个 Playwright 测试通过：100 张生成 JPEG 走真实前端/后端工作流。 |
| `npm run test:e2e:real-browser:large` | passed | rc2 加固期间，1 个 Playwright 测试通过：500 张生成的 3000x2000 JPEG 走真实前端/后端工作流。 |

验证细节：

- `npm run verify`：143 个后端测试通过，有一个已知的 Starlette/TestClient 弃用警告；83 个前端单元测试通过；发布脚本测试通过；Next 构建成功完成；已跟踪发布产物检查通过。
- rc2 加固期间完整 E2E：44 个测试通过。种子化 2,000 张筛选 smoke 仍被覆盖，并包含新的活动导入路由、处理与筛选守卫。
- rc2 加固期间的真实浏览器-后端 smoke 覆盖包括默认 100 张生成 JPEG 工作流，以及可选的 500 张生成 3000x2000 JPEG 工作流。
- 详细时序基线仍在 `docs/v2_performance_baseline.zh.md`；生成图像时序是回归 smoke 证据，不是真实世界算法验证。

观察到的非阻断警告：

- FastAPI/TestClient `StarletteDeprecationWarning`。

rc2 工作树清理了更早的 Node `NO_COLOR`/`FORCE_COLOR` 警告噪声，以及 `/_next/*` 资源的 Next 开发跨源警告。

## 5. 性能发布基线

- 100 真实浏览器-后端：当前运行和已记录基线均通过。
- 500 真实浏览器-后端：已记录基线对生成图像通过。
- 500 大图重复验证：已记录基线 3 of 3 次运行通过，导入计时稳定。
- 1000 真实浏览器-后端：已记录基线对生成小图以及可选的 3000x2000 生成 JPEG 通过。
- 2000 种子化筛选验证：完整 E2E 当前运行通过了种子化 2,000 张照片浏览器筛选 smoke。
- 2000 真实浏览器-后端：延后/手工。本次评审未运行，不应视为默认 v2.0 发布门槛。

合成基准注意事项：生成 JPEG 对可重复性和回归检查有用，但它们不是精选的真实世界验证，也不能证明摄影师质量的分组/排序。

## 6. 安全与隐私评审

- 原始源照片被复制进本地项目存储，导入后不会被修改。
- 原始源照片永远不会被自动删除。
- 生成的缩略图、预览、缓存、日志、导出、数据库、浏览器 trace、生成照片、ZIP 文件、`node_modules` 和 virtualenv 必须留在 Git 之外。
- 本次评审期间，已跟踪文件中未发现生成或私人产物。
- 不需要云上传、远程处理、用户账户、登录、支付、遥测要求或在线协作依赖。
- 应用假定本地 SQLite 项目元数据和单用户本地运行。
- 资源和导出的提供/写入路径被记录为经过项目根检查，测试中有路径安全覆盖。
- ZIP 和文件夹导出现在要求所选源文件解析到项目 `originals/` 目录内，因此损坏的元数据不能让文件导出复制任意本地文件。

## 7. 任务系统评审

- 导入 upload/register 在昂贵的衍生件工作完成之前返回。
- 导入衍生件生成和处理任务通过本地 API 进程中的 FastAPI `BackgroundTasks` 运行。
- 任务进度可通过轮询和任务历史看到。
- 活动导入任务会阻断直接处理请求，并把项目列表、仪表盘、处理页和筛选工作区路由回导入进度。
- 导入取消是协作式的，并在安全检查点停止。它不是硬进程杀死。
- 过期的排队或运行中任务会在配置的过期窗口之后被检测并标记为失败。
- 过期处理失败现在会清除部分组、移除照片组分配、把已处理或进行中的照片重置为可重试的已导入状态，并把项目已处理计数重置为零。
- 重试会创建新的导入任务，保留现有 Photo IDs、`user_status` 和 `star_rating`，复用有效衍生件，并在可能时从本地已复制原片重新生成缺失衍生件。
- 当前任务系统不能在 API 进程退出后持久存活。未来的持久化本地 worker 或可安全重启的任务队列，是 v2.0 之后的主要架构建议。

## 8. 算法评审

- 评分是确定性且可解释的，使用本地锐度、模糊风险、曝光、对比度、噪声风险、简单美学，以及实验性人脸/睁眼启发式信号。
- 分组使用确定性候选窗口、元数据兼容性、感知哈希距离、轻量 embedding 回退、union-find 和时间跨度拆分。
- 组内排序保守，并存储组 `score_summary` JSON，包含最佳分数、分数差距、置信度、推荐计数和解释文本。
- 人脸和睁眼信号是启发式且实验性的。它们不是专业人脸检测、关键点检测、眼睛状态检测、身份识别或生物特征分析。
- 在本次 2026-06-05 评审时，手工真实世界验证尚未完成。根据本次评审证据，不建议更改阈值、评分、分组、排序或解释。
- `docs/v2_rc2_validation_decision.zh.md` 后来记录了完成该门槛的 2026-08-17 验证证据。

## 9. 已知限制

- RAW 和 HEIC 支持被延后。
- AI 模型和大体积捆绑模型文件被延后。
- 桌面打包被延后。
- XMP sidecar 导出被延后。
- 2,000 张真实浏览器-后端导入/处理/复核尚未验证。
- 本次评审时，真实相机 JPEG 多样性尚未用已记录的非私人手工笔记验证。笔记后来于 2026-08-17 记录在 `docs/v2_real_world_validation_notes.zh.md`。
- 完整浏览器进程 RSS、已解码图像内存、GPU 内存和操作系统内存压力尚未验证。
- 导入和处理任务在进程内运行，不能在 API 进程退出后持久存活。
- 生成和合成基准不能替代真实世界/手工算法验证。
- CSV、ZIP 和文件夹导出是本地同步操作。

## 10. 发布阻断项

严重：

- 本次评审的自动化验证中未发现。

高：

- 评审当时，手工非私人真实世界算法验证笔记尚未记录，除非豁免，否则阻断无限定条件的 RC 标签。
- 该门槛不再待处理：`docs/v2_rc2_validation_decision.zh.md` 记录了已完成的 2026-08-17 验证证据。

中：

- FastAPI `BackgroundTasks` 在进程内运行，不能在 API 重启后持久存活。
- 2,000 张真实浏览器-后端工作流仍为延后/手工。
- 完整浏览器 RSS、已解码图像内存、GPU 内存和操作系统级压力尚未测量。

低：

- 在 FastAPI/Starlette 测试客户端栈迁移到 `httpx2` 或等效受支持客户端之前，Starlette/TestClient 弃用警告仍然可见。

## 11. 手工验证检查清单

- 运行非私人真实世界照片验证，最好先用 50 到 300 张照片。
- 检查分组错误合并。
- 检查漏组。
- 对照人工复核者选择检查排序不匹配。
- 检查不良或误导性解释。
- 用非私人数据确认 CSV、ZIP 和文件夹导出输出。
- 在 UI 中手工确认重试和取消行为。
- 在干净的本地环境上确认 README.zh.md 中的命令。
- 把所有照片、生成的项目数据、导出、ZIP 文件、trace 和 SQLite 数据库留在 Git 之外。

## 12. 打标签建议

验收后的建议标签名：`v2.0.0-rc2`。

评审当时的建议：不要仅凭自动化立即打标签。在产品负责人手工验证完成，或在发布说明中明确豁免之后再打标签。2026-08-17 的验证决策后来关闭了该门槛。

发布说明应链接 `docs/v2_rc2_validation_decision.zh.md` 和已完成的验证笔记文件。

打标签前的精确命令：

```bash
git status --short
git branch --show-current
git log --oneline --decorate -n 20
npm run check:pretag
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
npm run test:e2e
```

`npm run check:pretag` 包含 `npm run verify`、已跟踪产物检查和验证决策检查。2026-06-05 评审预期它会失败，因为当时 `docs/v2_rc2_validation_decision.zh.md` 仍为待处理且未豁免。2026-08-17 的决策关闭了该门槛。

可选手工基准，不是默认发布门槛：

```bash
FRAMEPILOT_BROWSER_PERF_COUNT=2000 npm run test:e2e:real-browser
```

打标签后的精确后续步骤：

```bash
git tag v2.0.0-rc2
git status --short
```

然后记录或链接手工验证笔记，发布 RC 决策，并开启 v2.0 之后的第一次迭代，用于持久化任务和真实世界算法调优。

## 13. 后续开发迭代

1. 持久化本地 worker 或可安全重启的任务队列。
2. 根据已记录的非私人验证笔记做真实世界算法阈值调优。
3. 可选 XMP sidecar 导出。
4. 可选 2,000 张真实浏览器-后端手工基准。
5. 在 v2.0 处理架构稳定之后，可选 RAW/HEIC 预览提取。
