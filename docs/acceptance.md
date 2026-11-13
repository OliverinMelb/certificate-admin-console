# 本地整体开发验收

范围：T0～T6应用功能、集成、启动与性能复现；用户授权“合并代码整体验收提交”。不包含部署、远端推送、书面题答案或完整考试材料认证。主分支通过快进接收已审查的集成版本，不重复合并各worker的临时路由适配文件。

## A1～A7证据索引

| 验收 | 自动复现入口 | 已有补充证据 |
| --- | --- | --- |
| A1 租户隔离 | backend/tests/test_certificates.py、test_issuance.py、test_csv_export.py、test_revocation.py | T1及T3/T4/T6浏览器身份切换记录 |
| A2 幂等并发 | backend/tests/test_idempotency.py | 已提交响应丢失后的同key浏览器重试与代理观察 |
| A3 key冲突 | backend/tests/test_idempotency.py | 同key换合法课程409，未知body422；原结果不覆盖 |
| A4 发证资格 | backend/tests/test_issuance.py | T2逐人结果页面 |
| A5 租户时间 | backend/tests/test_tenant_time.py、test_csv_export.py | Sydney/Perth字面样例与CSV实际下载 |
| A6 十万行导出 | scripts/benchmark_export.py、tests/test_export_stream.py | 集成版两次100000行1.098s/0.947s，相同hash；列表0.510s先于EOF |
| A7 重复撤销 | backend/tests/test_revocation.py、test_workflow_integration.py | 撤销确认、失败重试、详情及审计刷新 |

运行完整快速检查：`node scripts/check.mjs`。其启动用例建立干净临时副本，验证依赖安装、中文/空格路径、任意cwd、重启、端口冲突及锁文件不一致。独立性能复现命令见README；本次合并未改变已测业务代码，无需重复十万行实验。

T3/T4/T6执行包：`workflow/tasks/20261113-114507-789367-t3-t4-t6-implementation-on-integrate/`，包括两次完整verify、独立审查结论、实际下载CSV、截图与浏览器观察。最终提交前完整检查见 `workflow/tasks/20261113-121846-746294-final-local-acceptance-and-main-inte/`。

## 限制与原始AI证据

- 仅Windows本地实测。演示身份头不是生产认证。
- 本机SQLite3.50.4的罕见WAL-reset风险已在README说明；本轮没有升级运行时，不宣称生产部署安全。
- 发证key记录暂不清理；刷新后不恢复前端重试上下文；CSV公式防护改变导出文本，浏览器Blob占用文件大小级别内存。这些取舍已获确认。
- 后置CSV producer异常的专门故障注入未覆盖；断连和首块错误已测。关闭正在撤销的详情不保证服务端取消，列表可能需要重新加载。
- 原始AI对话与工具活动仍在Codex会话中；仓库内evidence是执行记录与索引，不是完整原始会话导出。尚未生成原始导出包，不将T7完整考试交付标成完成。
- 本地技术验收不代替用户业务验收。原worktree保留，不删除用户数据库、分支或工作区。
