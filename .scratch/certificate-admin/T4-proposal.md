# T4 详情与撤销（已确认，等待T2/T5集成）

用户已确认本方案、测试边界及并行分工。依赖由T3改为T2；日期展示复用T5，待T2/T5共同基线集成检查与审查通过后与T3、T6并行。确认原文见 decisions.md 的 D009。

## 推荐技术方案与取舍

- POST /api/certificates/{id}/revoke，沿用X-Actor-Id；无身份401，跨租户与不存在同404。当前无撤销原因要求，使用空body/{}，未知字段422，不增加理由或恢复功能。
- 只允许有效→撤销；首次200返回 {certificate_id,status:"revoked",changed:true}，再次200返回同ID/状态及changed:false。选择200便于UI统一处理，而非第二次409；此接口状态幂等，不引入T3的请求key表。
- 同一 BEGIN IMMEDIATE 事务内检查所属租户、条件更新状态并写REVOKED审计；唯一约束(certificate,event_type)兜底。重复或并发撤销不产生重复审计，不改变首次审计actor与时间。错误回滚状态和审计；忙锁503，可安全重试。
- 详情展示编号、课程、学员、T5当地日期/时间/时区、状态，以及已有公共审计接口返回的事件。保留UTC事实；撤销不改变签发时间。沿用T2已批准的终身唯一：撤销后不重发。
- 有效证书显示撤销按钮；点击先出现确认弹窗，说明不可恢复。确认后禁用重复提交；成功刷新详情、审计和列表；失败保留详情、显示可重试提示。已撤销时只显示状态。
- 取消弹窗不发送请求。身份切换或关闭详情忽略旧响应，不向新身份回填状态；浏览器取消不代表服务端撤销事务已取消。

## 验收与垂直TDD边界

公共边界为真实HTTP+文件SQLite、详情/列表/审计及浏览器操作，一条red→green后再下一条。

1. 首次撤销状态改变且新增恰好一条REVOKED审计，保留ISSUED事件及签发时间。
2. 第二次changed:false；原撤销actor/time不变，审计数不增加；重启后再次撤销同样成立。
3. Bob撤销East返回404；Alice详情/审计证实无副作用。
4. 两个重叠HTTP请求竞争同一证书，最终一条撤销审计；不使用内存库或mock替代事务。
5. 测试夹具制造审计写入失败，HTTP失败后详情仍有效且无REVOKED事件。
6. 浏览器取消确认无请求、确认后刷新、重复提交禁用、失败重试及身份切换隔离。
7. 与T3整合后验证撤销后旧发证key重放不会恢复证书；与T6整合后撤销证书仍包含在导出中。

## 影响与所有权

T4 writer候选路径：backend/app/revocation.py、backend/tests/test_revocation.py、frontend/src/components/certificates/RevokeCertificate.vue、frontend/src/api/revocation.ts、backend/T4-evidence.md。主线程负责路由、CertificateDetail挂接及共同数据库配置。

复用T2审计模型，不修改发证资格、幂等表、日期算法及查询排序；不新增生产认证、恢复/删除接口。回退可移除撤销入口但保留已撤销数据与审计；不能自动把已撤销证书恢复有效。
