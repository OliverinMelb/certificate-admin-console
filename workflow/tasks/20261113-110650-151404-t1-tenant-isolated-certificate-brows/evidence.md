# T1 实施证据

## 起点

三个原生 worktree 均从 a9ee16346692aee0d5ca47362909bc9f41b28edd 开始，开始时干净。backend/frontend writer 通过 assign-writer 登记；主线程在 verification worktree 执行测试与集成，路径和顺序见 spec。

用户原话：“确认 T1 的方案、测试边界和并行分工，用我的workflow并行开发”。plan 已确认并进入 EXECUTE。

## 验收驱动

主线程扩展 tests/test_startup.py 的已有干净启动检查，要求一条命令启动后有演示身份、12条 East / 4条 West 证书、跨租户详情404，并在重启后保持相同结果。基线运行：1 failed / 3 deselected，13.03秒；失败原因是 /api/actors 实际404、期望200。对应实现由后端 writer 逐条HTTP TDD推进，集成后再验证。

## 浏览器验收方法

tests/browser_proxy.py 仅在验收时使用，绑定回环地址、转发真实后端。normal 模式不改响应；slow-alice 对 Alice 请求延迟2秒；fail 对 API 返回503。用于真实页面点击和选择操作验证 loading、身份切换及重试。它不被应用或启动入口引用，不作为生产功能，不替代接口测试。

## 实现与集成

后端七轮逐项HTTP红绿验证及重启保留回归完成；另发现极大页码导致SQLite整数溢出，使用 page=9223372036854775807 真实HTTP复现 OverflowError 后修复为超出总数直接返回空列表。最终目标测试9 passed，见 backend/T1-evidence.md。

前端 typecheck/build 通过，未增加依赖或伪造浏览器测试证据，见 frontend/T1-evidence.md。两个writer均停止写入后，主线程从同一base按后端→前端顺序复制限定变更文件，未覆盖其他目录，未创建提交。

## 浏览器已观察

真实 Chrome 经本地代理转发实际应用数据：East初始12条；每页5条→第2/3页；搜索Alex→2条且页码回到1；EAST-001只读详情显示正确ID/课程/UTC时间；Escape关闭。

slow-alice 模式下先选Bob，再选Alice观察课程/证书loading，再立即选Bob；延迟响应返回后仍为West4条，见 browser-tenant-race.txt。无匹配查询的空状态见 browser-empty.txt。fail模式返回503后列表显示错误和重试按钮，见 browser-error.txt。

选择控件最初使用getByLabel遇到工具定位失败；读取实际DOM后改用getByRole('combobox')成功，不属于应用功能失败。其余结果与正式验证、独立审查在后续记录。

恢复 normal 后点击重试，West Alex 查询返回2条；清空搜索返回4条。降序实际行顺序为 WEST-004、003、002、001。slow-alice 下打开详情观察 loading，关闭并切换 Bob；迟到详情未重新打开，最终仍为 West4条。最终浏览器快照与截图见 browser-ready.txt / browser-ready.png。

## 正式集成验证

workflow verify 首次正式运行 PASS：frontend-types、frontend-build、12个HTTP测试、4个启动/进程测试全部通过；启动检查37.49秒，完整检查约42秒。证据见 verification/20261113-112035-169074.json。存在1条锁定依赖的 Starlette TestClient 弃用警告，不影响结果。浏览器观察为人工工具验收，不计入自动测试数量。

## 独立审查与并发交接

Spec reviewer 与 Standards reviewer 均未发现 T1 阻断问题。前者核查参数化租户隔离、字面搜索、极大页码、六表外键和事务 seed；后者核查 Vue 每资源取消/代次保护、身份切换清理、详情关闭和测试代理边界。没有重复全量检查。

非阻断说明：正式验证还包含 backend/app/serve.py 的 stdin 读取退出修复及 tests/test_startup.py 的对应检查，此为 T0 启动回归修复，不属于 backend writer 的 T1 文件交付清单。初始化中途失败回滚与多进程首次建库争用未专项实测；本轮运行平台仅 Windows。X-Actor-Id 是演示身份协议。

审查期间发现其他窗口正在同一目录更新 spec.md、tasks.md、decisions.md 与 T2/T5 计划，保留其变更。本线程不将这些后续变化算作上述版本已验证，也不覆盖其他窗口状态。T1 代码审查通过，但当前 workspace 指纹已变化，因此本线程暂不执行 workflow review/close 的状态迁移；后续集成者应在稳定工作区完成 freshness 检查后关闭。未提交或推送 T1。
