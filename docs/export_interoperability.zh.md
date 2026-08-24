# 导出互操作性

> 语言：[English](export_interoperability.md) | **中文**

FramePilot v2.0 支持 CSV、ZIP 和文件夹导出。XMP sidecar 导出计划放在后续 v2.x 切片中，需等确定性处理、筛选和当前导出流程稳定之后。

## 当前模式

- `csv`：写入本地 CSV 产物，包含所选照片、项目照片 id、来源身份字段（`original_path`、`project_copy_path`、`source_identity`、`content_hash`、大小和 mtime）、导入的拍摄与相机元数据、星级、状态、分数、组元数据、尺寸、处理状态/错误字段，以及推荐解释。
- `zip`：写入包含所选项目内原始副本的本地 ZIP，重复文件名用确定性后缀保留。
- `folder`：将所选项目内原始副本复制到本地导出文件夹，重复文件名用确定性后缀保留。

当前所有导出都是项目 `exports/` 目录下的派生输出。它们不修改原始源文件。
ZIP 和文件夹导出要求所选本地项目副本存在。若所选副本缺失，导出会标记为失败，并在可能时删除部分输出。

## 计划中的 XMP Sidecar 范围

第一版 XMP sidecar 实现应是显式导出模式，而不是自动写回步骤。它应当：

- 默认只在项目导出输出目录内创建 sidecar 文件。
- 保持原始照片不变。
- 将 FramePilot 星级映射为 XMP rating 值 `0` 到 `5`。
- 将 FramePilot 的 `Pick`、`Maybe`、`Reject` 和 `Unreviewed` 状态映射为下游工具可检查的保守标签或元数据字段。
- 在合适处把源文件名和项目照片 id 写入 sidecar 元数据。
- 记录带有模式、所选数量、所选状态、输出路径和完成状态的 `ExportRecord`。
- 增加测试，证明 sidecar 文件与原片分开创建，且原片未被修改。

## 推迟的决策

Lightroom 与 Capture One 的精确元数据字段需要在实现前验证。第一版实现在针对这些应用测试之前，不应声称完全兼容。在原始源文件旁写入 sidecar 仍应推迟，因为它改变了文件安全模型，需要用户明确同意。
