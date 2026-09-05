# 导出互操作性

> 语言：[English](export_interoperability.md) | **中文**

FramePilot v2.0 支持 CSV、ZIP 和文件夹导出。启用 `include_xmp` 时，可选的 XMP sidecar 只写在项目导出目录下。永不写到相机原片旁、`originals/` 内，或写入图像字节。

## 当前模式

- `csv`：写入本地 CSV 产物，包含所选照片、项目照片 id、来源身份字段（`original_path`、`project_copy_path`、`source_identity`、`content_hash`、大小和 mtime）、导入的拍摄与相机元数据、星级、状态、分数、组元数据、尺寸、处理状态/错误字段，以及推荐解释。`include_xmp` 会记在导出记录上；CSV **不写** `.xmp` 文件，因为 CSV 已含 `status` 和 `star_rating`。
- `zip`：写入包含所选项目内原始副本的本地 ZIP，重复文件名用确定性后缀保留。`include_xmp` 为 true 时加入匹配的 `{exported_filename}.xmp` 成员（XML 用 `ZIP_DEFLATED`；图像仍 `ZIP_STORED`）。
- `folder`：将所选项目内原始副本复制到本地导出文件夹，重复文件名用确定性后缀保留。`include_xmp` 为 true 时在每个拷贝旁写入 `{exported_filename}.xmp`。

当前所有导出都是项目 `exports/` 目录下的派生输出。它们不修改原始源文件。
ZIP 和文件夹导出要求所选本地项目副本存在。若所选副本缺失，导出会标记为失败，并在可能时删除部分输出。

## XMP Sidecar 映射

Sidecar 包是 UTF-8 RDF/XML，包装为 `x:xmpmeta` / `rdf:RDF` / `rdf:Description`。`xmp:Rating` 是限制在 `0`–`5` 的星级（Reject **不会**写成 `xmp:Rating = -1`）。`xmp:Label` 使用 Adobe 色标字符串，让 Pick/Maybe/Reject 可检查且不覆盖星级。`dc:subject` 重复 FramePilot 状态。`dc:title` 是导出文件名，`dc:identifier` 是项目照片 id。

| `user_status` | `xmp:Rating` | `xmp:Label` | `dc:subject` |
| -- | -- | -- | -- |
| Pick | 星级 0–5 | Green | Pick |
| Maybe | 星级 0–5 | Yellow | Maybe |
| Reject | 星级 0–5 | Red | Reject |
| Unreviewed | 星级 0–5 | 省略 | Unreviewed |

文件名在已唯一化的导出 basename 后追加 `.xmp`（`hero.jpg.xmp`，不是 `hero.xmp`），避免共享 stem 的 JPEG+RAW 成对冲突。Lightroom Classic 自动发现 sidecar 常常找 `{stem}.xmp`；本切片保证无歧义配对和 Lightroom 可读的**字段**，不保证自动发现。FramePilot 未对 Lightroom 或 Capture One GUI 往返做过测试，不声称认证。

## 推迟

在原始源文件旁写入 sidecar，或把 XMP 包嵌进图像字节，仍不在范围：这会改变文件安全模型，需要用户明确同意。导入和审阅永不写 XMP。
