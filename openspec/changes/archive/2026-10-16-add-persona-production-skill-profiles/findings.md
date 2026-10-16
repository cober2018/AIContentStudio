# 实际发现与待确认决策

## 来源核查

- Hypit有可用的参考分析方法与media/transcribe工具文档；语义分析由Agent完成，输出ANALYSIS/TIMELINE。没有证据支持“完美复刻”或一键训练角色模型。本机运行尚未验证。
- talkcraft现行许可为PolyForm Noncommercial并明确商业使用需作者许可；dbskill为CC BY-NC 4.0。两者价值高不等于可直接纳入日常商业运营。
- aftr是AE控制桥、预设与自动渲染复核循环；其无AE模拟器不等于真实AE渲染。保留现有MCP即可研究其方法。
- shotcraft源码/文档镜头数量口径不一；talkcraft本次实际108个卡片文件。按确切卡片验收，不按介绍数字验收。
- shotcraft音频参考明确承认部分曲目不可反查和SFX来源待考；不能靠代码许可证给捆绑音乐自动授权。
- khazix-writer包含作者身份；WeWrite状态原本是用户目录；chengfeng现版强依赖自有Runtime/Studio/云ASR。必须说明适配差异，不能直接拼接原文。

## 已由用户明确的边界

角色为核心资产；每阶段可多Skill独立开关；音乐按场景、标签可改、可不用；外部Agent执行，平台组织素材与配置；达芬奇主剪，AE按需包装；先科技、生活稍后、数字人作为后续能力。

## 已确认方案

用现有版本化资产承载文字/图片/视频风格；Hypit只做可选参考分析；先少量方法与三类AE镜头试验；talkcraft/dbskill不作为当前商业依赖；用同输入对照与新主题完整片验证。具体选择不自动变成角色默认，需实际作品采纳。

## 2026-10-16补充：专业软件组合操作

- 用户进一步明确Remotion/HyperFrames方法需要适配到AE/Resolve；新给三个仓库只作为原任务选型补充，原22项不扩张。
- 三个仓库根许可均MIT。yumehiko适合场景组合/稳定ID/局部修改；odaiouattara适合Resolve操作组合；ChaiWithJai更贴近专业后期判断。
- Chai的auto_silence_cut只报告片段间空隙；odaiouattara脚本有首个子串匹配和按整批计成功的逻辑，适配时需改用精确素材与实际返回回读。
- 当前AE工具目录已有组合工具保存/搜索/重放接口；无需新建平行工具库。读取执行指南遇到会话ID失效，本轮无AE运行验证。
- Resolve当前API索引有音量、Dialogue Leveler、归一化与Fairlight预设接口；本轮没查得Ducker/EQ同等直接调用。GUI方法需与脚本可用性分开验收。

## 实施发现（2026-10-16）

- 实际素材库页面是 `apps/web/src/pages/Materials.tsx`；Assets.tsx负责批准成品与交付。音乐标签编辑复用Materials。
- AE MCP保存空工程后需要重新绑定新工程路径；桌面旧会话失效不等于AE不可执行。
- 首次渲染与编辑共用撤销组导致警告。改用scheduleTask在调用返回、撤销组结束后启动渲染，独立读回DONE；未再出现弹窗。未知结果先回读，不重发。
- Resolve实测源区间24到71产生47帧，24到72产生48帧；必须回读实际时长，不能照搬上游加一算法。完整4秒24fps回片为96帧。
- 方法合同拒绝HTTP URL形式；候选保留repository/commit/相对文件/hash，可点击固定URL仍在research.md，未放宽原安全合同。
- AE三合成工程实际重新打开，图层分别8/15/5，1280×720、24fps、4秒，缺失媒体为0。Resolve DRP实际导入新工程，三片段在86400至86688连续排列。

## 试验标准采纳

2026-10-16用户采纳首版科技风格卡用于新主题试验；采纳规则不等于最终默认或完整样片质量通过。参考素材、隔离试用方法和音乐均保留精确版本及来源。

- 新主题同题同模型三组对照都需要修改，最终采用关闭版为修订底稿，没有凭方法数量选择默认。平台把角色已采纳风格与可选写作方法分开冻结，关闭写作方法后可信风格仍保留。
- 旁白、字幕、镜头共用一份帧级编辑映射；ASR同音字由已审核文案校正。时标是估计对齐，未宣称直接试听。
- AE工程重新打开后即使路径相同也须重新绑定；先完成真实重开，再读缺失媒体与合成参数，不能以文件存在代替工程验收。

## 原生导出与回收发现

- 当前Resolve构建SetTrackEnable(False)曾返回true但回读仍开启；实际无配乐验证用SetClipEnabled(False)逐个回读并比较真实导出PCM，不能只信调用布尔值。
- Resolve原生H264/AAC的47秒画面带47.083秒容器尾垫，超出平台一帧容差。最小交接修正为不重编码的stream-copy限时封装；解码画面完全不变、保留PCM完全不变，原生工程/原导出保留。原生FLAC精确47秒也已实测，但未作为正常网页交付默认。
- 原生项目仍是本机依赖交接：Resolve依赖持久目录同字节素材；AEP保留旧技术probe的持久参考PNG依赖。不能声称是自包含可移植工程包。

## 正式主稿绑定发现的遗漏

- 正式8个output接受后，本地主稿的render_attestation仍被MediaMasterAdapter无条件公开权限要求拒绝。既有content_masters.local_final_use_allowed已验证同owner/project/unit、accepted final及设计内容一致，资产绑定阶段通过；后续render snapshot未复用此判断，形成真实路径不一致。
- canonical web-video-production-handoff的既有Final delivery要求已明确允许该本地绑定，保留Candidate/发布公开门禁。本次仅补齐渲染确认与可用性门禁的一致性，沿用原批准范围，不扩展任意私有素材或图文路径。

## 首版默认与使用边界已落实

- 科技Persona2 v4为正式首版，保留旧v1–v3；写作3项候选保留但默认关闭，其他9阶段各启用一项已验证方法。此选择来自实际对照与用户采纳，不推导为方法越多越好。
- 正式Project7/Unit13/Master39已绑定本地成片；publicfalse保持，正常checks中的证据/rights blocker及缺channel适配不影响已授权本地使用，也不被抹成公开发布通过。
- 正常checks会调用既有Gemini语义身份检查并可能input_truncated；回执明确partial。没有新内容生成/媒体重渲染不等于完全没有模型调用。
