# Certificate Admin Console

独立的多租户培训证书后台项目。已确定 Vue 3 + FastAPI + SQLite；使用 SDD + TDD 和 codex-workflow，逐项确认技术方案后开发。

当前状态：T0 与 T1 已实现，T1 在 certificate-verification worktree 集成。具体检查、审查与验收状态见 workflow/tasks/20261113-110650-151404-t1-tenant-isolated-certificate-brows/。Desktop 主目录仍为已提交的 T0 基线；T1 尚未提交。T2 及之后的需求尚未实现。

- [轻量规格](spec.md)：功能范围、A1～A7、接口草案、影响范围与验证策略。
- [开发任务](tasks.md)：T0～T7、依赖、确认点和完成条件。
- [决策记录](decisions.md)：已确认内容与待确认方案。

## 开发约定

每个需求先确认方案与测试边界，再逐条执行失败测试 → 最小实现 → 通过。当前主技术栈批准不代表全部具体设计已批准。

## 启动

前置工具：Node.js 24（实测 24.18.0）、npm（实测 11.16.0）、Python 3.14.6、uv（实测 0.13.7），均可从 PATH 找到。首次安装需要联网；不会安装或更改全局包。Windows 已实测；Linux/macOS 尚未实测。

在项目根目录执行：

```text
node scripts/start.mjs
```

脚本使用 `uv sync --locked` 和 `npm ci`，完成前端类型检查和构建，再在 http://127.0.0.1:8000 提供页面。可用 `node scripts/start.mjs --port 8010` 更换端口。Ctrl+C 停止；端口被占用会失败，不会终止原占用者。脚本路径可使用绝对路径，调用者工作目录不影响项目定位。

后端环境位于 backend/.venv，前端依赖位于 frontend/node_modules；正常启动不重写锁文件。锁文件与声明不一致时停止，维护者需有意更新锁文件。

## T1 身份与读取契约

T1 使用演示身份头 `X-Actor-Id: alice` 或 `X-Actor-Id: bob`。这是题目允许的身份模拟，不是生产认证；调用者可以切换这两个演示身份。

默认数据库为当前项目的 data/certificates.sqlite3，首次启动创建并初始化；后续启动补齐缺失的种子记录，不覆盖已存在记录。两个 worktree 的默认数据库彼此独立。测试通过临时文件库隔离，不使用演示数据库。

- East：alice@east.test，Australia/Sydney；默认12张证书。
- West：bob@west.test，Australia/Perth；默认4张证书。
- 两边都有 Safety 101 和 Alex Lee，以及完成未获证、未完成和已获证报名。
- 当前时间展示明确标记 UTC；租户当地日期与夏令时在 T5 实现。

读取端点：/api/actors、/api/courses、/api/certificates、/api/certificates/{id}。除演示身份入口外均需要身份头。缺失/未知身份401；跨租户详情与不存在详情均404。

列表参数 q 支持姓名/编号字面包含搜索，% 和 _ 按字面字符处理；sort 为 learner_name/serial_number，order 为 asc/desc，默认按编号升序；page 默认1，page_size 默认50且最大100。未知排序、非法页码/页大小422；页码超出数据范围时返回空items和真实total。

Windows 可使用 curl.exe 验证读取隔离（先启动应用）：

```text
curl.exe -H "X-Actor-Id: alice" "http://127.0.0.1:8000/api/certificates?q=Alex"
curl.exe -H "X-Actor-Id: bob" "http://127.0.0.1:8000/api/certificates/east-cert-001"
```

第二个请求应返回404；同一ID由Alice访问应成功。伪造tenant_id查询参数不能扩大所属租户范围。此复现仅覆盖A1读取部分，发证/导出部分尚未实现。

## 验证

```text
node scripts/check.mjs
```

执行依赖同步、前端类型检查和构建、HTTP 契约测试、真实进程 smoke。后者在系统临时目录建立不含依赖和构建产物的隔离副本，验证中文/空格路径、任意工作目录启动、停止和重启、端口冲突、锁文件不一致；临时副本由 pytest 管理，可能保留供失败诊断。

GET /api/health 返回 `{"status":"ok"}`，只表示进程健康。未知 /api 路由返回 404。浏览器页面自动检查连接，并提供“重新检查”；错误态测试通过停止本次服务后点击按钮完成。

自动测试不能替代真实浏览器验收；浏览器记录保存在对应 workflow packet。tests/browser_proxy.py 是仅用于验收的本地代理，可给Alice请求延迟或返回503来验证loading、身份切换和错误恢复，不属于应用运行依赖。

## 待交付

剩余A1发证/导出场景、A2～A7、完整业务复现、大数据生成、完整AI原始活动证据及索引。任务内执行摘要不能替代原始会话导出。原题书面题由候选人独立完成，不生成答案或完成声明。
