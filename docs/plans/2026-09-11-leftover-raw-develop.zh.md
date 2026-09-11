# 残留：无内嵌预览时的 RAW 回退显影（2026-09-11）

> 语言：[English](2026-09-11-leftover-raw-develop.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)。S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) 已交付，只走 `extract_thumb`。不要把 #162 当未完成重开。本残留是：**没有内嵌预览时**回退 LibRaw `postprocess`。FramePilot 不是 RAW 编辑器。不要发明第十阶段 / S10 / 2.3。

**分支：** `feature/leftover-raw-develop`（从 `origin/main`）。提交不要切到 `main`。不要合并进 `main`。不要 squash。不要 force-push。实现者不合并。

**相关：** `develop_plan.md` §1.1；[docs/desktop_development_plan.md](../desktop_development_plan.zh.md) §5.6 / §10；[docs/v2_known_limitations.md](../v2_known_limitations.zh.md) 延后的格式；[docs/api.md](../api.zh.md) RAW 段；`apps/api/app/image/raw_preview.py`；`apps/api/app/services/importing.py`。

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
5. **新增 `open_raw_import_image`（或等价名）。** 先 `extract_thumb`。仅当 thumb 失败才 `postprocess`。
6. **锁定的 `postprocess` kwargs：** `use_camera_wb=True`、`no_auto_bright=True`、`output_bps=8`、`half_size=True`。评审可以收紧；不得加编辑器控件。
7. **`expand_import_paths` 内永不 `postprocess`。** 该路径是同步 HTTP。RAW 扩展名按后缀收集。显影或跳过只发生在 `register_import_file` / `import_image_file` / 导入衍生作业（`_open_imported_image` / `ensure_photo_derivatives`）。
8. **thumb 与 `postprocess` 都失败时的跳过原因：** `RAW file could not be developed; no embedded preview and demosaic failed`。清理任何 `originals/` 拷贝。不留残余字节。
9. **测试：** 已有 `tiny_dng_without_preview_bytes()` 构造无 JPEG 预览的 CFA。使用它。垃圾字节两条路径都失败。不要提交相机 RAW。
10. **一个草稿 PR。** 标题：`feat: leftover RAW fallback demosaic (no embedded preview)`。正文必须写 `Refs #202`。不得写 Fixes 或 Close。实现者不合并。
11. **不改 `APP_VERSION`。** 不打包 NSIS/DMG，不调度 `desktop.yml`，不碰托盘 / D3.06 / #41。

---

## 3. 状态板

残留：无内嵌预览时的 RAW 回退显影

- [x] 需求拆解 — 中英残留计划 + GitHub issue [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)
- [ ] 评审 — 对照现行 RAW 导入路径做对抗审阅
- [ ] 归档 — 残留板可进入开发
- [ ] 开发 — `open_raw_import_image` 在 thumb 失败时回退 `postprocess`
- [ ] 测试 — 点名 pytest + `lint:api`；无相机文件
- [ ] 上线 — 活文档 + issue 评论；**不要**合并；**不要**发明第十阶段

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
| `apps/api/app/image/raw_preview.py` | `extract_raw_preview_image` 仍只抽 thumb。新增 `open_raw_import_image`（先 thumb，再锁定 `postprocess`）。两条路径都失败时用新跳过原因常量。 |
| `apps/api/app/services/importing.py` | `expand_import_paths`：按后缀收集 RAW；**不要** `extract_thumb` / `postprocess` 探测。`register_import_file`、`import_image_file`、`_open_imported_image`、`ensure_photo_derivatives`：经 `open_raw_import_image` 显影或跳过。双路径失败时清理 `originals/`。 |
| `apps/api/tests/raw_helpers.py` | 复用 `tiny_dng_without_preview_bytes()`。不要加相机文件。 |
| `apps/api/tests/test_raw_preview.py` | 保留只抽 thumb 的断言。为无预览 CFA vs 垃圾字节补回退显影测试。 |
| `apps/api/tests/test_import_path_expansion.py` | 反转 expand：按后缀收集；expand 时不因缺 thumb 跳过。 |
| `apps/api/tests/test_import_from_paths.py` | 路径导入对无预览 CFA 显影；垃圾字节仍以新原因跳过；`originals/` 无残余字节。 |
| `apps/api/tests/test_import_process_export_api.py` | 多部分导入同样反转。有预览的 DNG 仍用 thumb RGB。 |
| [docs/api.md](../api.zh.md)（+ 英） | RAW 段：无内嵌预览时回退 demosaic；仍不是 RAW 编辑器。 |
| [docs/v2_known_limitations.md](../v2_known_limitations.zh.md)（+ 英） | 延后的格式：本残留 vs 色彩管理 / 额外扩展名仍未排期。 |
| `develop_plan.md` §1.1（+ 英） | **下一步**点名残留 #202。 |
| [docs/desktop_development_plan.md](../desktop_development_plan.zh.md) §5.6 / §10（+ 英） | 拆开回退 demosaic 残留 `[ ]` vs 色彩管理仍延后。 |
| `implement_goals.md`（+ 英） | 活指针指向 §1.1 本残留。不要发明第十阶段。 |
| `packaging/pyinstaller/framepilot-api.spec` | 仅核验：S9.04 已收集 `rawpy`。不要加模型。 |

现行树（`origin/main` `110eca7`）：

- `expand_import_paths` 调用 `extract_raw_preview_image`，`RawPreviewError` 时跳过（同步 HTTP）。
- `register_import_file` 先拷再探测 `extract_raw_preview_image`；失败则清理。
- `_open_imported_image` / `import_image_file` / `ensure_photo_derivatives` 只调用 `extract_raw_preview_image`。
- `RAW_EXTENSIONS = {".arw", ".cr3", ".dng", ".nef"}`。

---

## 6. 测试反转表

| 测试（今日） | 今日 | 本残留之后 |
| ---- | ---- | ---- |
| `test_extract_raw_preview_does_not_call_postprocess` | **有**预览的文件：只 `extract_thumb` | 仍为绿。`extract_raw_preview_image` 永不 `postprocess`。 |
| `test_extract_raw_preview_missing_thumb_raises` | `tiny_dng_without_preview_bytes()` → `RAW file has no embedded preview; FramePilot does not demosaic` | 对 `extract_raw_preview_image` 仍成立。`open_raw_import_image` 必须对该 CFA demosaic 并返回 RGB。 |
| `test_extract_raw_preview_garbage_bytes_raise` | 垃圾 `.dng` thumb 失败 | 垃圾仍 thumb **与** `postprocess` 都失败。导入跳过 + 清理。 |
| `test_expand_includes_dng_with_preview_and_skips_without` | expand 跳过 `empty.dng` / `garbage.dng` | expand 收集所有 RAW 后缀。此处不 `postprocess`。跳过发生在后面。 |
| `test_expand_nested_jpegs_and_skips` / `test_expand_includes_avif_and_still_skips_raw` | 垃圾 `.dng` 在 expand 以无预览原因跳过 | expand 按后缀收集 `.dng`。 |
| `test_import_dng_without_preview_is_skipped_without_copy` | 跳过 + 不拷 `originals/` | 经回退导入/显影。若两条路径都失败：以 `RAW file could not be developed; no embedded preview and demosaic failed` 跳过；清理拷贝；不留残余字节。 |
| `test_import_from_paths_accepts_dng_and_skips_no_preview` | `empty.dng` 被跳过 | 无 JPEG 预览的 CFA `empty.dng` 若 demosaic 成功则导入。源文件指纹不变。 |
| `test_import_accepts_dng_embedded_preview_and_skips_garbage_raw` | 有预览 DNG 导入；垃圾跳过 | 有预览 DNG 仍只用 thumb RGB。垃圾跳过改用双路径失败原因。 |
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
