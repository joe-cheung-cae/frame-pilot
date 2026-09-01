# FramePilot v2 测试策略

> 语言：[English](v2_testing_strategy.md) | **中文**

FramePilot v2 测试应证明本地照片工作流端到端可用，同时不让默认开发循环过慢。每次提交都应用快速确定性测试覆盖核心行为。更大的本地工作流应保持为显式 smoke 或性能命令。

## 测试分层

### 后端单元与服务测试

用 `apps/api/tests` 覆盖确定性后端行为：

- 评分归一化与图像质量惩罚
- 感知哈希与分组决策
- 组内排序与推荐解释
- 导入校验、跳过文件、重复文件名和文件安全
- 处理任务进度、重试、过期任务恢复和失败项处理
- CSV、ZIP、文件夹导出内容与产物安全
- SQLite 兼容迁移与查询索引

这些测试应使用临时目录和生成图像。它们不得要求私人照片数据集、网络访问、云服务或大模型文件。

### 后端集成测试

集成测试应通过 `TestClient` 走本地 API 工作流：

- 创建项目
- 导入 JPEG、PNG 或 WebP 夹具
- 轮询处理任务至完成或失败
- 按复核顺序列出照片和组
- 更新用户状态和星级
- 创建 CSV、ZIP 和文件夹导出
- 下载已完成的 CSV 和 ZIP 产物
- 验证原始源文件未被修改

在后续 v2.x 切片实现预览提取之前，不支持的 HEIC 和 RAW 文件应作为跳过导入来覆盖。

### 前端单元测试

前端单元测试应保持工作区状态和大列表逻辑稳定：

- 项目路由决策
- 复核进度持久化解析
- 键盘与组导航辅助函数
- 胶片条、组侧栏和对比模式窗口化
- 导出状态摘要与下载资格

当 UI 行为超出纯辅助函数逻辑时，应增加组件级测试，尤其是导入、处理进度、筛选状态更新和导出历史。

### E2E 测试

保留两层 E2E：

- 用于快速 UI 回归的 mocked E2E
- 使用生成合成图像的真实本地 smoke E2E，用于浏览器加 API 工作流验证

真实 smoke E2E 必须只用生成的本地图像。它应覆盖项目创建、导入、处理进度、复核状态更新、导出创建，以及测试环境能可靠支持下载时的浏览器可下载产物。

### 性能与可靠性 smoke

大批量验证应保持为可选：

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
```

性能 smoke 应报告生成、导入、处理、导出耗时、失败项数量、组数和峰值 RSS。最初目标是可靠性：不崩溃、内存增长有界、进度可见、失败可重试、原片完好。

## 提交前必做检查

开发时用最窄的相关检查，完成一个切片后再跑仓库门槛：

```bash
npm run verify
```

GitHub Actions（`.github/workflows/verify.yml`）在 pull request 与 `main` 上跑 `npm run test:e2e`（mocked E2E 加上 `tests/e2e/real-local-smoke.spec.ts`），以及独立的 `npm run test:e2e:real-browser` 作业（100 张生成 JPEG，Chromium）。该门禁不含 `test:e2e:real-browser:large`。当前端工作流变更影响项目创建、导入、处理、筛选或导出流程时，本地运行 `npm run test:e2e`。100 张真实浏览器-后端 smoke 本地运行 `npm run test:e2e:real-browser`。

## 测试数据规则

- 用 `npm run generate:synthetic` 生成合成图像。
- 把临时图像放在 `/tmp` 或 pytest 临时目录下。
- 不要提交私人照片、生成的照片数据集或大模型文件。
- 永远不要写会修改或删除原始源照片文件的测试。
