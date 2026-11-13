# 技术决策与确认记录

## D001 已确认的主技术栈

- 日期：2026-11-13，Asia/Shanghai。
- 用户原话：“就按 Vue 3 + FastAPI + SQLite 来”。
- 决定：使用上述技术栈，建立独立项目；spec 与任务清单落盘；按 SDD + TDD 结合 codex-workflow 开发。
- 限制：每项需求的具体技术选型或最佳实践必须先与用户确认。此前推荐不能视为整包批准。

## D002 独立工作目录

- 已执行的工作区选择：C:/Users/admin/Desktop/certificate-admin-console。
- 理由：独立于原 ComfyUI 目录；建立新的 Git 仓库，main 分支；无远端、无提交。
- 影响：仅此新目录的文档和 workflow 初始化配置。未改动原项目。

## D003 项目 workflow conventions

- 状态：已确认并应用。
- 用户原话：“确认，就按推荐的 workflow 配置来，先建立任务包，再把 T0 的技术方案和测试边界给我确认。”
- 决定：本地 Markdown tracker；远端发布需明确授权；单一领域文档；AGENTS.md；不引入 triage。
- 执行：setup 已完成，doctor 通过。此确认不授权 T0 实现。

## D004 T0 技术方案与测试边界

- 状态：已确认，允许实现 T0。
- 用户原话：“确认 T0 的方案和测试边界，再确认 T1 的方案。”
- 方案：见 workflow/tasks/20261113-103832-835581-t0-one-command-application-bootstrap/spec.md。
- 本机事实：Node v24.18.0、npm 11.16.0、Python 3.14、uv 0.13.7。补丁版本及依赖兼容性在批准后的锁定阶段核验。
- 推荐：Vue 3 + TypeScript + Vite；Python 3.14 + uv；npm lock 与 uv lock；Node 跨平台启动脚本；FastAPI 同源提供构建产物；HTTP/API 与真实进程边界测试，浏览器验收最小页面。

## 后续确认记录格式

每项记录需求 ID、具体决定、备选与取舍、用户确认原文或真实来源、测试边界、实施引用、验证证据与提交（存在时）。没有证据的字段标记待补，不编造。
