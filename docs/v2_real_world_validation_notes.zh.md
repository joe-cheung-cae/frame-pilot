# FramePilot v2 真实世界算法验证笔记

> 语言：[English](v2_real_world_validation_notes.md) | **中文**

用本记录保存非私人 Openverse CC0/PDM 照片复核。不要把私人文件名、私人路径、敏感元数据或生成的项目产物粘贴进本文件。

## 数据集摘要

- 数据集名称：Openverse CC0/PDM portrait-query photograph set（脱敏本地别名）
- 复核者：Cursor cloud agent，代表 Joe（joe-cheung-cae）
- 日期：2026-08-17
- 隐私状态：从 Openverse 获取的已发布 CC0 或 Public Domain Mark 照片。仅使用本地别名（`portrait-001.jpg`、`headshot-001.webp`、`landscape-001.jpg` 及类似名称）。无私人未发表照片。本文件不含人名。
- 照片数：138
- 相机/来源：Openverse 图像搜索（`license=cc0,pdm`，`category=photograph`，`mature=false`），查询 portrait / headshot / studio / landscape / still-life，外加若干 related-image 跟进。主机多为 Flickr，以及 StockSnap、Rawpixel 和 Wikimedia。文件为 JPEG、PNG 或 WebP。
- 验证层级：B（100–300 张照片；人像为主，含风景/静物对照）
- FramePilot 提交哈希：`67e9c2d4cfd0047acf2bd56777117f6af2e50dbd`（被测代码；笔记稍后提交）
- 本地项目数据位置（若可安全记录）：未跟踪的 `.local-validation/`（已 gitignore；不是发布产物）
- 复核耗时：2026-08-17 的导入/处理/导出，加上手工分组、分数、解释、人脸信号和导出检查

## 已运行的命令

```bash
git status --short
npm run verify
```

其他命令：

```bash
# Untracked local download and API workflow (photos and project data stay gitignored)
.venv/bin/python .local-validation/download_openverse.py
.venv/bin/python .local-validation/run_validation.py
bash scripts/check-validation-decision.sh
npm run check:artifacts
```

现场工作流创建了一个项目，通过单个导入 `job_id` 分三批导入 138 个文件（每批最多 50，最后一批 finalize），处理该项目，应用 Pick/Maybe/Reject/Unreviewed 和星级覆盖，并导出 Pick 的 CSV、ZIP 和文件夹选择。

## 摘要结论

- 结论：pass with notes
- 一段摘要：FramePilot 导入、处理、分组、排序并导出了 138 张已发布的 CC0/PDM 照片，未修改原片，也未损坏导出。分组保守（137 组，一对合法的两帧棚拍，无已确认的错误合并）。排序和解释跟随技术分数，并在较弱的单图上保持保守。实验性人脸/睁眼启发式在本集上未能可靠检测人脸，并在非人脸图像上产生少量误报；这些不匹配被记录为实验性限制，不是 v2.0 阻断项。Openverse 的 “portrait” 搜索语义较宽，因此本集包含真人肖像，以及野生动物、历史锡版、微距，以及少量天文/风景帧。
- 发布决策影响：rc2 豁免已被本 Tier B 证据取代。无限定条件的 `v2.0.0` 标签仍要求在待打标签的提交上 `npm run check:pretag` 通过。不要声称专业人脸检测、RAW/HEIC 或 XMP 支持。
- 建议后续工作：保持人脸/睁眼用语为实验性。可选后续：许可清晰的摄影师连拍/场次集，以及 v2.0 之后可选的本地人脸模型。不要根据这一次复核重调分组/排序阈值。

## 数据集覆盖

标记本数据集覆盖的每个类别。

| 类别 | 已覆盖？ | 备注 |
| -------- | -------- | ----- |
| Burst sequences | no | 在不合成帧的前提下，CC0/PDM 下没有可用的相机连拍序列。 |
| Near-duplicate travel photos | partial | 同一人的两帧棚拍对（`portrait-006` / `portrait-007`）。不是旅行连拍。 |
| Landscape scenes | yes | 15 张 landscape-query 照片，以及其他无人脸场景。 |
| Portraits | yes | 真人棚拍/户外人像、历史团体锡版，以及 Openverse 打了 portrait 标签的野生动物/微距。 |
| Indoor low light | partial | 历史室内锡版和一些较暗棚拍帧；不是现代低 ISO 室内活动集。 |
| Underexposed images | yes | 近黑的天文/太空帧分数低，被标为 Maybe。 |
| Overexposed images | partial | 有明亮棚拍和高调帧；不是专门的过曝裁切集。 |
| Intentionally blurred images | partial | 柔和历史底片和浅景深人像；不是标注过的虚化测试。 |
| Repeated composition with small subject changes | yes | `portrait-006` / `portrait-007` 一对（同一主体，姿态/锐度小变化）。 |
| Mixed orientation images | yes | 横向和纵向，以及方形帧。 |
| Images with no faces | yes | 风景、静物、天文、行星表面、昆虫微距、野生动物。 |
| Images with multiple faces, non-private only | yes | 历史已发表家庭/棚拍锡版（公有领域）。 |
| Similar unrelated scenes that should not merge | yes | 相邻野生动物头部、不同人物的混合棚拍人像，以及 Openverse related 跟进保持分开。 |
| Metadata-light images | yes | 本集导入后没有 `capture_time` 值。分组使用哈希/embedding/文件名信号。 |

## 指标

| 指标 | 数值 | 备注 |
| ------ | ----- | ----- |
| Total photo count | 138 | 全部文件已导入；0 跳过；全部 `processing_state` 为 `processed`。 |
| Group count | 137 | |
| Singleton group count | 136 | |
| Multi-photo group count | 1 | 两张棚拍人像的重复组。 |
| False merge count | 0 | 唯一的多图组是同一人的两帧。 |
| Missed group count | 0 | 复核中未发现其他明确近重复对。缺少连拍覆盖，因此这不是连拍漏组计数。 |
| Ranking mismatch count | 0 | 在唯一的多图组内，更锐的帧为 Pick，更软的帧为 Maybe。单图 Pick 跟随高技术分数，包括非人类微距，这符合技术排序设计。 |
| Explanation mismatch count | 2 | 两张被启发式标记的非人脸图像上出现人脸/睁眼用语。 |
| Face-signal mismatch count | high | 3 false positives on non-face images；真人肖像上系统性漏报，包括三人历史团体照。仅实验性。 |
| Export issue count | 0 | CSV、ZIP 和文件夹 Pick 导出完成。 |
| UI workflow issue count | not applicable | 本次使用本地 API 加图像检查，不是计时的筛选 UI 会话。 |

## 分组结果

| Issue ID | 类别 | 组或照片 ID | 期望 | 实际 | 严重程度 | 后续 |
| -------- | -------- | ------------------ | -------- | ------ | -------- | --------- |
| RW-001 | false merge | none confirmed | 不相关的人/场景保持分开 | 137 组；只有 `portrait-006`/`portrait-007` 共享一组 | none | None |
| RW-002 | missed group | burst category | 真实连拍序列分到一起 | 没有可用的 CC0 连拍集 | dataset gap | 在 v2.0 之后收集许可清晰的场次/连拍集 |

## 排序结果

| Issue ID | Group ID | 手工选择 | FramePilot 选择 | 分数摘要备注 | 严重程度 | 后续 |
| -------- | -------- | ------------- | ----------------- | ------------------- | -------- | --------- |
| RW-003 | alias `portrait-006`/`portrait-007` | 两帧中更锐的一帧 | Pick on `portrait-006` (0.377), Maybe on `portrait-007` (0.320) | 分数差距 0.0575；解释引用 0.06 和较弱锐度 | none | None |

单图排序偏好技术锐度/曝光/对比度。本集最高总分是一张锐利的昆虫头部微距（`headshot-001.webp`，0.824，Pick）。这对混合 Openverse “portrait” 查询上的技术排序器是预期行为，不视为组内不匹配。

## 解释结果

| Issue ID | 照片或组 ID | 期望解释 | 实际解释 | 严重程度 | 后续 |
| -------- | ----------------- | -------------------- | ------------------ | -------- | --------- |
| RW-004 | `portrait-052.jpg`, `portrait-078.jpg` | 不要在非人脸场景上引用人脸/睁眼信号 | 误报标记后面，解释提到了实验性人脸和睁眼信号 | medium | 保持实验性标注；本次不改阈值 |

其他抽样解释与数字匹配：低分单图为 Maybe，并引用了数字分数；两帧组引用了 0.06 差距。

## 导出结果

- 检查的导出模式：CSV / ZIP / folder
- 导出的状态：Pick
- 导出项数：6
- 已检查输出：yes
- 存在敏感文件名：no（仅脱敏别名）
- 原始源文件未改变：yes（全部 138 个源文件的 SHA-256 在导入/导出前后匹配）
- 导出产物未进入 Git：yes

| Issue ID | 导出模式 | 期望 | 实际 | 严重程度 | 后续 |
| -------- | ----------- | -------- | ------ | -------- | --------- |
| RW-005 | CSV | Pick 行、UTF-8、分数与工作区匹配 | 6 Pick rows; CSV `score` matched displayed scores to 3 decimals | none | None |
| RW-006 | ZIP | 字节相同的 JPEG/WebP，stored 压缩 | 全部 6 个成员为 ZIP_STORED，且 SHA-256 与源文件相同 | none | None |
| RW-007 | folder | 项目导出目录下字节相同的副本 | 全部 6 份副本与源文件相同 | none | None |

手工覆盖在导出中可见：API 状态更新后，CSV 只包含 Pick 行。

## 问题日志

使用 `docs/v2_real_world_validation.zh.md` 中的类别。

| Issue ID | 类别 | 照片或组 ID | 期望 | 实际 | 严重程度 | 证据 | 可疑原因 | 阈值担忧？ | 需要测试？ | 后续 |
| -------- | -------- | ------------------ | -------- | ------ | -------- | -------- | --------------- | ------------------ | -------------- | --------- |
| RW-001 | false merge | n/a | 无不相关合并 | 未发现 | none | 137 组；对唯一一对做视觉检查 | 无拍摄时间时的保守分组 | no | no | None |
| RW-002 | missed group | burst category | 连拍成组 | 数据集不含连拍类别 | low | 覆盖表 | 没有许可清晰的连拍 | no | no | Optional later dataset |
| RW-003 | bad ranking | `portrait-006`/`007` | 推荐更锐的帧 | Pick on sharper frame | none | 分数 0.377 vs 0.320 | 技术排序 | no | no | None |
| RW-004 | misleading explanation | `portrait-052`, `portrait-078` | 非人脸上无人脸用语 | 出现人脸/睁眼用语 | medium | 解释加视觉复核 | 人脸启发式误报 | no | no | Keep experimental copy |
| RW-008 | face-signal mismatch | 真人肖像，包括 `portrait-025`、`studio-001` | 实验性启发式可能漏检人脸 | 几乎所有真人肖像 `face_presence=false` | medium | 2/83 portrait-query files flagged, and those two flags were non-faces | 肤色掩膜启发式限制 | no | no | Documented limitation |
| RW-009 | face-signal mismatch | `landscape-015`, `portrait-052`, `portrait-078` | 无人脸标记 | 风景 / 天文 / 行星表面帧上 `face_presence=true` | medium | 视觉复核 | 纹理/肤色区域上的误报 | no | no | Documented limitation |
| RW-010 | UI workflow issue | n/a | n/a | API-only pass | none | Validation runner | 不是 UI 会话 | no | no | Optional later UI pass |

## 发布决策

- 无关键数据安全问题：yes
- 无原始文件修改：yes
- 无严重导出损坏：yes
- 若适用，Tier B 中无频繁错误合并：yes
- 排序不匹配在诚实解释和用户覆盖下可接受：yes
- 人脸/睁眼启发式不匹配已记录为实验性：yes
- 发布前需要阈值或代码变更：no
- 最终发布决策：pass with notes。v2.0 现已有真实世界算法证据。保持人脸/睁眼信号为实验性。在文档提交上 `npm run check:pretag` 变绿之前不要打标签。

## 后续任务

| 优先级 | 任务 | 负责人 | 发布阻断？ |
| -------- | ---- | ----- | ----------------- |
| Medium | 保持 README.zh.md 和 `docs/scoring.zh.md` 明确：人脸/睁眼信号是实验性本地启发式 | maintainer | no |
| Low | 可选的许可清晰摄影师连拍/场次集，用于分组 | maintainer | no |
| Low | v2.0 之后可选本地人脸模型，不提交大权重 | maintainer | no |
| Low | 可选地在同一未跟踪集上做键盘筛选 UI 复核 | maintainer | no |
