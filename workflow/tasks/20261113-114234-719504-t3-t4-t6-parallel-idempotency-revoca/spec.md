# T3/T4/T6 执行规格

根 spec.md 为产品验收依据；本轮详细合同为 .scratch/certificate-admin/T3-proposal.md、T4-proposal.md、T6-proposal.md 与 T3-T4-T6-parallel-plan.md。用户已逐项整包确认，并明确不再补充grilling讨论、按原方案实施；此记录代表共同理解确认，不伪称进行了逐项问答。

最新授权：“T2/T5 集成通过了 按原方案用我的 workflow 并行开发 T3、T4、T6。”前置任务20261113-112716-944318-t2-t5-parallel-issuance-and-tenant-d已CLOSED，最终verify PASS且acceptance coverage covered。

## 范围与验收

- T3：必需Idempotency-Key；tenant/actor/operation/key作用域；规范请求冲突409；成功结果、证书和审计原子持久化；并发与重启重放；忙锁503；浏览器同key显式重试，不承诺刷新后恢复重试上下文。
- T4：租户内有效证书撤销及审计同事务；首次changed:true，重复changed:false；同证书并发仅一条REVOKED审计；确认弹窗、详情与列表刷新；撤销后不重发。
- T6：租户过滤、搜索排序与T5日期语义一致；四列CSV，BOM/CRLF/公式前缀防护，包含撤销项；独立连接快照与有界流式读取/取消释放；浏览器Blob下载；专用10万行库重复导出≤60秒且导出过程中列表成功。
- 不变：T1租户隔离、T2资格和终身唯一、T5UTC与当地日期规则、默认seed、启动方式。不引入生产认证、云服务、数据库替换或全局依赖。

## 已核对的适配点

issuance.issue_course当前拥有BEGIN IMMEDIATE，主线程需提取事务内执行入口供T3包装，不允许嵌套BEGIN；保持T2原资格及savepoint语义。certificate_query当前将过滤、日期排序与分页写在list_certificates内，主线程提取公共查询构造供T6使用，禁止worker复制后产生两种排序规则。数据库状态字面量使用既有ACTIVE/REVOKED，外部撤销响应按proposal返回revoked。

## 所有权与集成

三个writer分别拥有proposal列明的独立模块及测试，原生worktree共用T2/T5稳定提交。主线程独占main.py、database.py、issuance.py事务适配、certificate_query.py共享查询、既有Page/Detail/BulkIssue与公共类型。顺序T3→T4→T6；先登记worktree/base SHA/路径，再启动writer。

## 验证

每个writer一次red→green循环只实现一个公共行为，以真实HTTP+文件SQLite验证。并发使用真实重叠请求及锁夹具，流式/取消使用真实网络；不以mock证明事务或TestClient缓冲证明流式。主线程最终统一快速检查、独立Standards/Spec审查与新增浏览器行为；性能场景独立执行并保留环境/时间/数量/顺序证据。

跨项验证：撤销后旧发证key重放不恢复证书，CSV包含撤销项且日期一致，导出中写入不混入当前快照、下一次可见，身份切换不显示旧结果。

## 当前基线门槛

T2/T5代码已集成但尚未提交，HEAD仍为T1 1b30bbe。用户此前的本地提交授权仅限T1，D009明确未授权新提交。已准备新的执行包；在新本地基线提交获授权前保持PLAN，不改业务代码。待批准提交范围为已集成T2/T5源代码、测试、依赖锁和交付证据，以及已批准的后续方案/本执行包；排除数据库、虚拟环境、node_modules与构建产物。不推远端。
