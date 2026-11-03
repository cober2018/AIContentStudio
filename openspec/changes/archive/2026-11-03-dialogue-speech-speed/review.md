# review：dialogue-speech-speed

## 2026-11-03 审计（审计方）

代码版本：0054c0f + 未提交工作区（9 个文件，见 README「代码位置」）。

### 结论

基本通过，有 1 处缺陷要改：MCP 说明前后矛盾。另有 1 处文档没同步。

### 核对结果

| 项 | 方法 | 结果 |
|---|---|---|
| 导演稿字段校验 | 读 `video_documents.py` diff | speed_percent 只收 50–200 整数，只允许出现在声音段；长度允许差 34 毫秒；不写时哈希不变。符合 |
| 整片换算 1.15 | 作品 94 主稿 #244 在内存里调用 `_rescale(100→115)`，不存库，再过 `canonical_payload` | 117720 → 102365 毫秒（比 1.1500）；镜头时长之和 = 总长；画面轨首尾相接，每段 = 镜头时长；14 段声音都写了 115，截取与放置 × 1.15 最大差 0.45 毫秒，不重叠；字幕、叠字都在总长内；校验通过 |
| 调回 1.0 | 115 → 100 | 所有时间点和原稿最大差 1 毫秒，speed_percent 已去掉 |
| 两端和连调 | 0.8 倍、1.5 倍各调一次；100 → 105 → 110 → 115 连调 | 都能通过校验；连调和一次调到 1.15 最大差 1 毫秒 |
| 不算新导演稿 | 读 `video_chain._keeps_draft` | speech_speed 已登记 |
| 接口 | 线上只读 `GET voiceover`；`PUT voiceover/speed` 发 300 | 作品 94 返回 speech {100, 117720}；300 返回 422 |
| 页面 | 读 `VoiceoverPanel.tsx` / `StoryboardTable.tsx` diff | 只在有声音轨时显示；定稿只读；时长估算对；分镜标「1.15 倍速」 |
| 规则文字 | 读 `video_chain.py`、`sound.md` | 已写变速、音调校正、同步实拍画面同速；sound.md 引用的 beat-and-speed「变速基础」存在 |
| 测试 | 全量 pytest；前端 tsc | 2441 通过、28 跳过、5 个失败，和之前几次记录的 5 个旧失败相同（schema_lifecycle、migrations ×3、plugins），与本次无关；tsc 通过 |

### 缺陷

1. **MCP `save_director_draft` 说明前后矛盾**（`creative_mcp.py:482`）
   - 现状：新加了「speed_percent … so trim length = placement length × speed_percent / 100 — keep it when re-saving」，但后面原来的「and trimmed length must equal placed length」没删。
   - 影响：第三方模型读到两条相反的规则，重存导演稿时可能把用户调的语速去掉，或者不敢写 speed_percent。
   - 改法：删掉后面那句，或改成「trimmed length must equal placed length × speed_percent / 100」。

2. **tasks.md 没打勾**
   - README / progress.md 写着已实施完成，tasks.md 的 10 项仍全是 [ ]。
   - 改法：按实际完成情况勾选。

### 可选建议（不阻塞）

- shot_sources 没有速度字段：变速的实拍镜头，平台第一轮按 shot_sources 估源时间会偏（5 秒镜头中点约偏 0.4 秒）。剪辑清单交上来后按清单的 speed_percent 重算会纠正，所以只影响第一轮提示。
- 实拍作品里个别镜头用 dub_persona 配音时，配音段在非声音轨上：滑块会把它的放置时间压短，但配音本身不变速，可能和下一段挤在一起。作品 94 没有这种镜头。
- 键盘方向键每按一下就存一版主稿（progress 已注明）。
