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

## D005 T1 已确认

- 用户原话：“确认 T1 的方案、测试边界和并行分工，用我的workflow并行开发”。
- 使用 sqlite3、X-Actor-Id、文件库、参数化查询、Vue composable 与独立原生 worktree；范围为读取隔离与默认种子数据。
- 固定契约与文件所有权见 workflow/tasks/20261113-110650-151404-t1-tenant-isolated-certificate-brows/spec.md。T2 之后仍待确认。

## D006 T1 浏览器验收

- 用户原话：“T1 浏览器验收通过了，按已确认的方案用我的 workflow 并行开发 T2、T5。”
- 来源：另一个 fork 窗口执行浏览器验收，由用户向本线程确认通过；本线程不重复浏览器操作，不声称亲自完成该轮验收。

## D007 T2 与 T5 并行批准

- 用户原话：“批准两项并行（含撤销后不重发）”；D006 再次授权开始。
- T2：终身唯一证书、撤销后不重发；BEGIN IMMEDIATE + 每学员 SAVEPOINT；证书和 ISSUED 审计原子提交；逐人 issued/skipped/failed；公共审计读取接口。幂等结果重放仍属 T3。
- T5：zoneinfo + tzdata；保留 UTC 原值，动态生成租户当地日期/时间；SQLite 受控日期函数在分页前排序，同日 id ASC；不新增日期存储列。CSV 与十万行性能仍属 T6。
- 公共测试边界、权衡与验收见 .scratch/certificate-admin/T2-proposal.md、T5-proposal.md。独立 worktree 并行，主线程负责共享文件装配。

## 记录格式

每项记录需求 ID、具体决定、备选与取舍、用户确认原文或真实来源、测试边界、实施引用、验证证据与提交（存在时）。没有证据的字段标记待补，不编造。

## D008 T1 本地基线提交授权

- 用户原话：“允许本地 T1 基线提交，不推远端”。
- 已执行本地提交 1b30bbe13fde37334738a22b5a3395d53b8fdee5，包含 T1 实现、验收记录与已批准的后续规划。无远端推送。
- T2、T5 worktree 从同一提交建立；原 T1 开发 worktree 保留。后续代码提交未获授权。

## D009 T3、T4、T6 条件执行批准

- 用户原话：“确认 T3、T4、T6 的方案、测试边界和并行分工，接受这两个取舍，等 T2/T5 集成通过后按我的 workflow 并行开发。”
- 已批准：.scratch/certificate-admin/T3-proposal.md、T4-proposal.md、T6-proposal.md 及 T3-T4-T6-parallel-plan.md；T4不再依赖T3，三项共同等待T2/T5集成检查与审查通过。
- 接受：T3刷新页面不恢复前端重试上下文，服务端仍持久化结果；T6公式防护会改变导出文本，浏览器Blob占用与文件大小相应的内存。
- 此批准允许满足前置条件后并行实施，无需重复确认相同技术方案；不授权提前越过依赖、不授权新本地提交或推送。执行包在稳定基线就绪时记录相同批准与独立所有权。

## D010 T2/T5基线与后续并行授权

用户原话：允许本地提交 T2/T5 基线和任务文档，不推远端，然后创建三个独立 worktree，按已确认的方案用我的 workflow 并行开发 T3、T4、T6。授权仅本地基线提交；三个后续功能不自动提交或推送。

## D011 本地合并与整体开发验收提交

用户原话：合并代码整体验收提交。执行范围为已有批准功能的完整检查、证据整理、本地提交及main快进合并；不推远端、不部署，不将执行检查理解为用户已亲自完成业务验收。复用已批准的测试边界，无新技术方案。
