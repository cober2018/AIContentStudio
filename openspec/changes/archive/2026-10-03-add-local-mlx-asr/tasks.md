## 1. Batch A — local runtime and existing Product flow

- [x] 1.1 移植Radar最小MLX桥接为`local.mlx_whisper@1`并接Registry/受控opt-in；实现固定离线路径/缓存模型、WAV/MP4音轨、实际runtime指纹、有界私有临时文件/输出/进程回收及本地120秒/单并发，其他Provider保持30秒；无依赖安装、云端请求、表或migration。
- [x] 1.2 接现有ASR建议API/字幕面板：安全本地/云端标签及不可用原因，本机可用才默认选本机，缺失留空不自动上云；保留MiniMax显式选项、精确来源/权利/当前Master/receipt/CAS校验、接受仅改本地字幕和显式append-only保存，不改CPA或既有全局路由。

## 2. Batch B — real acceptance, compatibility and lifecycle handoff

- [x] 2.1 用用户提供的真实本地MP4音轨跑通页面请求→43条字幕预览/校对→人工接受→显式保存Master5/v3→刷新/API重启读历史，核对MaterialRevision3、source hash、local runtime fingerprint与`verified_output_match` provenance；未公开发布，public rights保持false。
- [x] 2.2 跑完新鲜后端相关回归、TS/Vite与FE-P1、OpenSpec strict、范围lint/diff及最终独立复核；更新README、task_plan/progress/findings及实际剩余F7边界；已按用户授权同步`local-asr-subtitles`主规格并归档本change。不归档/提交其他dirty内容、不推送/部署/迁移/发布，也不声称新生成接受或全F7完成。

## Apply gate

2026-10-03用户已对当前标准提案明确授权进入apply；直接main、两批执行。实现和真实验收完成前不勾任务，不拆成百项小任务。

2026-10-03阶段结果：Batch A实现及七源码限定安全复核APPROVE、241定向/1660全量既有后端、Web/FE-P1及strict34/34通过；真实离线adapter WAV/MP4与本机页面引擎选择已核对。当前2/4；Batch B的许可明确用户素材→页面字幕接受/保存/刷新/重启尚未完成，不以adapter smoke或空Master替代、不提前归档。
