# T1 执行规格与并行契约

用户确认：“确认 T1 的方案、测试边界和并行分工，用我的workflow并行开发”。沿用根 spec.md 与 .scratch/certificate-admin/T1-proposal.md 的范围和约定。本项仅实现读取闭环，不实现 T2～T7 的业务操作。

## 固定接口

- GET /api/actors 为演示身份入口，无需身份头，返回 {items: Actor[]}。
- Actor: {id, email, tenant_id, tenant_name, timezone}。alice 属于 east / East / Australia/Sydney；bob 属于 west / West / Australia/Perth。
- 其余业务 GET 请求必须带 X-Actor-Id，缺失/未知 401；未知/跨租户证书详情返回相同 404。
- GET /api/courses → {items: [{id, title}]}。种子课程 ID 为 east-safety 与 west-safety，标题均 Safety 101。
- GET /api/certificates → {items: Certificate[], total, page, page_size}。
- Certificate: {id, serial_number, learner_id, learner_name, course_id, course_title, issued_at, status}；status 为 ACTIVE/REVOKED；issued_at 是 UTC ISO 字符串，本阶段 UI 明确标记 UTC，T5 再确认当地日期转换。
- GET /api/certificates/{id} → Certificate，与列表项字段一致。
- q 默认为空，trim 后按姓名或编号字面包含匹配，转义 LIKE 的反斜杠、% 和 _；SQLite 默认 ASCII 不区分大小写语义，不承诺完整 Unicode case folding。
- sort 默认为 serial_number，允许 learner_name/serial_number；order 为 asc/desc，默认 asc；追加 id ASC 稳定排序。page 默认1且>=1，page_size 默认50且1～100；非法值422。页外返回空 items 与真实 total。
- 客户端 tenant_id 参数不影响服务端身份解析或查询范围。

## 数据与启动

sqlite3、参数化 SQL、连接启用 foreign_keys；每个同步请求独立连接并关闭。六个表、复合租户外键、稳定种子 ID、事务幂等初始化。create_app(database_path=...) 接受测试临时文件路径，默认本 worktree 的 data/certificates.sqlite3；启动初始化且重复启动不覆盖数据。

建议默认种子 East 12 张、West 4 张已发证样例以便页面分页验收；两侧均有 Alex Lee、Safety 101，同时有已完成未获证与未完成报名。east-cert-001 / west-cert-001 使用原题固定 UTC 时间。用稳定确定性数据，不依赖随机。

## UI

组件按提案分工，composable 管理请求、300ms 防抖、取消和请求序号。身份切换立即清除列表、课程和详情，页码回到1。分页大小可选5/10/50/100，默认50；搜索/排序/页大小改变重置页码。只读详情使用原生 dialog 或语义清晰区域，不添加全局状态库或依赖。loading/empty/error/retry 可见。

## 并行所有权与顺序

共同 base SHA: a9ee16346692aee0d5ca47362909bc9f41b28edd；三个目录都是原生 linked worktree、detached HEAD。

1. backend writer: C:/Users/admin/.codex/worktrees/certificate-backend/certificate-admin-console，仅 backend/**；逐个 HTTP 行为 red→green；不得编辑其他 worktree。
2. frontend writer: C:/Users/admin/.codex/worktrees/certificate-frontend/certificate-admin-console，仅 frontend/**；遵守固定契约，typecheck/build；真实 UI 验收由主线程在集成后完成，不把 mock 当真实集成证据。
3. root verifier/integrator: C:/Users/admin/.codex/worktrees/certificate-verification/certificate-admin-console，工作期间仅 tests/**、scripts/**、workflow/**、.scratch/**、README.md、decisions.md、tasks.md；后端和前端 writer 停止后依次复制限定变更集到当前工作区，再验证。

不创建提交或推送；用户先前提交授权仅覆盖 T0 基线。本次文件集集成不使用 git merge，也不改动 Desktop 主目录。并行测试各用独立临时目录/端口；避免重复运行完整启动矩阵。

## 验收

- AC1 身份与租户：401；列表/课程/详情隔离；跨租户和不存在同404；伪造tenant_id无效。
- AC2 查询：搜索及字面通配符、分页、非法参数、同名稳定排序。
- AC3 持久化：真实临时文件SQLite、默认种子完整、重复启动不增加数量或覆盖已有数据、测试不污染默认库。
- AC4 UI：身份/搜索/分页/详情，loading/empty/error与重试，旧响应不能覆盖新租户。
- AC5 集成：单命令启动后包含演示数据，原T0健康接口/静态资源/启停不回归。

主要自动边界为真实文件SQLite支撑的HTTP接口、启动公开入口；不测内部SQL文本或私有方法。浏览器通过实际用户操作验收。批准了整体方案与公开边界；接口字段与固定ID为并行实现所需的具体化，不扩大需求。
