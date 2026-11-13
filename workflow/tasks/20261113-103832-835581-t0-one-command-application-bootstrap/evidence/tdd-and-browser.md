# T0 实施证据

日期：2026-11-13，Asia/Shanghai。以下是执行摘要，不是 AI 原始会话导出。

## 测试驱动记录

1. 初始 FastAPI 空应用：test_health_reports_process_ready 失败，实际 404 / 期望 200；增加健康接口后 1 passed。
2. 增加根页面契约测试：实际 404 / 期望 200；接入 Vue 构建与静态托管后 2 passed。
3. 增加真实启动测试：公开入口 scripts/start.mjs 不存在导致失败；实现入口后干净副本测试 1 passed（7.99s）。
4. 对已有行为补充未知 API、重启、终止父进程、端口冲突和锁文件漂移回归；没有为这些已正确行为伪造红灯。
5. node scripts/check.mjs：类型检查与 Vite 构建通过，HTTP 3 passed（0.55s），真实进程 4 passed（32.84s）。最终 authoritative 检查以 workflow verify 输出为准。

FastAPI 新版 TestClient 对 HTTPX 发出弃用提示；改用批准的 HTTPX AsyncClient + ASGITransport，无新增测试依赖。HTTP 测试不模拟内部协作者。

## 浏览器验收

使用真实 Chrome、http://127.0.0.1:8010，未注入应用状态：

- 页面显示“服务已连接”，页面截图观察正常。
- 只停止本次启动的 Uvicorn 进程，点击“重新检查”；显示“暂时无法连接服务，请检查服务是否启动后重试。”
- 错误态截图保存为 browser-error.png。
- 使用同一公开命令重启后点击“重新检查”；恢复“服务已连接”。
- 恢复态 accessibility snapshot 已观察；保存恢复态 PNG 时浏览器截图调用超时，因此不宣称有恢复态截图文件。

## 审查修正

Standards 与 Spec 独立审查发现直接 Uvicorn 不监听父进程 stdin EOF；新增 app/serve.py 监测父进程管道，launcher 关闭或意外退出会使服务退出；POSIX 信号增加 SIGHUP 和有界 SIGKILL 兜底。现有 Windows 生命周期测试此前已通过；此修正来自代码审查，不虚构 POSIX 实测。文档、正式检查配置和浏览器记录在审查期间补齐；重新验证与复审结果另见 workflow 证据。

首次正式 verify 的四项检查全部通过、scope violations 为 0，但 AC2 引用目录而非具体文件，记录被引擎拒绝，导致验收映射不完整。已修正引用并重跑验证，不将第一次整体 FAIL 记为通过。

额外使用真实 PTY 发送 Ctrl+C：观察到 Uvicorn 完整 shutdown 和退出；KeyboardInterrupt traceback 属于正常中断，入口已处理以避免误导用户。自动生命周期测试使用 Ctrl+Break，与此实操分别记录。

## 影响与限制

实测 Windows、Node 24.18.0、Python 3.14.6。Linux/macOS 未实测。未生成业务数据库、证书功能或第 6 节答案。未提交、发布、部署。业务验收需用户另行确认。
