# T6 CSV与十万行导出（已确认，等待T2/T5集成）

用户已确认本方案、测试边界及并行分工，接受公式防护改变导出文本及浏览器Blob占用文件大小级别内存的取舍。依赖T5及T2/T5通过集成检查与审查的稳定基线；与T3/T4并行，最终在共同WAL配置上做交叉验证。确认原文见 decisions.md 的 D009。

## 推荐技术方案与取舍

- GET /api/certificates/export.csv，X-Actor-Id鉴权；参数q、sort、order与列表同语义，不受页码限制。建议收到page/page_size时422而非静默截断；静态export.csv路由在动态{id}路由之前注册。
- 复用T5查询规则、排序白名单、字面搜索、租户过滤和日期转换。排序均追加id ASC，即使主字段desc也如此。导出全部匹配证书，包含撤销项；不额外增加状态筛选。
- 固定四列表头 learner_name,course_title,serial_number,issued_local_date，日期YYYY-MM-DD；UTF-8 BOM、CRLF、标准csv.writer转义，方便Excel读取中文。空结果也返回BOM和表头。
- 建议对文本字段做CSV公式防护：若去除前导空白/控制字符后以 =、+、-、@ 开始，或原字段以TAB/CR/LF开始，则在原字段前加单引号。此措施改变导出文本而不改数据库原值；双引号转义本身不防公式。不承诺所有表格软件都按相同方式解释。
- 后端流式响应、独立只读用途连接与显式读事务，单一游标fetchmany(1000)，不把所有行转为Python列表。快照从首次SELECT开始，导出期间修改不混入该次文件。排序临时存储可能由SQLite使用，不能把分批读取等同于数据库零额外内存。
- 使用受控后台线程处理同步SQLite/csv工作，通过有界批次队列交给响应；同一个连接始终由创建它的worker拥有。队列满时有界等待并检查取消，避免无限预读和跨线程连接错误；finally关闭游标/事务/连接。客户端断开触发取消并释放资源，包括尚未产出首批的情况。长快照可能延迟WAL检查点，实测记录这一限制。
- 响应开始前校验身份、参数和时区，并获取首批；开始后的读取失败只能终止下载，不能在CSV末尾混入JSON错误。Content-Type text/csv; charset=utf-8，固定安全文件名及Content-Disposition attachment。
- 浏览器fetch携带身份头，10万行范围内收集Blob后触发下载，并释放object URL；切换身份取消旧下载。明确取舍：服务端流式、客户端Blob按文件大小用内存；暂不增加文件系统API兼容层或带身份信息的下载URL。若需要浏览器也恒定内存，另行确认方案。
- 大数据生成脚本必须显式指定独立目标数据库，拒绝覆盖既有文件；创建专用性能库使East恰好100000张证书，包含排序同值、跨日期及West对照记录，不修改默认seed或正在演示的数据库。

## 验收与垂直TDD边界

先通过小规模真实HTTP和CSV解析用例，再运行一次独立性能场景。不得用ASGI TestClient缓冲后的结果证明实时流式和并发；相关验收启动真实服务，使用真实网络流客户端。

1. 字段/表头/BOM、中文、逗号、引号、换行、公式前缀及空结果；解析内容与明确字面预期比较。
2. Bob导出只含West；搜索与列表一致；超过一页仍导出全部匹配，日期来自租户时区；包含撤销项。
3. 三种排序字段双方向、小样本跨批次同值顺序稳定；重复导出内容一致（数据库无变化条件下）。
4. 真实连接读取首块后暂停消费并请求列表，记录列表响应早于导出EOF；另在导出快照建立后写入，再验证当前文件不混入新数据、下一次导出可见新数据。
5. 中途断开下载后正常列表和写操作可用；结合专用性能库WAL检查点/资源观测确认没有遗留读事务，而不能只用“查询成功”推断连接关闭。
6. 100000行独立性能库：完整导出至少两次，每次从请求发起到完整接收≤60秒；核对总数、租户、顺序和同值稳定性；另做带过滤排序的导出及导出中列表请求。客户端解析采用增量方式，性能测量不计建库时间。
7. 记录Windows/Python/SQLite版本、机器配置、查询条件、文件字节数、每次耗时、列表响应时刻及峰值内存观测。不把某一次本机结果宣传为所有环境保证。

若T5日期函数全量排序未达60秒，先报告测量再确认派生列/表达式索引等变更，不擅自改已批准的日期数据模型。浏览器验收正常下载、失败提示、重复点击限制与切换身份取消。

## 影响与所有权

T6 writer候选路径：backend/app/csv_export.py、backend/tests/test_csv_export.py、tests/test_export_stream.py、scripts/generate_export_fixture.py、scripts/benchmark_export.py、frontend/src/components/certificates/ExportCertificates.vue、frontend/src/api/export.ts、backend/T6-evidence.md。主线程拥有certificate_query.py的共享查询提取、路由和页面挂接。

保持默认启动种子、列表分页、时区和发证/撤销语义不变。不引入数据库迁移或全局依赖。回退只移除导出入口，独立性能文件只在路径明确时按用户授权处理，不删除演示数据库。

依据：[Python CSV](https://docs.python.org/3/library/csv.html)、[SQLite快照事务](https://www.sqlite.org/lang_transaction.html)、[WAL读写并发](https://www.sqlite.org/wal.html)。
