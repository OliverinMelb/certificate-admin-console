# Certificate Admin Console

独立的多租户培训证书后台项目。已确定 Vue 3 + FastAPI + SQLite；使用 SDD + TDD 和 codex-workflow，逐项确认技术方案后开发。

当前状态：T2/T5 已集成并保存为本地基线 746edee。T3/T4/T6 已在三个独立worktree开发并集成，接口/启动/浏览器检查及独立代码审查通过，业务验收待用户确认；最终记录以 workflow/tasks/20261113-114507-789367-t3-t4-t6-implementation-on-integrate/ 为准。应用代码已本地提交为7d90f26，并快进合并到 Desktop 主目录的main；验收记录见docs/acceptance.md，未推远端。

- [轻量规格](spec.md)：功能范围、A1～A7、接口草案、影响范围与验证策略。
- [开发任务](tasks.md)：T0～T7、依赖、确认点和完成条件。
- [决策记录](decisions.md)：已确认内容与待确认方案。
- [整体验收索引](docs/acceptance.md)：A1～A7复现入口、实测证据和交付限制。

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
- T5 在列表/详情展示服务端生成的租户当地日期与时间，带 IANA 时区及 UTC 偏移；原始 issued_at 保留 UTC。

读取端点：/api/actors、/api/courses、/api/certificates、/api/certificates/{id}。除演示身份入口外均需要身份头。缺失/未知身份401；跨租户详情与不存在详情均404。

列表参数 q 支持姓名/编号字面包含搜索，% 和 _ 按字面字符处理；sort 为 learner_name/serial_number/issue_date，order 为 asc/desc，默认按编号升序；page 默认1，page_size 默认50且最大100。未知排序、非法页码/页大小422；页码超出数据范围时返回空items和真实total。

Windows 可使用 curl.exe 验证读取隔离（先启动应用）：

```text
curl.exe -H "X-Actor-Id: alice" "http://127.0.0.1:8000/api/certificates?q=Alex"
curl.exe -H "X-Actor-Id: bob" "http://127.0.0.1:8000/api/certificates/east-cert-001"
```

第二个请求应返回404；同一ID由Alice访问应成功。伪造tenant_id查询参数不能扩大所属租户范围。此复现覆盖 A1 读取部分。发证越租户行为另见下文，导出使用相同租户隔离。

## 验证

```text
node scripts/check.mjs
```

执行依赖同步、前端类型检查和构建、HTTP 契约测试、真实进程 smoke。后者在系统临时目录建立不含依赖和构建产物的隔离副本，验证中文/空格路径、任意工作目录启动、停止和重启、端口冲突、锁文件不一致；临时副本由 pytest 管理，可能保留供失败诊断。

GET /api/health 返回 `{"status":"ok"}`，只表示进程健康。未知 /api 路由返回 404。浏览器页面自动检查连接，并提供“重新检查”；错误态测试通过停止本次服务后点击按钮完成。

自动测试不能替代真实浏览器验收；浏览器记录保存在对应 workflow packet。tests/browser_proxy.py 是仅用于验收的本地代理，可给Alice请求延迟或返回503来验证loading、身份切换和错误恢复，不属于应用运行依赖。

## 待交付

T3/T4/T6 已覆盖幂等、撤销、CSV及十万行场景。剩余T7最终交付整理、用户业务验收、完整AI原始活动证据及索引。任务内执行摘要不能替代原始会话导出。原题书面题由候选人独立完成，不生成答案或完成声明。

## T2 / T5 新增行为

选择管理员和课程后，点击批量发证；仅完成课程且从未获证的学员可获证。已有证书（包括已撤销）和未完成学员跳过。结果逐人列出状态及原因，成功后刷新证书列表；身份切换清空旧操作结果。

```text
curl.exe -X POST -H "Idempotency-Key: demo-issue-1" -H "X-Actor-Id: alice" "http://127.0.0.1:8000/api/courses/east-safety/issue"
curl.exe -X POST -H "Idempotency-Key: demo-issue-1" -H "X-Actor-Id: bob" "http://127.0.0.1:8000/api/courses/east-safety/issue"
curl.exe -H "X-Actor-Id: alice" "http://127.0.0.1:8000/api/certificates?sort=issue_date&order=asc"
```

默认 East 第一次发证 1 人成功，其余跳过；重复提交不会新增证书。Bob 请求 East 课程返回 404。发证结果中的 certificate_id 可用于 GET /api/certificates/{id}/audit，真实发证对应一条 ISSUED 记录。演示种子证书未伪造历史审计。

UTC 2026-01-10T13:30:00Z 在 Sydney 显示 2026-01-11 00:30（+11:00），在 Perth 显示 2026-01-10 21:30（+08:00）。日期排序按当地日历日，同日按唯一 ID 升序；日期计算发生在数据库分页前。

T3发证必须携带1～128字符的非空可打印ASCII Idempotency-Key。同一租户/管理员/操作/key重试返回首次结果；换课程409，未知body字段422。网络失败在页面选择“重试原操作”沿用key；新操作使用新key，刷新页面不保留重试上下文。已有重复证书的旧库会在新增唯一索引时明确失败，不自动清理数据。

## T4 撤销与 T6 导出

撤销：POST /api/certificates/{id}/revoke，空body或{}，同样携带演示身份头。有效证书首次changed:true，重复changed:false，均返回200；详情审计只新增一次REVOKED。撤销后不恢复、不重新发证。UI先确认，再刷新详情、审计与列表。

CSV：GET /api/certificates/export.csv?q=&sort=issue_date&order=asc，携带演示身份头。导出全部匹配，包含撤销项，不接受page/page_size。四列为learner_name,course_title,serial_number,issued_local_date；UTF-8 BOM/CRLF；危险公式前缀文本加单引号（不改变数据库原值）。服务端有界分批快照读取，浏览器Blob下载按文件大小占用内存。

SQLite启用WAL，每连接busy_timeout=5000ms。已核对本机Python3.14.6链接SQLite3.50.4，官方披露罕见WAL-reset竞态，修复版本为3.50.7或3.51.3及以后：https://www.sqlite.org/wal.html 。本轮未升级已批准运行时，不能将本地测试等同生产可靠性承诺。仅Windows实测；演示身份不是生产认证。

## 独立性能复现

下面命令只生成显式指定的新文件库；已有文件会拒绝覆盖，不修改默认演示库。基准脚本启动自己的临时端口服务并在结束时停止；100000行完整导出两次及过滤导出另行计时。

```powershell
backend/.venv/Scripts/python.exe scripts/generate_export_fixture.py --database .smoke/export-performance.sqlite3 --rows 100000
backend/.venv/Scripts/python.exe scripts/benchmark_export.py --database .smoke/export-performance.sqlite3 --rows 100000
```

快速检查仍使用 `node scripts/check.mjs`；十万行性能脚本不自动重复运行。CSV取消/快照并发通过tests/test_export_stream.py的真实TCP服务验证，普通API通过文件SQLite+HTTP验证。
