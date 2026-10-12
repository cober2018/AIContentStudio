# Creative Orchestration：本机正式启用

## 需求与当前状态

2026-10-05用户授权在这台电脑上完整使用已验收新版。本轮执行配套备份、正式SQLite增量升级、原API/Worker恢复、loopback Web启动、私有MCP配置和正式联通验收。不新增业务代码、表设计、依赖、服务器部署或登录体系。

**LOCAL_ENABLED**：`http://127.0.0.1:5173/` 默认进入新版Home；API为 `http://127.0.0.1:8000`。代码仍为本地main@341ead8加未提交change；OpenSpec147/147实施验收完成，canonical同步/归档与本地提交未执行。

## 正式资源与目录

| 资源 | 实际位置/状态 |
| --- | --- |
| SQLite | `apps/api/content_studio.db`，head `aco000000001` |
| 本地素材 | `apps/api/app/media`，路径不变 |
| 运行配置 | `apps/api/scripts/startup/runtime.env`，ignored且0600；不在文档复制内容 |
| API | 原launchd `com.aicontent.api`，仅127.0.0.1:8000 |
| Worker/beat | 原launchd `com.aicontent.worker`，原队列、Redis DB2、并发1及beat保持 |
| Web | 原npm/Vite启动方式，显式127.0.0.1:5173；未新增登录自启daemon |
| MCP | 同API进程 `/api/v1/creative-mcp`，Bearer且绑定原激活admin用户1 |
| 日常/旧功能 | 九个日常入口；Settings→高级运行环境保留十五个兼容入口和历史URL |

继续沿用APP_ENV=development的技术行为和header身份，不把“正式使用”错误地等同APP_ENV=production/JWT/MinIO。

## 本轮执行与验证

1. 原Worker真实active/reserved/scheduled均0，停止原API/Worker进入停写窗口。旧ContentJob的3条queued记录未重发；既有97条外键异常不借迁移修复。
2. 私有0700快照 `backups/creative-local-enable-a63DyjDV/` 保存SQLite在线 `before.db`、完整32MB `media-full/`、引用素材hash副本 `media/`、原运行配置及既有签名密钥文件（存在时）。私有凭据不输出、不入Git。
3. `rehearsal.db` 从同一快照恢复，明确升级aco000000001→降回f7d000000001→再升级。83张历史表/5145行全部原始列hash不变，97条外键异常集合不变，integrity ok。
4. 正式升级依次执行既有f8a000000001和aco000000001；f8a仅新增两列nullable身份字段，不改变原身份行为。升级后及原服务重启后都验证相同83表/5145行原始列hash、FK集合、integrity，完全一致。引用素材7条/5份字节hash再次通过。
5. 只在原私有配置追加REQUIRED_SCHEMA_HEAD、MCP owner和随机token；保留原模型路由、凭据、媒体根和Worker拓扑。API/Worker已通过原LaunchAgents恢复；8000/5173实际监听地址均为127.0.0.1。
6. readiness HTTP200、ready=true、reasons=[]；Worker真实ping成功且active/reserved/scheduled仍0。私有HTTP MCP initialize/initialized、15工具、status与owned context读取成功。
7. 已安装Codex app-server实际连接正式MCP并读取项目1/单元3的资源，Bearer认证、15工具、1资源/4模板，0模型turn和全局配置写入。此为真实客户端读取，不表示本聊天工具目录或所有Agent全局配置已自动更新；runtimeStatus=null不推断成额外验证。
8. 实际浏览器打开九个日常入口、Settings十五个兼容目录、运行状态、方法库、Text Master及创意执行面板。新方法/执行列表为空是原正式库没有新记录，不是伪造成功。视频Master5仍stale，文字Master9仍current，原素材权利/检查/身份阻断保留。
9. 启用后另存 `enabled.db` 和0600的 `runtime.env.enabled`，源/备份integrity均ok；素材未变，与同快照media-full配套。升级前库配原runtime.env.before，升级后库配runtime.env.enabled，不能把两组head配置混用。没有创建示例或写业务对象、模型请求、公众号草稿、公开发布、push。
10. 最后再验正式历史行/完整性与readiness/Web HTTP200；OpenSpec strict35/35、git diff--check、29个owned untracked文档空白/冲突标记检查、F8十三文件hash通过。浏览器console error为0，启用首页凭证为快照目录内 `new-home.jpg`。本轮没有业务代码改动，未把此前1660项后端/构建门禁冒充本轮重新运行。

完整“结果提交→人工接受→MaterialRevision→显式Master/Variant→Candidate→Review→本地包”写链与三形态验收仍以既有隔离验收为证，本轮不冒充在正式库重新执行了它们。

## 日常启动、停止与日志

API/Worker沿用原LaunchAgents：已加载时用 `launchctl kickstart -k gui/$(id -u)/com.aicontent.api` 或对应worker；已卸载时通过各自 `~/Library/LaunchAgents/com.aicontent.*.plist` bootstrap。不要同时再运行第二个API/Worker。

Web在仓库根执行 `make dev-web` 是原入口；需要明确loopback和目标时，在apps/web执行 `AI_STUDIO_API_TARGET=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`。当前Web已经运行，不再启动重复5173实例。

停写维护时针对上述两个确切launchd label执行bootout；Web在其终端Ctrl-C。日志使用现有 `logs/api.log`、`logs/worker.log` 和Web终端，不使用宽泛pkill来停止无关任务。不打印私有配置、token或原始供应商响应来排查。

## 备份与恢复边界

沿用 `docs/runbooks/backup-restore.md` 和现有SQLite在线backup/素材hash脚本。数据库必须与同一快照的完整本地素材及必要私有签名配置配套；单独一个db文件不是完整恢复包。

本轮快照含升级前与升级后数据库，不做自动删除。恢复先在新路径验证schema、历史行、素材hash和完整性，再停写且保全当前库。新域已有正式写入后不得盲目downgrade或用旧快照覆盖；回退需要明确范围和恢复授权。

## 已完成与待办

- 本机正式启用、配套备份/恢复演练、历史保全、loopback健康、正式MCP/实际Codex只读联通已完成。
- canonical同步/归档、本地提交尚未执行；F8十三个owned文件原SHA256保持一致。
- 既有外键异常是保留的历史数据债，不表示本次升级新增异常；如需修复应单独确定范围。
- 历史内容的stale/rights/check/identity风险需按正常创作流程明确处理，不能用部署验收替代稿件批准。
- 真实专业工具自动化pilot和生成质量不在第一版范围；本地ZIP不等于公开发布。

本轮使用skills：using-superpowers、writing-plans、executing-plans、openspec-apply-change、verification-before-completion。
