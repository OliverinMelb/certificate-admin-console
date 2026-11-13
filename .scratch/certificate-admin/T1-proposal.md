# T1 管理员切换与租户隔离列表方案

状态：用户已确认方案、测试边界和并行分工。当前按 workflow/tasks/20261113-110650-151404-t1-tenant-isolated-certificate-brows/spec.md 的具体契约执行。

## 目标

让 Alice 与 Bob 各自查看所属租户的课程、证书列表与只读详情，具备姓名/编号搜索、分页、排序及加载/空/错误状态。实现 A1 的读取部分及默认演示数据；发证、撤销、幂等与导出留给后续 ticket。

## 推荐技术决策

1. 数据访问：Python 标准库 sqlite3 + 参数化 SQL，暂不引入 ORM。每个请求独立连接；同步数据库访问用 FastAPI 普通 def 路由，避免在 async 路由中直接执行阻塞数据库操作。连接启用外键，结束请求及时关闭。
2. Schema：tenant、admin、course、learner、enrollment、certificate；稳定主键，租户字段、复合外键保持关联属于同一租户。索引优先覆盖租户、默认排序和关联键；姓名包含搜索不声称能命中普通 B-tree 索引。
3. 身份：演示 X-Actor-Id，服务端查 admin → tenant_id，缺失/无效返回 401；这是题目允许的身份模拟，不是生产认证。任何目标 tenant_id 参数都不能覆盖服务端解析结果。
4. Seed：事务内幂等插入，包含 East/West、各自管理员、同名 Safety 101/Alex Lee、混合完成状态与已发证样例。启动时创建缺失 schema 并 seed；重复启动不覆盖用户已有数据。
5. 数据路径：默认项目 data/certificates.sqlite3；测试通过应用工厂传入临时文件路径，测试与演示数据不共用。数据目录忽略入 Git。WAL/锁等待细节与 T3 并发协议一并确认，T1 不据此声称并发发证已完成。
6. 列表协议：q 为去首尾空格后的姓名或编号字面包含匹配，SQL LIKE 的 %/_ 转义；page 默认 1；page_size 默认 50，上限 100；越界参数 422；越过最后一页返回空 items 与真实 total。
7. 排序：T1 先实现 learner_name/serial_number 两个白名单字段、asc/desc；末尾追加 id 升序作稳定决胜键；非法排序 422。当地日期显示/排序在 T5 确认实现，此项不先确定存储派生日期。
8. 前端：CertificatePage 编排，ActorSelect/CertificateFilters/CertificateTable/CertificatePagination/CertificateDetail 分工；useCertificates 管理请求；props down/emits up，无 Pinia。切换身份清空旧结果与详情、重置页码，取消旧请求并用请求序号阻止迟到响应覆盖；搜索防抖 300ms。

## 接口草案

- GET /api/actors：仅返回明确标注为演示用的管理员选择项。
- GET /api/courses：当前身份所属租户课程。
- GET /api/certificates?q=&sort=serial_number&order=asc&page=1&page_size=50 → items、total、page、page_size。
- GET /api/certificates/{id}：所属租户详情；其他租户或不存在的 id 均返回相同 404。
- T1 不创建 mutation API、审计表和公开审计 API，T2 再确认。

## 测试边界与验收

主要边界为真实文件 SQLite 支撑的 HTTP API；seed 通过公开启动行为与 HTTP 观察，不测试 SQL 字符串或私有仓库方法。

1. 缺失/无效身份拒绝；Alice/Bob 的列表、课程和详情互相隔离。
2. 跨租户与不存在详情均 404；伪造 tenant_id 不改变访问范围。
3. 姓名/编号搜索、%/_ 字面搜索、分页边界、非法参数、同名排序稳定。
4. 重复启动后列表和总数不重复增长；临时测试库不污染演示库。
5. 真实浏览器切换身份、搜索、翻页、只读详情；无结果与错误状态可观察，旧请求不覆盖新租户状态。

每条验收逐个 red → green；完成 T1 后报告 A1 读取范围，不能声称 A1 的发证/导出场景已通过。需要用户确认以上方案及边界后，才创建并批准 T1 执行 packet。
