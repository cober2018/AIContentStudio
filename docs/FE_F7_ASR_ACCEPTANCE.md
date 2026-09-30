# F7 ASR 建议与显式保存批验收

## 需求与边界

精确已保存 Video v2 Master + 当前项目可见音频/视频版本 → 有界 ASR 建议 → 人工拒绝或接受到本地字幕 → 显式保存不可变 Master 修订。

建议不写 Master，接受仅修改本地字幕并使成片绑定失效。显式保存重新核对 actor/project/unit/current Master/context/runtime、精确来源哈希和实时 model-use 权利；血缘为 `verified_output_match` 或 `subsequently_modified`。不新建 ASR 表、migration、自动 durable save 或 Provider Verification。

来源最大十分钟；最多 1000 非重叠有序字幕、每条 500 字符、全文 100000 字符。actor receipt 15 分钟 TTL，全局 40、每 actor 8、总输出 4 MB；重启/跨 worker 不可读，不冒充持久化。

共享 Provider 单次调用上限两个未结束 worker；30 秒响应期限，unknown 不重试。超时任务可能仍在运行，占用槽位直至终止，不声称取消远端效果。输入授权锁持有至调用结果/响应超时，Provider 自身仍须使用请求携带的 timeout。内部容量不足与外部异常分开，外部 HTTPException/raw diagnostics 不进入 API。

## 文件与启动

- `apps/api/app/services/asr_suggestions.py`：actor receipt、来源/输出验证、保存血缘。
- `apps/api/app/services/provider_calls.py`：单次有界调用；ASR/媒体生成共用。
- `apps/web/src/product/AsrSuggestionPanel.tsx`：Video-only lazy 建议面板。
- `apps/api/tests/test_f7_asr_suggestions.py`：20 个 ASR 定向回归。
- `apps/web/scripts/fe-f7-asr-browser-acceptance.mjs`：隔离真实 WAV/fixture 转录验收。

沿用 API/Vite 依赖与启动，无新依赖。浏览器必须使用 guarded `fe_f7_media_acceptance_server`、独立 `/tmp/aicontent-f7-media.<suffix>/studio.db` 与 media；隔离迁移后启动 18271 API 和 15671 Vite。脚本要求 `F7_ISOLATED_ACCEPTANCE=yes`、`F7_BROWSER_URL=http://127.0.0.1:15671` 与精确 `F7_ACCEPTANCE_DB`。

## 实际门禁

| 验证 | 结果 |
|---|---|
| ASR / 素材接受定向 | 41 passed |
| ASR / 旧 Video / 素材接受 | 111 passed，之后新增异常脱敏回归纳入全套 |
| 全后端最终重跑 | 1291 passed / 2 skipped / 8 existing warnings，52.28s |
| TypeScript/Vite/FE-P1 | PASS |
| `/projects` | 224.84 kB raw / 72.94 kB gzip |
| 公共 Production | 279.65 / 88.98；无 TipTap/XYFlow |
| ASR lazy chunk | 3.30 / 1.97 |
| OpenSpec strict | 30/30 |
| 范围 Ruff / diff-check | PASS |
| 隔离浏览器 | 4 gates，0 page error |
| 独立窄复核 | APPROVE；未代替真实外部验证或 F7 终验 |

独立复核发现并关闭：撤权前调用窗口、历史素材引用不等于当前项目可见性、Provider HTTPException 原样返回秘密。新增负向回归先失败，再修复通过。浏览器首次因列表断言用了 `.length` 而非 `.items.length` 失败，修正脚本后真实重跑。

浏览器证据：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-asr-browser-Q4ZMvk`；隔离 DB/media：`/tmp/aicontent-f7-media.IOrZHJ/`。使用实际 WAV 字节和显式 fixture，未调用真实 ASR、未写 Provider verified。

## 待完成

F7 80/105：真实单次 Image/Video/TTS/ASR adapter 和凭据、Renderer、不可改稿 Publisher、真实账号验证及完整终验仍未完成；F8 尚未 apply。不 push/deploy/生产 migration/canonical sync/archive。既有原始 OpenSpec 包保持原样。
