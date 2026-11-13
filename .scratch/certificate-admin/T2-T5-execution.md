# T2 / T5 并行执行边界

用户已批准两项方案与公开测试边界。根 spec.md 为产品规格；T2-proposal.md、T5-proposal.md 为已批准的实施细节。T1 浏览器验收由用户确认通过。

## 所有权与集成顺序

1. T2 writer：backend/app/issuance.py、backend/tests/test_issuance.py、frontend/src/components/certificates/BulkIssue.vue、frontend/src/api/issuance.ts、backend/T2-evidence.md。独立 worktree。
2. T5 writer：backend/app/tenant_time.py、backend/app/certificate_query.py、backend/tests/test_tenant_time.py、backend/pyproject.toml、backend/uv.lock、frontend/src/components/certificates/CertificateTime.vue、backend/T5-evidence.md。独立 worktree。
3. 主线程：main.py 路由与初始化挂接、database.py 必要挂接、Certificate 公共类型、现有列表/详情/过滤器/Page 装配、规格与任务记录。先集成 T2，再集成 T5。

## 小接口

- T2 提供 initialize_issuance(db)（在初始化事务中调用）、issue_course(db, tenant_id, actor_id, course_id)、certificate_audit(db, tenant_id, certificate_id)。业务不可访问对象由模块返回 HTTP 404 或明确异常供路由映射；不得信任客户端 tenant。
- T2 BulkIssue 接收 actorId、courses，成功提交后发出 issued 事件，父组件刷新列表。身份切换清空结果并忽略旧响应；失败不自动重发。
- T5 提供 list_certificates(db, tenant_id, q, page, page_size, sort, order)、get_certificate(db, tenant_id, certificate_id)；将现有 SQL 查询迁入此模块并保持 T1 语义，加入本地日期排序/投影。时间模块仅接收服务端获取的时区。
- T5 CertificateTime 接收 localDate、localDatetime、timezone，按服务端字段显示，不使用浏览器时区换算。
- writer 的 HTTP 测试使用真实文件 SQLite 与 FastAPI 公共接口；共享装配由主线程提供后同步到各 worktree。禁止测试私有函数或用 mock 替代事务行为。

## 影响范围与不变契约

仅本仓库；消费者为本地管理员 UI、HTTP 客户端和启动流程。保留 T1 的 X-Actor-Id、跨租户 404、字面搜索、分页上限和旧排序默认值、种子数据不覆盖、UTC issued_at、健康接口和启动方式。不实现 T3、T4、T6，不更换技术栈，不部署或推送。

回退：保留 T1 基线和原始数据库；新索引遇既有重复明确失败，不删除数据。不自动执行回退或数据删除。

## 验证

逐行为 red → green；各 writer 只运行本项目标 HTTP 测试与必要类型检查。集成后主线程统一执行配置检查与 Standards/Spec 审查。浏览器仅验收新增发证及日期行为，不重复 T1 全流程。不将构建通过当作浏览器通过；未执行项如实记录。
