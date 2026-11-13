# AI活动原始条目交付

## 交付范围与来源

本地交付提供从原始JSONL逐条提取的可见记录，不是重写的摘要。覆盖当前主会话、关联fork及全部已发现实现/审查子代理，共15份来源：1个主会话、1个fork、13个子代理。已核对日志中的13个spawn_agent任务名，均能匹配到来源文件。

根会话：01a1d2b6-3a4e-7620-84c2-42217e3aadd8。fork：01a1d2e6-9c25-7792-a495-5aa45b2ccf45。子代理包括T0两项审查、T1前后端与两项审查、T2/T5实现、T3/T4/T6实现、T7两项审查。关系依据session_meta的parent_thread_id和forked_from_id，未按目录名猜测；T0来源起始目录不同，仍已纳入。

原文件留在本机Codex sessions目录，只读、不修改、不入Git。已扫描会话元数据确认本任务关系树；本项目15份日志均位于2026/11/13目录。全局历史目录存在无关的重复ID，导出使用该日期目录；重复ID会显式失败，不静默覆盖。

## 导出结构

- transcripts/<session-id>.jsonl：用户消息、助手可见回复、工具调用/结果。保留来源行号、原始时间、正文、调用ID、次序；不把失败改写成成功。
- dispositions/<session-id>.json：原文件每一行的处理清单，记录导出或排除、嵌套字段/内容项过滤路径及凭据脱敏计数。
- manifest.json：来源关系、原文件名、读取字节前缀长度与SHA-256、首末时间、原行数、导出/排除条数、未完整末行字节数，以及所有交付文件的大小与SHA-256。
- manifest.sha256：清单自身校验值。校验和证明文件一致性，不提供数字签名。

完整性定义为：清单所列来源在各自明确字节截止点之前的全部行均有处置记录，全部可交付条目均已提取。工具会从原始前缀重新提取并逐条比对，且验证关系来源、文件集合和hash。运行中的会话会继续增长；截止点之后的消息（包括最终交付回复）不属于该快照，可用同一命令创建新快照。

## 明确排除与脱敏

系统/开发者指令、隐藏推理、加密内部字段、运行时代理通信、运行时状态与压缩摘要不进入交付副本；重复事件流不冒充新增对话。原始内部日志不是可直接交付的公开记录，因此不宣称逐字节完整原件导出。过滤项以来源行号和字段名记录，不泄露被排除的内部正文。

可见文本中的已识别Bearer凭据、常见API token、密码/API key/cookie赋值和私钥块替换为[REDACTED]，逐行记次数。普通正文及工具失败结果保留。自动识别不是穷尽性秘密审计；材料仍仅本地保存，外部发布应另行审查。机器路径和任务会话ID作为来源信息保留。

这补齐了T7本地截止点范围的可交付AI活动证据，不等于提供内部推理，也不声称满足限时考试或用户业务验收。

## 复现与来源校验

在项目根目录运行（输出目录必须尚不存在）：

```powershell
backend/.venv/Scripts/python.exe scripts/export_ai_evidence.py export --sessions C:/Users/admin/.codex/sessions/2026/11/13 --root 01a1d2b6-3a4e-7620-84c2-42217e3aadd8 --output .smoke/delivery/ai-evidence-new
backend/.venv/Scripts/python.exe scripts/export_ai_evidence.py verify --sessions C:/Users/admin/.codex/sessions/2026/11/13 --output .smoke/delivery/ai-evidence-new
```

接收者没有原日志时可省略verify的--sessions，仅校验交付文件。原日志继续追加允许通过；原有字节前缀被修改会失败。导出不读取无关会话正文；发现关系所需的其他会话首行元数据仅在本地读取。

docs/acceptance.md和workflow/tasks仍是执行证据索引；它们与逐条导出用途不同，不能相互冒充。
