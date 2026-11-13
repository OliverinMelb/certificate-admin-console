# T0 一条命令启动应用

状态：用户已确认 T0 技术方案及测试边界，允许进入实现。用户原话：“确认 T0 的方案和测试边界，再确认 T1 的方案。”本文是 T0 的有限执行规格；根 spec.md 的产品需求保持权威。T1 尚未获实现授权。

## 目标与范围

在独立仓库建立可重复启动的最小前后端闭环：浏览器打开页面，页面从同源 FastAPI 获取健康状态。依赖隔离与锁定，启动、关闭和重启行为可验证。

本项不实现身份、证书表、演示业务数据、数据库事务、列表、发证、撤销、时区或 CSV。SQLite 选型保持不变，数据库文件与 seed 在 T1 接入同一启动入口。因此 T0 通过不代表原题完整启动验收通过。

## 技术提案

| 决策 | 推荐 | 取舍 |
| --- | --- | --- |
| 前端 | Vue 3 + TypeScript + Vite，script setup / Composition API | 类型检查与简单构建；本阶段原生 CSS，无组件库、Router、Pinia |
| 运行时 | Node 24；Python 3.14，记录核验后的补丁版本 | 复用本机运行时，避免无依据下载另一版本；依赖不兼容时停止并回报，不擅自降级 |
| JS 依赖 | npm + package-lock.json；安装用 npm ci | 使用现有 npm；不添加第二套 JS 包管理器 |
| Python 依赖 | uv + backend/pyproject.toml + backend/uv.lock；uv sync --locked | 锁文件不匹配即失败，正常启动不重写锁；backend/.venv 隔离 |
| 后端 | FastAPI + Uvicorn；仅健康 API 与静态文件 | 同源单服务，不需要 CORS、Docker、代理或开发服务进程 |
| 启动入口 | node scripts/start.mjs | Node 已是前端前置依赖；跨平台编排，避免仅支持 PowerShell |
| 检查入口 | node scripts/check.mjs | 类型检查、构建、pytest 和真实进程 smoke；独立检查输出对应 workflow 配置 |
| 测试 | pytest + HTTPX，临时目录；浏览器实操验收页面 | 测公共边界，不 mock 内部启动函数；T0 不加 Playwright 浏览器下载或 Vue 单元测试栈 |

具体包版本在批准后通过兼容性解析选择并锁定；不使用启动时自动升级。Python、Node、npm、uv 是 README 声明的前置工具；启动脚本缺工具时给出明确错误，不修改全局环境。

## 建议文件边界

frontend/：package.json、package-lock.json、Vite/TS 配置、src/App.vue、src/components/ServiceStatus.vue。

backend/：pyproject.toml、uv.lock、app/main.py、tests/。应用使用可创建实例的入口，便于隔离测试。

scripts/：start.mjs、check.mjs；tests/：真实进程 smoke。根目录记录运行时版本、忽略规则、README；workflow/config.json 配置真实检查。

App.vue 负责页面组合；ServiceStatus.vue 负责请求与展示 loading/ready/error。通过同源 /api/health 读取状态，使用 fetch，不增加 HTTP 客户端依赖。

## 启动契约

默认命令：node scripts/start.mjs；可选 --port，用于端口冲突处理和独立 smoke。

1. 验证前置工具和路径；工作目录由脚本路径解析，不依赖调用者当前目录。
2. npm ci、uv sync --locked；失败则停止，输出步骤和非零退出码。
3. 前端类型检查和构建；不成功则不启动服务。
4. 直接调用项目 venv 的 Python 启动一个 Uvicorn 进程；绑定 127.0.0.1，默认端口 8000，不开启 reload。
5. 展示实际访问地址；不自动打开浏览器或另开控制台。
6. Ctrl+C/终止后只清理本脚本拥有的子进程；不得杀死占用端口的其他进程。

首次运行需要访问声明的依赖源；不承诺首次离线安装。重复执行仍依据锁文件安装/同步，不破坏未来的数据目录。npm ci 会重建本项目 node_modules，换取更简单的依赖一致性。

## HTTP 契约

- GET /api/health → 200，JSON {"status":"ok"}，表示进程健康，不声称数据库就绪。
- GET / → 200，HTML；引用的前端构建资源可访问。
- 未知 /api 路由 → 404，不能落入 SPA HTML fallback。
- 页面显示请求中的状态、服务可用状态或可理解的错误；此原型允许一个小状态组件负责自身请求。

## 测试边界及验收

| ID | 边界 | 通过标准 |
| --- | --- | --- |
| T0-AC1 | HTTP API | /api/health 返回固定契约；未知 API 404 |
| T0-AC2 | 构建与 HTTP 静态资源 | vue-tsc 与 Vite 构建通过；真实服务根页面及脚本资源成功返回 |
| T0-AC3 | 真实启动进程 | 无 node_modules/.venv/dist 的隔离副本，在已具备前置工具的机器上，一条命令安装、构建并可请求健康接口 |
| T0-AC4 | 进程生命周期 | 停止后任务子进程退出、端口释放；同一目录重启成功；端口冲突时失败且不终止原占用者 |
| T0-AC5 | 真实浏览器 | 页面正常显示、健康请求成功；请求失败能显示错误；不以静态 HTML 200 代替页面运行证据 |
| T0-AC6 | 影响范围 | 所有依赖与产物位于项目或测试隔离目录/包管理器正常缓存；不修改 ComfyUI、全局包、原始 PDF；正常启动不修改锁文件 |

TDD 按 AC1 → AC2/AC3 → AC4 的可观察行为逐条推进：先记录因缺失目标行为而失败的测试，再做最小实现。干净启动使用公开入口与真实 HTTP；测试准备可以复用系统包缓存，不等于测试断网安装。只清理测试自己创建并验证路径的临时目录。

浏览器加载和错误态在功能形成后实操验收，不为文案、目录存在或内部函数调用次数编写镜像测试。测试命名和预期来源于以上契约。平台实测首先为 Windows；未在 Linux/macOS 运行不得声称这些平台通过。

## 交付与证据

README 补充前置条件、启动/验证命令与 T0 限制。workflow 配置分开记录前端类型/构建、后端接口、启动 smoke 检查；浏览器验收记录实际操作和结果。当前已有的 git-diff-check 不能替代上述验证。

不提交或发布。批准只允许 T0；完成后先报告结果，再呈现 T1 的方案。全局其他待决策项保持未确认。

## 资料

- Vite 入门与 Node 要求：https://vite.dev/guide/
- uv 锁定与同步：https://docs.astral.sh/uv/concepts/projects/sync/
- uv Python 版本管理：https://docs.astral.sh/uv/concepts/python-versions/
