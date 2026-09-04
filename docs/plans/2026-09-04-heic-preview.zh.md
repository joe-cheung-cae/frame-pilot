# 第八阶段实现计划 — HEIC 预览（2026-09-04）

> 语言：[English](2026-09-04-heic-preview.md) | **中文**

**总议题：** [#150](https://github.com/joe-cheung-cae/frame-pilot/issues/150)  
**本关：** [#151](https://github.com/joe-cheung-cae/frame-pilot/issues/151) — 实现 H8.01–H8.06（RAW、AVIF、XMP、签名不在完成定义内）  
**相关：** `develop_plan.zh.md` §1.1、§7、§10.5、§16.7；`apps/api/app/services/importing.py`（`SUPPORTED_EXTENSIONS`、`PLANNED_HEIC_EXTENSIONS`）；`docs/v2_known_limitations.zh.md` 延期格式

Goal Mode：一次只做一个 task id。当前任务未实现、测试、评审并提交之前，不要开始下一个。

---

## 1. 为什么做这一刀

JPEG/PNG/WebP 精选、桌面 RC、持久作业和处理取消已在 `main`。包装 Windows GUI 生命周期 QA（[#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)）已按 Windows-only 关闭。

下一个用户能看见的缺口是 **iPhone 静帧**：导入现在会跳过 `.heic` / `.heif`，文案是 “HEIC files are not supported yet”。`develop_plan` §7 已写明处理架构稳定后再做 HEIC。

这一刀在**本地**把 HEIC/HEIF 解进现有衍生件/评分管道。这是**预览支持**，不是 RAW 显影，不是 XMP，也不是签名商店发行。

---

## 2. 锁定的决定

1. **只做本地。** 不云端解码、不登录、不支付、不捆绑神经网络模型、不把大文件提交进 git。
2. **解码器：** 加 `pillow-heif`，在 API 启动时调用一次 `register_heif_opener()`，让现有 `Image.open` / `ImageOps.exif_transpose` / `.convert("RGB")` 路径可用。**不要**只解析「容器里的 JPEG 预览」——常见 iPhone HEIC 是 HEVC，不是盒子里的 JPEG。
3. **拷贝原文件字节。** HEIC/HEIF 按与 JPEG 相同的规则进入 `{root_path}/originals/`，内容不变。缩略图和预览仍是 **WebP**。永不修改或删除源文件。
4. **在解码后的 RGB 上评分和分组**，与 JPEG 相同。不要另起一套 HEIC 评分栈。
5. **只要主图。** pillow-heif 报多图时用 primary。不导入 Live Photo 的 `.mov` 附件。`.mov` 仍不支持。
6. **HDR / gain map：** 解码 pillow-heif 给出的主图 RGB。本切片不做 gain-map 色调映射。写进限制说明。
7. **RAW 继续跳过**（`.arw`、`.cr3`、`.dng`、`.nef`），沿用现有明确原因。这里不提取 RAW 预览。
8. **AVIF 不在范围。** 即使插件能打开 AVIF，也不得把 `.avif` 加进 `SUPPORTED_EXTENSIONS`。
9. **导出拷贝原始 HEIC**，不要转成 JPEG。把 `.heic` / `.heif` 加进 `STORED_IMAGE_EXTENSIONS`，ZIP 用 `ZIP_STORED`（已经压缩过）。文件一旦在 `originals/` 里，CSV/文件夹/ZIP 本来就会拷 `project_copy_path`。
10. **不写 XMP**（[#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117) 保持 `not_planned`）。
11. **测试在进程内用 pillow-heif 生成小 HEIC。** 不要提交相机 HEIC。垃圾 `.heic` 字节走坏 JPEG 那条路（拷贝后该照片失败），不再走旧的「不支持扩展名」跳过。
12. **打包：** PyInstaller 必须收集 `pillow_heif` 及其自带的 libheif 二进制。只打未签名 NSIS/DMG。不签名。不升 `APP_VERSION`。
13. **许可证：** `pillow-heif` 为 BSD-3-Clause；wheel 里带 **LGPL** 的 `libheif`（及编码器）。写进已知限制 / 本计划。不要把 libheif 源码塞进 MIT 树。
14. **活文档双语**；代码、注释、测试、提交说明用英文。
15. **不做：** 导出作业取消、J7.07 暂停、D3.06 托盘、自动更新、桌面 2.2、默认 CI 的 500/1000/2000 真浏览器、`:large` GUI RSS。

---

## 3. 状态板

第八阶段 — HEIC 预览（#144 之后）

- [x] H8.01 pillow-heif 依赖与 opener 注册
- [x] H8.02 导入接受 `.heic` / `.heif`
- [ ] H8.03 处理并导出原始 HEIC
- [ ] H8.04 Web 导入 accept 与文案
- [ ] H8.05 冻结 sidecar 收集 pillow-heif
- [ ] H8.06 文档收口

---

## 4. 文件地图

| 路径 | 新建 / 修改 | 任务 |
| ---- | ------------- | ----- |
| `apps/api/pyproject.toml` | 加 `pillow-heif`；仅在插件要求时升 Pillow | H8.01 |
| `apps/api/app/image/heif_support.py` | 新建：可重复调用的 `ensure_heif_opener()` | H8.01 |
| `apps/api/app/main.py` | `create_app` 里调用 `ensure_heif_opener()` | H8.01 |
| `apps/api/app/services/importing.py` | 注册 opener；把 HEIC 扩展名移入 `SUPPORTED_EXTENSIONS` | H8.01–H8.02 |
| `apps/api/app/services/exporting.py` | `STORED_IMAGE_EXTENSIONS` 增加 `.heic`、`.heif` | H8.03 |
| `apps/api/tests/test_import_process_export_api.py` | 反转 HEIC 跳过；加解码/导出 | H8.02–H8.03 |
| `apps/api/tests/test_import_from_paths.py` | 反转 `shot.heic` 跳过 | H8.02 |
| `apps/api/tests/test_import_path_expansion.py` | 反转 `shot.heic` 跳过 | H8.02 |
| `apps/api/tests/test_path_import_process_export_workflow.py` | HEIC 原片走完处理+导出 | H8.03 |
| `apps/web/src/components/ImportPanel.tsx`（+ 测试） | `accept` 包含 HEIC | H8.04 |
| `packaging/pyinstaller/framepilot-api.spec`（必要时 hook） | hiddenimports + 原生库 | H8.05 |
| `scripts/sidecar-smoke.sh` 或打包测试 | 冻结解码冒烟 | H8.05 |
| `docs/api.md`、`docs/architecture.md`、`docs/v2_known_limitations.md`、`README.md`、`docs/desktop_user_guide.md`（+ 中文） | 格式说明 | H8.06 |
| `CHANGELOG.md`（+ 中文） | Unreleased 第八阶段 | H8.06 |
| 本计划（+ 英文） | 每完成一个任务勾 §3 | 各任务 |

---

## 5. 现有代码（不要回退）

| 行为 | 位置 |
| -------- | ----- |
| 拷贝前跳过 HEIC/HEIF | `is_supported_image` / `unsupported_image_reason` — “HEIC files are not supported yet…” |
| 跳过 RAW | 同一 helper — 保留 |
| 无 HEIF 插件的 `Image.open` | `importing.py` 衍生件/评分路径 |
| 导出拷贝 `originals/` 里任意文件 | `copy_selected_files` / `zip_selected_files`；`STORED_IMAGE_EXTENSIONS` 只决定 ZIP 压缩方式 |
| Web 文件选择器 | `ImportPanel.tsx` `accept="image/jpeg,image/png,image/webp"` |
| 冻结 sidecar | `packaging/pyinstaller/framepilot-api.spec` 只列了 JPEG/PNG/WebP 插件 |
| 断言跳过的测试 | `test_import_reports_heic_and_raw_as_planned_unsupported_formats`、path-expansion 的 `shot.heic` |

JPEG/PNG/WebP 导入、取消、回收和桌面退出必须保持绿色。

---

## 6. 任务规格

### H8.01 — pillow-heif 依赖与 opener 注册

**依赖：** 无

**契约：**

- 在 `apps/api/pyproject.toml` 运行时依赖中加入 `pillow-heif`。选带 CPython 3.11 manylinux / macOS / win_amd64 wheel 的版本。若该版本要求 Pillow 11，同一提交里升 `pillow`；否则保持 `pillow>=10.4.0`。
- 新建 `apps/api/app/image/heif_support.py`，提供 `ensure_heif_opener()`，内部调用 `pillow_heif.register_heif_opener()`，调用两次也安全。
- `create_app()` 调用它。`importing.py` 在模块导入时也调用（不经 `create_app` 的服务测试仍能解码）。
- **先不要**改 `SUPPORTED_EXTENSIONS`。HEIC 文件直到 H8.02 仍跳过。
- 测试辅助（仅测试模块）：用 pillow-heif 把小 RGB 图写成 HEIC 字节；`ensure_heif_opener()` 之后 `Image.open` 成功，`.convert("RGB")` 尺寸符合预期。
- 即使库提供 AVIF opener，也不要注册。

**H8.01 非目标：** 不改导入扩展名；无 UI；无 PyInstaller；无文档收口；无 RAW；不升 `APP_VERSION`。

**提交说明：** `feat: register pillow-heif opener for HEIC decode`

---

### H8.02 — 导入接受 `.heic` / `.heif`

**依赖：** H8.01

**契约：**

- 把 `.heic` 和 `.heif` 加进 `SUPPORTED_EXTENSIONS`。从 `PLANNED_HEIC_EXTENSIONS` 移除（若空则删掉该集合）。
- `unsupported_image_reason` 不再返回 HEIC 计划跳过字符串。RAW 字符串保留。
- 多部分 `/import` 和 `from-paths` 把有效的小 HEIC 拷进 `originals/`，写 WebP 缩略图+预览，有 EXIF 就提取，源文件 size/mtime/bytes 不变。
- 垃圾 `.heic`（`b"not-a-real-heic"`）**不是**「不支持的格式」。它是失败的导入项（与 `broken.jpg` 同类）：不要把整次作业打崩。
- 反转：
  - `test_import_reports_heic_and_raw_as_planned_unsupported_formats` — HEIC 导入；RAW 仍跳过；旧断言是没有 `originals/camera.heic`，现在有效夹具 HEIC 的拷贝**必须**存在。
  - `test_import_from_paths.py` / `test_import_path_expansion.py` 里的 `shot.heic` 用例。

**H8.02 非目标：** 无处理/导出工作流测试（H8.03）；无 web `accept`（H8.04）；无 PyInstaller（H8.05）；无活文档扫尾（H8.06）。

**提交说明：** `feat: import HEIC and HEIF stills`

---

### H8.03 — 处理并导出原始 HEIC

**依赖：** H8.02

**契约：**

- path-import 一张小 HEIC，`POST /process`，再对选中照片做 CSV + ZIP + 文件夹导出。
- 分组/排序可以是单张一组；够用。
- ZIP/文件夹载荷是**原始 HEIC 字节**，不是转 JPEG。`STORED_IMAGE_EXTENSIONS` 包含 `.heic` 和 `.heif`。
- 源 HEIC 在导入、处理、导出后 size/mtime/bytes 不变。
- 现有 JPEG 处理/导出测试保持绿色。

**H8.03 非目标：** 无 UI accept；无 PyInstaller；无文档扫尾；无导出作业取消。

**提交说明：** `feat: process and export original HEIC`

---

### H8.04 — Web 导入 accept 与文案

**依赖：** H8.02（可在 H8.03 之后落地）

**契约：**

- `ImportPanel.tsx` 文件输入的 `accept` 在 JPEG/PNG/WebP 之外包含 HEIC（`image/heic`、`image/heif`、`.heic`、`.heif`）。
- 导入面板或空状态里任何「只支持 JPEG、PNG 和 WebP」的用户可见文案，若与 HEIC 支持矛盾则改掉。RAW 仍标明不支持。
- `ImportPanel.test.tsx` 覆盖 accept 字符串（或等价断言）。
- 除非桌面原生文件夹选择器在 TS 里硬过滤扩展名，否则不要改它（path-import 走 API 列表）。

**H8.04 非目标：** 不改 API 行为；无 PyInstaller；除 UI 字符串外无文档扫尾。

**提交说明：** `feat: accept HEIC in the import panel`

---

### H8.05 — 冻结 sidecar 收集 pillow-heif

**依赖：** H8.01（若导入测试已证明能解码，可在 H8.02 之后开始）

**契约：**

- `framepilot-api.spec`（若 PyInstaller 不会自动收集则加 hook）包含 `pillow_heif` hiddenimports 以及 wheel 自带的原生库（`libheif` 和编解码 DLL/so/dylib）。
- 保留现有 JPEG/PNG/WebP Pillow 插件。不要砍 scipy。
- 冻结 sidecar 冒烟仍 unset `PYTHONPATH`。加解码检查：冻结环境能 `ensure_heif_opener()` + `Image.open` 生成的小 HEIC，**或**经冻结二进制的等价导入。`/health` 仍是最低门槛。
- 安装包体积：pillow-heif wheel 相对 scipy/numpy 很小。保持在已记录的 **400 MB 未打包** D4.06 阈值以下；不要把多出来的原生库当成该卸编解码器的信号。
- 不签名。不以包装 NSIS/DMG GUI 作为本任务完成定义。

**H8.05 非目标：** 无文档扫尾；不升 `APP_VERSION`；desktop.yml 不加签名密钥。

**提交说明：** `packaging: collect pillow-heif in the frozen sidecar`

---

### H8.06 — 文档收口

**依赖：** H8.02–H8.05 已落地（或作为同分支最后一笔）

**契约：** 双语页面与线上行为一致。不要声称 RAW、AVIF、HDR 色调映射、XMP 或已签名构建。

文件：

- `README.md` + `README.zh.md`
- `docs/api.md` + `docs/api.zh.md`
- `docs/architecture.md` + `docs/architecture.zh.md`
- `docs/v2_known_limitations.md` + `docs/v2_known_limitations.zh.md`
- `docs/desktop_user_guide.md` + `docs/desktop_user_guide.zh.md`（格式 / 导入）
- `CHANGELOG.md` + `CHANGELOG.zh.md` — Unreleased `### Phase 8 — HEIC preview` / `### 第八阶段 — HEIC 预览`
- 本计划 + 英文 — 只在**实现提交**里勾 §3 和 §7

各文件：

- **README / 已知限制：** HEIC/HEIF 静帧本地导入；RAW 仍跳过；原片不变；衍生件是 WebP；无 XMP。
- **api / architecture：** 导入列表含 HEIC/HEIF；经 pillow-heif 解码；导出原始字节。
- **CHANGELOG：** 本地 HEIC 预览；RAW 仍延期；无版本号提升、签名或 XMP。

若本指针 PR 已把第八阶段写成下一步，实现提交里**不要**再改 `develop_plan.md`（避免指针打架）。第八阶段合入后再用后续指针 PR 标成已交付。

**H8.06 非目标：** 无生产代码；若实现任务仍开着，不要用文档提交的 `Fixes` 关总议题。

**提交说明：** `docs: close out Phase 8 HEIC preview`

---

## 7. 第八阶段完成定义

- [ ] 有效 `.heic` / `.heif` 静帧能导入、拷进 `originals/`、并得到 WebP 缩略图/预览
- [ ] 源 HEIC 字节/mtime 在导入、处理、导出过程中不变
- [ ] 评分/分组/排序跑在解码后的 RGB 上，不另起管道
- [ ] ZIP/文件夹导出带上原始 HEIC；CSV 列出它
- [ ] 垃圾 HEIC 只让该文件失败，不打崩作业
- [ ] RAW 扩展名仍按现有原因跳过
- [ ] Web 导入 accept 包含 HEIC
- [ ] 冻结 sidecar 能解码 HEIC（插件 + 原生库已收集）
- [ ] 双语文档一致；CHANGELOG Unreleased 有第八阶段
- [ ] `npm run test:api`、`npm run test:web` 和 `npm run verify` 绿色
- [ ] 不升 `APP_VERSION`、不签名、不写 XMP、不做 RAW 预览、不做 AVIF、不做 J7.07

---

## 8. 验证命令

```bash
npm run test:api
npm run lint:api
npm run test:web
npm run typecheck
npm run verify
```

迭代时定向：

```bash
.venv/bin/pytest apps/api/tests/test_import_process_export_api.py apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_path_expansion.py -q -k 'heic or HEIC or heif'
npm run test:web
```

不签名。不要把未签名当成已签名。不要重开 #117 或 D3.06。

---

## 9. 明确非目标

- RAW 内嵌预览（DNG/ARW/CR3/NEF）
- AVIF
- 写 XMP sidecar
- HDR gain-map 显示
- Live Photo 视频
- 导出作业取消 / 导出回收
- J7.07 暂停/恢复
- 签名 / 商店发行 / 升 `APP_VERSION`
- D3.06 托盘、自动更新、桌面 2.2
- 提交相机 HEIC 或 libheif 源码

---

## 10. 工作流执行

H8.01–H8.06 每个任务是**独立**工作流（工作流不能再启动工作流）。那些工作流里不要实现 RAW 或 XMP。
