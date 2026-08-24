# FramePilot v2.0 验证决策

> 语言：[English](v2_rc2_validation_decision.md) | **中文**

决策日期：2026-08-17。

发布负责人：Joe（joe-cheung-cae），验证笔记由 Cursor cloud agent 记录。

状态：completed。

本文件是真实世界算法置信度门槛的发布负责人决策记录。
2026-08-17 完成了一次 Tier B 非私人照片复核，并取代该门槛在 2026-06-05 的 rc2 豁免。

## 当前门槛

手工非私人真实世界算法验证记录在
`docs/v2_real_world_validation_notes.zh.md`。

协议仍然是：

- `docs/v2_real_world_validation.zh.md`
- `docs/v2_release_candidate_checklist.zh.md`

不要把私人照片、敏感文件名、生成的项目目录、导出、ZIP 文件、
trace、SQLite 数据库、缩略图、预览或本地缓存文件当作已跟踪的发布证据。

## 验证证据

验证笔记文件：docs/v2_real_world_validation_notes.zh.md。

验证层级：B。

数据集隐私状态：已发布的 CC0/PDM Openverse 照片，使用经过脱敏的本地别名。

摘要指标：

| 指标 | 数值 |
| ------ | ----- |
| 总照片数 | 138 |
| 组数 | 137 |
| 错误合并数 | 0 |
| 漏组数 | 0 |
| 排序不匹配数 | 0 |
| 解释不匹配数 | 2 |
| 导出问题数 | 0 |

验证结论：pass with notes。

发布决策影响：真实世界算法门槛现已有完成的 Tier B 证据。人脸/睁眼不匹配仍作为已记录的实验性限制。仅在待打标签的提交上 `npm run check:pretag` 通过后，才打 `v2.0.0` 标签。

## 豁免记录

豁免状态：已被验证证据取代。

历史 rc2 说明（2026-06-05）：Chao Zhang 豁免该门槛，使 `v2.0.0-rc2` 能在没有真实世界照片笔记的情况下作为工程预发布。该豁免仅作为历史保留。2026-08-17 的复核已在 v2.0 验收上取代它。

- 历史豁免负责人：Chao Zhang
- 历史豁免日期：2026-06-05
- 原因：rc2 在自动化加固后作为工程预发布；真实世界笔记被推迟。
- 当时接受的风险：真实照片集上的分组、排序、解释或人脸/睁眼问题可能未被看到。
- 后续任务：已由记录在 `docs/v2_real_world_validation_notes.zh.md` 的 2026-08-17 Openverse CC0/PDM 人像查询复核完成。

## 打标签前必须确认

- 待打标签的提交上 `npm run verify` 通过。
- 待打标签的提交上 `npm run check:artifacts` 通过。
- 待打标签的提交上 `npm run check:pretag` 通过。
- `git status --short` 只包含有意的发布变更。
- 未跟踪生成/私人照片、项目数据、导出、ZIP、trace、SQLite 数据库、缓存目录、virtualenv 或 `node_modules` 文件。
- README.zh.md 和发布文档不声称已实现 RAW、HEIC、XMP、云工作流、持久化任务或专业人脸/眼睛检测。
- 发布说明应链接 `docs/v2_real_world_validation_notes.zh.md` 和本决策文件。
