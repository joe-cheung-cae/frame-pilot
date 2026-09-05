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
6. **AVIF：** 用 HEIC 的 `pillow-heif` opener 加入 `.avif`。测试里进程内生成小文件。不是 RAW。
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
- [ ] S9.01 导出作业取消 — [#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164)
- [ ] S9.02 J7.07 处理暂停/恢复 — [#161](https://github.com/joe-cheung-cae/frame-pilot/issues/161)
- [ ] S9.03 AVIF 静帧预览 — [#163](https://github.com/joe-cheung-cae/frame-pilot/issues/163)
- [ ] S9.04 RAW 内嵌预览 — [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162)
- [ ] S9.05 XMP sidecar 导出 — [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165)（历史 [#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117)）
- [ ] S9.06 可选系统托盘（D3.06） — [#169](https://github.com/joe-cheung-cae/frame-pilot/issues/169)
- [ ] S9.07 独立预览窗口 — [#166](https://github.com/joe-cheung-cae/frame-pilot/issues/166)
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

**文件：** `apps/api/app/api/routes.py` `cancel_job_endpoint`；导出/作业服务；导出循环检查点；把 `apps/api/tests/test_import_process_export_api.py` 里导出 422 倒过来；若有进行中的导出，桌面退出可取消。

**测试先行：** 排队/运行中的导出取消 → 202 + 标志；终态 → 200 no-op；不完整产物删除；原片未动；导入/处理取消仍绿。

**非目标：** S9.02–S9.13；导出持久恢复；`APP_VERSION`；签名。

### S9.02 — J7.07 暂停

**文件：** `apps/api/app/services/processing.py`；`ProcessingPanel`；如需暂停标志列则改作业 schema；勾选第七阶段计划。

**测试先行：** 运行中处理暂停会持久化标志且不标 `cancelled`；分组不可审阅；恢复路径是 reset 后的 `POST /process`；取消测试仍绿。

**非目标：** 原地从半批次哈希继续；导出暂停。

### S9.03 — AVIF

比照 HEIC：`SUPPORTED_EXTENSIONS`、`STORED_IMAGE_EXTENSIONS`、ImportPanel `accept`、PyInstaller collect、pytest 里生成小 AVIF。

**非目标：** RAW、XMP、gain-map HDR。

### S9.04 — RAW 内嵌预览

当存在 thumb 时，`.arw/.cr3/.dng/.nef` 不再无条件跳过。拷贝原片；抽 thumb；WebP 衍生件。无 thumb 时带原因跳过。

**非目标：** 完整 demosaic；XMP；把相机样张提交进 git。

### S9.05 — XMP

可选导出勾选，默认关。sidecar 只在导出目录。测试：原片字节不变；评分映射；启用时 ZIP 含 sidecar。

**非目标：** 写到 `originals/` 旁或相机卡上。

### S9.06 — 托盘

可选托盘 + 作业进度。不加新的 `fs:`/`shell:` 能力。勾选 D3.06。

### S9.07 — 独立预览

第二个 WebView + 共享选中。WebView 失败则退回壳内预览。

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

建议 `agent_budget`：32。
