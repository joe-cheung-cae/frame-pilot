# FramePilot v2 已知限制

> 语言：[English](v2_known_limitations.md) | **中文**

本文档列出本地 MVP-plus 发布候选版本已接受的 v2.0 限制。这些是产品边界、验证注意事项和工程约束，而不是隐藏缺陷。

## 仅限本地范围

FramePilot v2.0 是一款由本地 FastAPI 服务器和 SQLite 数据库支撑的本地 Web 应用。它不提供云同步、在线协作、用户账户、支付、遥测要求、远程照片处理或移动端访问。

## 支持的文件格式

v2.0 支持以下格式的本地导入与处理：

- JPEG
- PNG
- WebP
- HEIC / HEIF 静帧（本地 `pillow-heif` 解码；WebP 衍生件；导出原始字节）
- AVIF 静帧（仅 `.avif`；Pillow 自带 `AvifImagePlugin`；WebP 衍生件；导出原始字节）
- 带内嵌预览的 RAW（`.dng`、`.arw`、`.cr3`、`.nef`；原样拷贝；只走 LibRaw `extract_thumb`；用预览 RGB 生成 WebP 衍生件；导出原始字节）

不受支持的文件会在本地报告，而不是远程上传或解码。

## 延后的格式

完整 RAW 显影（demosaic / `postprocess`）仍延后。没有内嵌预览的 RAW 以 `RAW file has no embedded preview; FramePilot does not demosaic` 跳过，不会拷进 `originals/`。不接受 `.cr2`、`.raf`、`.orf`、`.rw2` 等额外 RAW 扩展名。HEIC/HEIF 与 AVIF 静帧可本地导入；不实现 Live Photo 配套 `.mov`、`.avifs` 序列或 HDR/gain-map 色调映射。导入、`originals/`、相机文件旁和图像字节都不会写入 XMP。

`pillow-heif` 为 BSD-3-Clause。其 wheel 在 API/sidecar 运行时内带有 **LGPL** 的 `libheif`（及编码器）。FramePilot 不把 libheif 源码塞进本 MIT 树。

`rawpy` 为 MIT。其 wheel 在 API/sidecar 运行时内带 **LGPL-2.1 / CDDL** 的 LibRaw。FramePilot 不把 LibRaw 源码塞进本 MIT 树。

## 后台任务持久性

导入与处理工作使用本地 API 进程中的 FastAPI `BackgroundTasks`（或可选的本地 worker 入口）。任务具有可见进度、过期检测（存在租约心跳时为 2 分钟，否则 `updated_at` 为 10 分钟）和重试路径。默认情况下，它们在 API 进程退出后是持久的：如果 API 进程在工作期间停止，下次启动会将残留的活动任务标为 `interrupted` 并自动续跑。

**默认开启回收（第 6.1 阶段，[#105](https://github.com/joe-cheung-cae/frame-pilot/issues/105)）：** 启动时会将残留的活跃导入/处理任务标为 `interrupted`，并在进程内自动续跑导入衍生件（以及对中断的处理任务清理不完整分组后重建）。也可通过 `npm run worker` / `python -m app.worker` 运行本地 worker 入口。设置 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0`（或 `false`/`no`/`off`）可退回旧的失败并重试行为：下次启动会把残留的活动任务标为失败，以便用户手动重试。无论哪种方式，导出任务在重启时仍失败并清理。详见 [第六阶段计划](plans/2026-08-29-phase6-durable-jobs.zh.md)。

当同一项目存在活动的导入衍生件任务时，处理会被有意阻塞。直接的处理请求返回 `409 Conflict`；项目列表、仪表盘、处理页和筛选工作区会把用户送回导入进度，直到该导入任务到达终态。

如果处理任务在提交了部分分组之后过期，清理会清除部分分组、移除分组分配，将已处理或进行中的照片恢复为可重试的已导入状态，并将项目已处理计数重置为零。这可以防止把过期的部分推荐当成处理已完成来复核。

## 取消语义

导入、处理和导出取消都是协作式的。取消请求会持久化一个标志，后台 worker 在安全检查点读取该标志。取消不是硬性进程杀死，可能不会立即停止，并且永不修改或删除源原图。导入取消会保留已完成的衍生件，让未处理照片保持可重试。处理取消随后清分组：在飞照片回到 `imported`，`user_status` 与 `star_rating` 保留，导入衍生件保留。重跑分组走 `POST /process`；`/retry` 仍仅导入。导出取消将作业终态为 `cancelled`，对应导出记录走 fail-and-cleanup（`failed`）：项目导出根下的不完整 CSV/ZIP/文件夹会被删除；根外路径保留。再导出走新的 `POST /export`。导出作业不会被回收。

桌面端在导入、处理或导出仍活动时关闭，可以 POST 同一取消路由，最多等待 10 秒，然后对 sidecar 发送 SIGTERM（继续工作 / 退出并取消导入或处理或导出 / 仍要退出）。默认下次启动会将残留的导入/处理任务标为 `interrupted` 并回收；残留导出仍 fail-and-cleanup。设置 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` 后，残留导入/处理任务会改为通过旧的启动扫描标记为 `failed`。硬杀死不会被标记为 `cancelled`。

处理暂停是协作式的，且与取消分开（`POST .../jobs/{job_id}/pause`，`pause_requested`）。工作器在安全检查点停下，不 finalize 为 `cancelled`，清掉半成品分组，并将作业标为 `paused`。恢复是经新的 `POST /process` 做 clear-and-rerun；原地从半批次哈希继续未实现。导入和导出作业不能暂停。桌面退出仍走取消而不是暂停。

## 重试语义

导入重试适用于失败、`complete_with_errors`、过期失败以及已取消的导入任务。重试会创建新的导入任务，保留现有 Photo ID、`user_status` 和 `star_rating`，复用有效衍生件，并在可能时从本地已复制原图重新生成缺失衍生件。重试不会引入外部队列，也不会重新注册一个新的外部源文件夹；启动回收默认开启，中断的导入会在重启后进程内续跑。

## 性能注意事项

大型导入仍然计算密集。在已记录的本地机器上，生成的 100、500 和 1,000 张照片真实浏览器-后端工作流可以通过，2,000 条种子元数据筛选也可以通过，但默认并未验证 2,000 张照片的真实浏览器-后端导入/处理/复核。全分辨率相机 JPEG 多样性、长时间复核会话以及操作系统内存压力仍然测量不足。

## 浏览器内存测量注意事项

浏览器基准的堆值来自 Chromium 冒烟指标，例如可用时的 `performance.memory` 或 CDP 指标。它们不是完整的浏览器进程 RSS、解码图像内存、GPU 内存、跨浏览器内存或操作系统压力指标。

## 合成基准注意事项

生成的 JPEG 基准有利于可重复性和回归检测。它们不能替代使用非私有、接近相机照片集进行的真实世界/人工算法验证。合成图像可能低估真实噪声、镜头表现、主体运动、光照、压缩伪影和创作意图。

发布负责人决策记录是 `docs/v2_rc2_validation_decision.zh.md`。一次 Tier B 非私有 Openverse CC0/PDM 照片通过记录在 `docs/v2_real_world_validation_notes.zh.md`（2026-08-17），并取代更早的 rc2 豁免。合成 JPEG 基准仍然不能替代那次人工复核。

## 分组与排序启发式限制

分组与排序是确定性的推荐辅助。它们可能错误合并视觉相似但无关的场景，漏掉元数据稀疏或文件名间隔很大的分组，把技术干净但意义较弱的帧排在更好的创作选择之上，或对含糊集合给出低置信度推荐。用户必须通过手动状态和星级保持最终控制。

## 人脸与睁眼启发式限制

人脸与睁眼分数是轻量本地启发式，不是专业人脸检测、关键点检测、眼睛状态检测、身份识别或生物特征分析。它们可能漏检人脸，误读异常光照或肤色，在侧脸或遮挡时失败，并在肤色物体上产生误报。

## 导出限制

CSV、ZIP 和文件夹导出作为带进度和过期检测的本地后台任务运行。可选 XMP sidecar（`include_xmp`，默认关）只写在项目导出目录下：文件夹拷贝旁以及 ZIP 成员。CSV 会存储该标志但不写 `.xmp` 文件。sidecar 永不写入 `originals/`、相机原片旁，或图像字节。这不是经过测试的 Lightroom/Capture One GUI 往返。文件夹导出暴露本地输出路径，而不是浏览器下载产物。导出的文件和 ZIP 是生成产物，不得提交到版本库。

ZIP 和文件夹导出要求所选源文件解析到项目 `originals/` 目录内部。这是针对损坏元数据的纵深防御；同时也意味着，如果本地已复制原图缺失或不再解析到项目存储内部，文件导出可能失败。

## 文件系统与路径假设

项目存储在本地项目目录中。v2.0 将导入的原图复制到项目存储，将衍生件和导出分开写入，并防止资源/导出路径逃逸出项目根目录。它不会自动重新扫描外部源文件夹、跟踪可移动驱动器生命周期，或管理网络共享一致性。

## SQLite 假设

应用假定单用户本地 SQLite 访问。它不是为多用户并发编辑、共享远程数据库或分布式项目状态设计的。应用启用 SQLite WAL，并为导入与处理期间的本地读/写并发设置有界 busy timeout；这仍然是单进程本地调优选择，而不是多用户数据库支持。

## 不支持的场景

v2.0 不支持云图库、共享团队项目、自动删除原图、远程 AI 处理、大型捆绑 AI 模型、在线画廊、作为 Lightroom 替代的编辑，或移动优先工作流。

## Desktop 2.1

可安装桌面应用（`2.1.0-desktop`）共用同一套本地 API 与筛选 UI，并带有额外壳层约束：

- 导入与处理任务在 sidecar 被杀或应用退出后**默认持久**：残留的导入/处理任务会标为 `interrupted`，并在下次启动时回收。设置 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` 可退回旧行为，把过期任务标为失败以便用户重试（无论哪种方式，导出仍失败并清理）。
- HEIC/HEIF 静帧以及带内嵌预览的 RAW 可本地导入（与 web 应用相同）。没有预览的 RAW 以本地提示跳过。
- **检查更新**仅在 Help 菜单（启动时不联网）。它查询 GitHub Releases，不下载、不安装。清单缺失为非致命 no-op。未签名构建仍可启动。用户仍需手动安装新构建。
- CI 已**签名就绪**：完整 GitHub Actions secret 集在场时会做 Authenticode / Developer ID + 公证。缺少 secrets 时保持**未签名**上传绿灯。见 [桌面代码签名手册](desktop_signing.zh.md)。
- 桌面计划里的 2.2 残留已由第九阶段交付（托盘 S9.06、独立预览 S9.07、导入 worker S9.08、数据目录 S9.09、检查更新 S9.10），除 cache 旋钮、自动下载安装和 macOS GUI pass。不声称双平台安装包 GUI DoD。
- **包装 macOS DMG GUI 生命周期为 skip，不是 pass**（S9.12，[#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)，`2026-09-05T12:31:10Z`）。开发主机是 Linux/WSL2（`uname -s` 不是 Darwin）；未挂载或启动 DMG。skip 不是 macOS pass。Windows NSIS GUI 生命周期记在 [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)（仅 Windows）。见 [桌面测试矩阵](desktop_testing.zh.md)。
- **WSL 可能无法运行 GUI**（需要 rustc ≥1.88 与显示）；HTTP/API 冒烟仍可用。见 [桌面测试矩阵](desktop_testing.zh.md)。
- 存储为**仅复制模式**（不支持相机卡原地引用）。
- 桌面**独立预览**（View → Detached preview，或筛选工具栏）打开第二个 WebView，显示当前筛选照片并共享选中。裸筛选键只作用于聚焦窗口。创建失败为非致命，并保持壳内预览。关闭预览窗不会退出应用。未添加额外的 `fs:` / `shell:` capabilities。
- 导入衍生 worker 默认 **1**。设置可将下一次导入作业升到 **2–4**（`GET`/`PATCH /api/settings`，`{data_dir}/app_settings.json`）。处理仍是每个项目一个作业。没有处理 worker 池、Redis 或 Celery。
- 桌面 **Change data directory** 把当前应用数据目录拷贝到已通过 D2.00 授权的空文件夹，并改写前缀为旧 data dir 的已存路径。旧树不删除。相机卡和其他源文件夹不移动、不修改。`FRAMEPILOT_DATA_DIR` 仍优先于 `{anchor}/data_dir.json`。未添加额外的 `fs:` / `shell:` capabilities。
- 可选**系统托盘**（D3.06）在 tooltip 中显示作业进度。**Show** 恢复主窗口；**Quit** 走与 File → Quit 同一套进行中作业对话框。关窗口仍是退出，不是藏到托盘。无头或部分 Linux 桌面创建托盘可能失败，且为非致命。未添加与托盘相关的 `fs:` / `shell:` capabilities。

终端用户步骤见 [桌面用户指南](desktop_user_guide.zh.md)。
