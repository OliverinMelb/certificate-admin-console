# T5 租户当地日期与排序方案

状态：用户已批准实现。确认原文：“批准两项并行（含撤销后不重发）”；T1 浏览器验收通过后，用户再次要求按已确认方案并行开发 T2、T5。依赖调整为 T1；无需等待发证或撤销。

## 行为与技术决定

- 保留 issued_at 为UTC原始事实，不新增当地日期持久化列，避免与T2并行修改证书表及派生数据一致性问题。
- 使用 Python zoneinfo.ZoneInfo 与显式声明的 tzdata 依赖，读取 tenant.timezone；Windows缺少系统IANA数据库时仍可运行。时区来源只能是服务端租户，不接受客户端覆盖。
- API为证书列表项和详情增加 issued_local_date（YYYY-MM-DD）、issued_local_datetime（带UTC偏移的ISO字符串）、timezone；保留 issued_at 不变。
- UI使用服务端返回的当地时间和时区标识；不按浏览器本地时区二次转换。非法/未知时区或无时区时间戳报明确错误，不静默退回UTC。
- 扩展sort白名单允许issue_date。日期排序按租户当地日历日，日内不按时分秒排序，仍用唯一id ASC作稳定决胜键，保持已有asc/desc与分页契约。
- 推荐SQLite连接注册受控本地日期函数，ORDER BY tenant_local_date(issued_at), id；函数闭包绑定已验证租户的ZoneInfo对象。排序在数据库分页前完成，不能只排序当前页或把全部行加载到浏览器。
- 不采用SQLite localtime依赖宿主时区，也不使用固定UTC+偏移代替IANA时区。计算排序当前不能利用普通issued_at索引；T6按10万行实测评估，若不达标再讨论派生列/索引，不能无证据承诺性能。
- 同一日期转换模块同时服务列表、详情和未来CSV；T5交付复用接口，CSV功能在T6实现。

## 测试边界

仍以真实文件SQLite支撑的HTTP列表/详情为主要边界；准备固定时间的测试夹具。期望值来自人工明确的样例，不调用待测函数生成期望值。

1. 原题UTC 2026-01-10T13:30:00Z：Sydney为2026-01-11 00:30（+11:00），Perth为2026-01-10 21:30（+08:00）。
2. 冬季Sydney标准时、夏令时切换前后、跨当地午夜的样例，覆盖偏移变化。
3. 本地同日不同UTC时刻按id稳定决胜；跨日期升/降序正确，跨分页无重复或漏项。
4. 租户切换使用所属时区，列表与详情字段一致；未知时区不能显示误导性日期。
5. 浏览器显示租户当地日期及明确时区，排序选择可用；浏览器所在时区不改变同一租户显示结果。

T5覆盖A5列表/详情及转换契约；A5的CSV部分需在T6补齐后才算全部完成。不提前执行完整10万行导出性能测试。

## 并行边界

依赖T1即可，与T2同时开始。T5拥有时间模块、日期查询模块与日期UI；不修改T2发证/审计逻辑和schema。公共Certificate类型、main.py路由装配和现有列表组件挂接由主线程串行集成，避免共享文件冲突。确切拥有路径在批准后的workflow任务包登记。

资料：Python zoneinfo https://docs.python.org/3/library/zoneinfo.html；SQLite自定义函数 https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.create_function 。
