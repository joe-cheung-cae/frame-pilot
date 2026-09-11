# 残留：无内嵌预览时的 RAW 回退显影（2026-09-11）

> 语言：[English](2026-09-11-leftover-raw-develop.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)。S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) 已交付，只走 `extract_thumb`。不要把 #162 当未完成重开。本残留是：**没有内嵌预览时**回退 LibRaw `postprocess`。FramePilot 不是 RAW 编辑器。不要发明第十阶段 / S10 / 2.3。

**分支：** `feature/leftover-raw-develop`（从 `origin/main`）。提交不要切到 `main`。不要合并进 `main`。不要 squash。不要 force-push。实现者不合并。

**相关：** `develop_plan.md` §1.1；[docs/desktop_development_plan.md](../desktop_development_plan.zh.md) §5.6 / §10；[docs/v2_known_limitations.md](../v2_known_limitations.zh.md) 延后的格式；[docs/api.md](../api.zh.md) RAW 段；`apps/api/app/image/raw_preview.py`；`apps/api/app/services/importing.py`。

需求拆解 只写文档合同。评审 已按现行 RAW 导入路径修正规格漏洞。本次 归档 提交只记录 开发 交接。不要实现生产 Python。不要勾 开发 或 上线。不要声称色彩管理 RAW。不要发明第十阶段 / S10 / 2.3。

---

## 1. 为什么是残留，不是第十阶段

第九阶段 remaining-stretch 已关闭。S9.04 原样拷贝 RAW 字节，并抽取内嵌 JPEG/位图预览。没有 thumb 的文件以 `RAW file has no embedded preview; FramePilot does not demosaic` 跳过，不会拷进 `originals/`。

真实 DNG/ARW/CR3/NEF 里有的没有可用内嵌预览。精选仍需要一张 RGB 静帧。这是 S9.04 的残留，不是新产品阶段。

本残留只在 `extract_thumb` 失败时做**回退 demosaic**。它不把 FramePilot 变成 RAW 编辑器、色彩管理显影管线，或第十阶段。

**不要**发明第十阶段 / S10 / 2.3。产品字符串仍是 `2.1.0-desktop`。不改 `APP_VERSION`。不签名。不声称 SmartScreen 干净或商店上架。

---

## 2. 锁定决策

1. **本地优先。** 无云上传、登录、支付、遥测或捆绑神经网络模型。
2. **不是 RAW 编辑器。** 无曝光 / 白平衡 UI。无色彩管理管线。无额外扩展名（`.cr2`、`.raf`、`.orf`、`.rw2`）。只保留 `.dng`、`.arw`、`.cr3`、`.nef`。
3. **原片不变。** 永不修改或删除相机文件。只拷进 `{project}/originals/`。WebP 衍生件另写。
4. **`extract_raw_preview_image` 仍只抽 thumb。** 绝不能调用 `postprocess`。对**有**预览的文件，保持 `test_extract_raw_preview_does_not_call_postprocess` 为绿。
5. **新增 `open_raw_import_image`（或等价名）。** 先 `extract_thumb`。仅当 thumb 失败才 `postprocess`。优先同一 `rawpy.imread` 句柄。双路径失败仍抛 `RawPreviewError`，以便 `importing.py` 的 `except RawPreviewError` 继续工作。`RAW_NO_PREVIEW_REASON` **只**留给 `extract_raw_preview_image`。
6. **锁定的 `postprocess` kwargs（评审未收紧）：** `use_camera_wb=True`、`no_auto_bright=True`、`output_bps=8`、`half_size=True`。已在 `tiny_dng_without_preview_bytes()` 上用 rawpy 0.27.1 确认：RGB `uint8` 16×12（32×24 CFA 的 `half_size`）。不得加编辑器控件。必须在 `with rawpy.imread` **内部**对拷贝后的数组 `Image.fromarray`（关闭后 numpy 缓冲无效）。
7. **`expand_import_paths` 内永不 `postprocess`。** 文件夹遍历是同步 HTTP。RAW 扩展名只按后缀收集——也不做 `extract_thumb` 探测。HTTP 多部分与 from-paths 走 `register_import_file`，**不是** `import_image_file`（后者只被一个分块读取测试使用）。`_open_imported_image` 必须调用 `open_raw_import_image`，这样 `process_registered_import_photo`、`ensure_photo_derivatives`、`import_image_file` 才能显影无预览文件。
8. **thumb 与 `postprocess` 都失败时的跳过原因：** `RAW file could not be developed; no embedded preview and demosaic failed`。第一个「跳过且不留拷贝」闸门是 `register_import_file`（以及若被调用的 `import_image_file`）：先拷再打开，`RawPreviewError` 时在插入 Photo **之前** `_cleanup_paths(source_path)`。现行 `process_registered_import_photo` 只删缩略图/预览；`_mark_import_photo_failed` 会留下 originals + failed Photo。**不要**把衍生作业当成第一个双路径失败闸门，除非开发同时删除 originals 且不留 Photo/字节。`unsupported_image_reason` 不得承载此字符串（其 RAW 分支是死代码：RAW 已在 `SUPPORTED_EXTENSIONS`）。
9. **测试：** 已有 `tiny_dng_without_preview_bytes()` 构造无 JPEG 预览的 CFA。把它当**正向**回退夹具。垃圾字节两条路径都失败。不要提交相机 RAW。回退 RGB 没有 JPEG EXIF（`_extract_metadata` 为空）；不要要求 `capture_time` / `camera_model`，也不要加 DNG 标签读取器。
10. **一个草稿 PR。** 标题：`feat: leftover RAW fallback demosaic (no embedded preview)`。正文必须写 `Refs #202`。不得写 Fixes 或 Close。实现者不合并。已有草稿：[#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203)。
11. **不改 `APP_VERSION`。** 产品字符串仍是 `2.1.0-desktop`。不打包 NSIS/DMG，不调度 `desktop.yml`，不碰托盘 / D3.06 / #41。
12. **PyInstaller：** `packaging/pyinstaller/framepilot-api.spec` 已列出 `rawpy`、`_rawpy`、`numpy`，以及 `collect_submodules("rawpy")`。`packaging/pyinstaller/hooks/hook-rawpy.py` 已 `collect_all` + `collect_dynamic_libs`。评审确认**不需要额外 hiddenimports**。不要加模型。

---

## 3. 状态板

残留：无内嵌预览时的 RAW 回退显影

- [x] 需求拆解 — 中英残留计划 + GitHub issue [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)
- [x] 评审 — 对照现行 RAW 导入路径做对抗审阅
- [x] 归档 — 已记录 开发 交接（本次提交）；开发 保持 `[ ]`
- [x] 开发 — 测试先行；`open_raw_import_image` 先 thumb 再 postprocess；反转跳过测试；同一提交勾残留计划 开发 `[x]`（**不要**勾 上线）
- [ ] 测试 — 点名 pytest + `lint:api`；无相机文件
- [ ] 上线 — 活文档 + issue 评论；**不要**合并；**不要**发明第十阶段

本次 归档 提交只勾 **归档**。开发 保持 `[ ]`。不要勾 上线。不要声称色彩管理 RAW。

---

## 4. 勾选规则

| 时机 | 勾选 | 不要勾 |
| ---- | ---- | ----------- |
| 需求拆解 | 残留板 需求拆解 | 开发；上线；§2.2；第十阶段 |
| 评审 + 归档 | 残留板 评审 + 归档 | 开发；上线 |
| 开发 + 点名 pytest 绿 | 残留板 开发 + 测试 | 上线；色彩管理 RAW；额外扩展名；商店上架 |
| 本分支上线文档 | 残留板 上线；§1.1 点名本残留 | 合并进 `main`；重勾 §2.2；第十阶段；SmartScreen 干净 |

---

## 5. 文件地图

| 文件 | 角色 |
| ---- | ---- |
| `apps/api/app/image/raw_preview.py` | `extract_raw_preview_image` 仍只抽 thumb。新增 `open_raw_import_image`（先 thumb，再锁定 `postprocess`）。双路径失败时用新跳过原因常量挂在 `RawPreviewError` 上。在 rawpy 上下文内拷贝 RGB。 |
| `apps/api/app/services/importing.py` | `expand_import_paths`：按后缀收集 RAW；**不要** `extract_thumb` / `postprocess` 探测。`register_import_file` 仍是跳过且不留拷贝的闸门（拷后 `open_raw_import_image`；插入 Photo 前删 `originals/`）。`_open_imported_image` → `open_raw_import_image`（覆盖 `process_registered_import_photo`、`ensure_photo_derivatives`、`import_image_file`）。不要把 `unsupported_image_reason` 改成新字符串。 |
| `apps/api/tests/raw_helpers.py` | 复用 `tiny_dng_without_preview_bytes()`。不要加相机文件。 |
| `apps/api/tests/test_raw_preview.py` | 保留 `extract_raw_preview_image` 只抽 thumb 的断言。为 `open_raw_import_image` 补测试：无预览 CFA 返回 RGB；有预览文件仍永不 `postprocess`；垃圾字节抛双路径失败原因。 |
| `apps/api/tests/test_import_path_expansion.py` | 反转 expand：按后缀收集；expand 时不因缺 thumb 跳过。 |
| `apps/api/tests/test_import_from_paths.py` | 路径导入对无预览 CFA 显影；垃圾字节仍以新原因跳过；`originals/` 无残余字节。反转 `test_import_from_paths_accepts_avif_and_still_skips_raw` 的垃圾 `.dng` 原因。 |
| `apps/api/tests/test_import_process_export_api.py` | 多部分导入同样反转。有预览的 DNG 仍用 thumb RGB。反转 HEIC/AVIF「仍跳过 raw」垃圾 `.dng` 原因。 |
| [docs/api.md](../api.zh.md)（+ 英） | RAW 段：无内嵌预览时回退 demosaic；仍不是 RAW 编辑器。 |
| [docs/v2_known_limitations.md](../v2_known_limitations.zh.md)（+ 英） | 延后的格式：本残留 vs 色彩管理 / 额外扩展名仍未排期。 |
| `develop_plan.md` §1.1（+ 英） | **下一步**点名残留 #202。 |
| [docs/desktop_development_plan.md](../desktop_development_plan.zh.md) §5.6 / §10（+ 英） | 拆开回退 demosaic 残留 `[ ]` vs 色彩管理仍延后。 |
| `implement_goals.md`（+ 英） | 活指针指向 §1.1 本残留。不要发明第十阶段。 |
| `packaging/pyinstaller/framepilot-api.spec` + `hooks/hook-rawpy.py` | 评审：已收集 `rawpy` / `_rawpy` / 动态库。**不需要额外 hiddenimports。** 不要加模型。 |

现行树（`origin/main` `110eca7`，在 `feature/leftover-raw-develop` 上审阅）：

- `expand_import_paths` 调用 `extract_raw_preview_image`，`RawPreviewError` 时跳过（同步 HTTP 文件夹遍历）。
- HTTP 多部分与 from-paths 走 `register_import_file`（先拷再探测 `extract_raw_preview_image`；失败时在 Photo **之前**清理 `source_path`）。
- `import_image_file` 不是 HTTP 路由；一个测试使用它。它经 `_open_imported_image` 打开，`RawPreviewError` 时清理 `source_path`。
- `_open_imported_image` / `ensure_photo_derivatives` / `process_registered_import_photo` 只调用 `extract_raw_preview_image`。衍生作业失败路径**不会**删除 originals。
- `RAW_EXTENSIONS = {".arw", ".cr3", ".dng", ".nef"}`。`unsupported_image_reason` 的 RAW 分支返回 `RAW_NO_PREVIEW_REASON`，但是死代码（RAW 已在 `SUPPORTED_EXTENSIONS`）。
- `APP_VERSION` 为 `2.1.0-desktop`。

---

## 6. 测试反转表

| 测试（今日） | 今日 | 本残留之后 |
| ---- | ---- | ---- |
| `test_extract_raw_preview_does_not_call_postprocess` | **有**预览的文件：只 `extract_thumb` | 仍为绿。`extract_raw_preview_image` 永不 `postprocess`。对有预览文件的 `open_raw_import_image` 补同样断言。 |
| `test_extract_raw_preview_missing_thumb_raises` | `tiny_dng_without_preview_bytes()` → `RAW file has no embedded preview; FramePilot does not demosaic` | 对 `extract_raw_preview_image` 仍成立。`open_raw_import_image` 必须对该 CFA demosaic 并返回 RGB（正向夹具；评审：锁定 kwargs 成功，16×12 `uint8`）。不要把尺寸 == `TINY_DNG_PREVIEW_SIZE` 当成产品规则——那是 `half_size=True` 下的 CFA/2。 |
| `test_extract_raw_preview_garbage_bytes_raise` | 垃圾 `.dng` thumb 失败（`imread` 时 `LibRawIOError`） | `extract_raw_preview_image` 仍用无预览原因。`open_raw_import_image` / 导入跳过改用双路径失败原因。清理 `originals/`。 |
| `test_expand_includes_dng_with_preview_and_skips_without` | expand 跳过 `empty.dng` / `garbage.dng` | expand 收集所有 RAW 后缀（`frame.dng`、`empty.dng`、`garbage.dng`）。此处不 `extract_thumb` / `postprocess`。跳过发生在 register。 |
| `test_expand_nested_jpegs_and_skips` / `test_expand_includes_avif_and_still_skips_raw` | 垃圾 `.dng` 在 expand 以无预览原因跳过 | expand 按后缀收集 `.dng`。 |
| `test_import_dng_without_preview_is_skipped_without_copy` | 跳过 + 不拷 `originals/` | **反转：** 无预览 CFA 经回退导入；拷进 originals；不再跳过。此路径不要断言 EXIF capture_time/camera_model。 |
| `test_import_from_paths_accepts_dng_and_skips_no_preview` | `empty.dng` 被跳过 | 无 JPEG 预览的 CFA `empty.dng` 导入。源文件指纹不变。 |
| `test_import_accepts_dng_embedded_preview_and_skips_garbage_raw` | 有预览 DNG 导入；垃圾以无预览原因跳过 | 有预览 DNG 仍只用 thumb RGB。垃圾跳过改用双路径失败原因；`originals/` 无残余字节。 |
| `test_import_accepts_heic_and_still_skips_raw` / `test_import_accepts_avif_and_still_skips_raw` / `test_import_from_paths_accepts_avif_and_still_skips_raw` | 垃圾 `.dng` 以 `RAW_NO_PREVIEW_REASON` 跳过 | 仍跳过且不留拷贝；原因改为双路径失败字符串。 |
| 额外扩展名 | `.cr2` / `.raf` / `.orf` / `.rw2` 不受支持 | 不变。超出范围。 |

不要提交相机 RAW。测试阶段点名 pytest：`test_raw_preview.py`、`test_import_path_expansion.py`、`test_import_from_paths.py`、`test_import_process_export_api.py` 中的 RAW 用例，以及 `npm run lint:api`。

---

## 7. 非目标

- 第十阶段 / S10 / 2.3。
- RAW 编辑器：曝光、白平衡、色调曲线、色彩管理显影。
- 额外 RAW 扩展名：`.cr2`、`.raf`、`.orf`、`.rw2`。
- 在 `expand_import_paths` 内 `postprocess`。
- 从 `extract_raw_preview_image` 调用 `postprocess`。
- 自动下载安装、处理池、Redis/Celery。
- SmartScreen / 商店上架、托盘 / D3.06、`APP_VERSION` 提升。
- 打包 NSIS/DMG、调度 `desktop.yml`、签名、公证。
- 把相机照片、证书、模型权重提交进 git；云上传/登录/支付。
- 第二个 PR。合并进 `main`。本 PR 对残留 issue 写 Fixes/Close。

---

## 8. 评审发现（评审，2026-09-11）

对照 `feature/leftover-raw-develop` 现行树审阅（`65af8e0` 基于 `origin/main` `110eca7`）。确认：

1. **是残留，不是第十阶段。** `develop_plan.md` §1.1 **下一步**点名残留 [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)。桌面 §5.6 / §10 拆开回退 `[ ]` vs 色彩管理未排期。不要发明第十阶段 / S10 / 2.3。不要把 S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) 当未完成重开。
2. **`extract_raw_preview_image` 仍只抽 thumb。** 现行函数永不调用 `postprocess`。对**有**预览的文件保持 `test_extract_raw_preview_does_not_call_postprocess` 为绿。
3. **`expand_import_paths` 将不 `postprocess`。** 今日它在同步 HTTP 遍历里探测 `extract_raw_preview_image`。本残留之后只按后缀收集 RAW（也不做 thumb 探测）。
4. **跳过原因仅在两条路径都失败时改变。** `RAW_NO_PREVIEW_REASON` 仍是只抽 thumb 助手的文案。导入跳过字符串是 `RAW file could not be developed; no embedded preview and demosaic failed`。
5. **正向夹具：** `tiny_dng_without_preview_bytes()` 是无 JPEG 预览的 CFA。评审已跑锁定 kwargs：`extract_thumb` → `LibRawNoThumbnailError`；`postprocess` → RGB。垃圾 `b"not-a-real-raw"` 打开时 `LibRawIOError`（两条路径都失败）。不要提交相机 RAW。
6. **issue 编号与 GitHub 一致：** [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)。草稿 PR [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203) 已写 `Refs #202`（无 Fixes/Close）。
7. **§1.1 下一步点名本残留。** `implement_goals.md` 活指针也是。
8. **PyInstaller 已收集 `rawpy`。** spec hiddenimports + `hook-rawpy.py` 的 `collect_all` / `collect_dynamic_libs`。**不需要额外 hiddenimports。**

本提交修掉的漏洞（现行树让需求拆解规格不完整）：

1. HTTP 走 `register_import_file`，不是 `import_image_file`。衍生作业失败不会删除 `originals/`。register 仍是跳过且不留拷贝的闸门。
2. 测试反转表漏了 `test_import_accepts_heic_and_still_skips_raw`、`test_import_accepts_avif_and_still_skips_raw`、`test_import_from_paths_accepts_avif_and_still_skips_raw`。
3. 复用 `RawPreviewError`；在 rawpy 上下文内拷贝 RGB；回退 RGB 没有 JPEG EXIF。
4. `unsupported_image_reason` 不得变成新跳过原因。
5. 双重 demosaic（register 探测 + 随后 `_open_imported_image`）在 `half_size=True` 下可接受。不要加缓存或编辑器 UI。

非漏洞：kwargs 未收紧；额外扩展名仍排除；不改 `APP_VERSION`；开发 / 上线保持 `[ ]`。

---

## 9. 归档交接（归档，2026-09-11）

评审后的计划已锁定给 开发。状态：需求拆解 `[x]`，评审 `[x]`，归档 `[x]`。开发 仍是 `[ ]`（本分支还没有 `feat: demosaic RAW without embedded preview` 提交）。

**开发必须**在主题为 `feat: demosaic RAW without embedded preview` 的同一提交里：

1. **测试先行。** 按 §6 反转跳过测试。用 `tiny_dng_without_preview_bytes()` 作为无预览 CFA 的正向夹具。垃圾字节两条路径都失败。对**有**预览的文件保持 `test_extract_raw_preview_does_not_call_postprocess` 为绿。不要提交相机 RAW。
2. 新增 `open_raw_import_image`：先 `extract_thumb`，仅当 thumb 失败才走锁定 `postprocess`（`use_camera_wb=True`、`no_auto_bright=True`、`output_bps=8`、`half_size=True`）。`extract_raw_preview_image` 仍只抽 thumb，绝不能调用 `postprocess`。在 `with rawpy.imread` 内部拷贝 RGB。
3. 反转导入：`expand_import_paths` 按后缀收集 RAW（不做 `extract_thumb` / `postprocess` 探测）。`register_import_file` 仍是跳过且不留拷贝的闸门。`_open_imported_image` 调用 `open_raw_import_image`。双路径跳过原因：`RAW file could not be developed; no embedded preview and demosaic failed`。清理 `originals/` 拷贝；不留残余字节。
4. **同一提交**勾残留计划 开发 `[x]`（英+中）。
5. `git push -u origin HEAD`。不要开第二个 PR（草稿 PR 是 [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203)）。
6. **不要**勾 上线。**不要**声称色彩管理 RAW、额外扩展名（`.cr2` `.raf` `.orf` `.rw2`）或 RAW 编辑器。不改 `APP_VERSION`。不要发明第十阶段 / S10 / 2.3。不要把 S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) 当未完成重开。

本次 归档 提交不要实现生产 Python。以**本评审后的计划**（§2、§5、§6）为准。

指针：残留 [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)；草稿 PR [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203)；S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) 保持已交付、只走 `extract_thumb`。
