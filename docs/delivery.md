# T7 本地交付清单

T0～T6已完成本地技术验收。T7的文档、交付包和包内启动核对按用户批准执行；关联AI可见原始条目以固定截止点快照单独交付，用户业务验收仍单独跟踪。无远端推送、部署或书面题答案。

## 交付组成

- 源码：frontend、backend、scripts、tests，以及项目版本声明和依赖锁文件。
- 使用说明：README.md；规格与决策：spec.md、tasks.md、decisions.md。
- 验收入口：docs/acceptance.md及其引用的workflow执行证据、真实浏览器记录和性能结果。
- AI材料说明：docs/ai-evidence.md。此说明是索引；逐条导出作为独立AI证据附件，不混入Git源码包。
- ZIP内DELIVERY-MANIFEST.json列出每个文件的字节数及SHA-256；ZIP旁的.sha256校验整个压缩包。
- 排除依赖、构建缓存、运行数据库、.env、原始JSONL会话及其他项目文件。原始PDF继续保留在用户原位置。

## 演示顺序

1. 解压到新目录，按README准备Node 24、Python 3.14.6和uv，在根目录运行 `node scripts/start.mjs`。首次安装需要网络。
2. 打开 http://127.0.0.1:8000 ，选择Alice，查看East列表，搜索Alex，切换排序和分页；查看详情和租户时区。
3. 选择Safety 101批量发证；观察逐人issued/skipped/failed。默认新库第一次有1名合格学员获得证书；再次提交不新增证书。
4. 查看新证书及ISSUED审计；确认撤销并检查状态和REVOKED审计。取消确认不得发起撤销。
5. 保留搜索和排序，下载CSV，检查四列、当地日期和全部匹配记录；撤销项仍在导出中。
6. 切换Bob，确认只有West数据。使用README中的跨租户HTTP请求，预期404。
7. 同key重放、并发、响应丢失重试和十万行性能按docs/acceptance.md中的独立测试及历史浏览器证据核对；普通演示不声称覆盖这些故障场景。

演示会改变解压目录自己的数据库，不能据此假设后续仍有初始12/4条数据。不要删除用户已有库；需要重演时使用另一个全新解压目录。

## 打包与校验

从干净提交打包；输出放在已忽略的.smoke目录，每次使用新文件名：

```powershell
backend/.venv/Scripts/python.exe scripts/package_delivery.py build .smoke/delivery/certificate-admin-console-t7-source.zip
backend/.venv/Scripts/python.exe scripts/package_delivery.py verify .smoke/delivery/certificate-admin-console-t7-source.zip
```

预提交验证可加 `--working-tree`，清单会明确标为未提交快照。最终包从干净提交重建，不将预提交快照冒充提交产物。校验和提供完整性检查，不提供签名或来源认证。

## 验收范围

复用已有A1～A7证据，不重复十万行实验。最终ZIP解压后实际执行启动命令，验证首页与JS资源、健康检查、两租户列表及跨租户404；这是HTTP启动冒烟，不冒充新的浏览器交互验收。原浏览器记录继续有效，因为本轮不改变业务源码。

本轮仅文档与独立打包脚本；不改变接口、数据库、身份、依赖锁文件、运行时或前端行为。回退本轮提交即可移除交付工具，不影响已有用户数据库。

已知限制见README及docs/acceptance.md。仅Windows实测；T7可交付AI条目覆盖范围、过滤与截止点见AI证据说明；不宣称内部原始日志或完整考试交付；用户业务验收未被技术检查替代。

## AI证据附件

最终本地交付由源码ZIP、AI证据ZIP、各自SHA-256及总清单组成。AI附件含transcripts、dispositions、manifest及其校验值；从原日志提取并逐条校验，不纳入Git。源码清单的original_ai_export_complete=false专指源码ZIP不含逐字节内部日志，并不表示另附的可见记录快照缺失。

## 本地组合包复现（PowerShell）

先按上文生成源码ZIP，并按AI说明导出/验证一个新目录。以下命令从项目根目录运行，文件名不得与已有交付覆盖；当前实际交付使用ai-evidence-final与certificate-admin-console-t7-source.zip：

```powershell
# 前置：已生成并验证 .smoke/delivery/ai-evidence-final
backend/.venv/Scripts/python.exe -m zipfile -c .smoke/delivery/certificate-admin-console-t7-ai.zip .smoke/delivery/ai-evidence-final
$sourceZip = '.smoke/delivery/certificate-admin-console-t7-source.zip'
$aiZip = '.smoke/delivery/certificate-admin-console-t7-ai.zip'
$sourceHash = (Get-FileHash -LiteralPath $sourceZip -Algorithm SHA256).Hash.ToLowerInvariant()
$aiHash = (Get-FileHash -LiteralPath $aiZip -Algorithm SHA256).Hash.ToLowerInvariant()
$aiHash + '  ' + (Split-Path $aiZip -Leaf) | Set-Content -LiteralPath ($aiZip + '.sha256') -Encoding ascii
[ordered]@{ source_commit = (git rev-parse HEAD); source_zip = (Split-Path $sourceZip -Leaf); source_sha256 = $sourceHash; ai_zip = (Split-Path $aiZip -Leaf); ai_sha256 = $aiHash; scope = 'visible records at manifest byte cutoffs; internal records excluded' } | ConvertTo-Json | Set-Content .smoke/delivery/t7-delivery-manifest.json -Encoding UTF8
backend/.venv/Scripts/python.exe -m zipfile -c .smoke/delivery/certificate-admin-console-t7-complete.zip .smoke/delivery/certificate-admin-console-t7-source.zip .smoke/delivery/certificate-admin-console-t7-source.zip.sha256 .smoke/delivery/certificate-admin-console-t7-ai.zip .smoke/delivery/certificate-admin-console-t7-ai.zip.sha256 .smoke/delivery/t7-delivery-manifest.json
```

解压组合包，先将两个ZIP的Get-FileHash值与总清单比对。源码ZIP使用package_delivery.py verify；AI ZIP解压到新目录后，使用export_ai_evidence.py verify --output指向其中的ai-evidence-final目录，若有原始sessions可加--sessions做来源回放验证。源码和AI附件必须分别验证，不能只依赖ZIP文件名。
