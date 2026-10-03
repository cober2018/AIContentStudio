# Local MLX ASR subtitles

## 需求背景

用户在2026-10-03确认本机ASR足够：不把视频外发云端，优先复用FinanceOpinionRadar的MLX桥接；MiniMax保留为显式选项。Studio现有字幕建议/校对/接受/Save不重造。

## 目录结构

```text
add-local-mlx-asr/
├── .openspec.yaml
├── proposal.md
├── design.md
├── tasks.md
└── specs/local-asr-subtitles/spec.md
```

## 已完成与TODO

- 已确认本地优先方向、实际Radar桥接/worker合同和Studio接入边界；已产出标准规格和两批四项实施计划。
- 已apply后端Provider与字幕面板；现有本机模型在断网执行器真实WAV/MP4 smoke通过，页面默认本机/云端显式选择/来源缺失禁用通过。用户视频已完成MaterialRevision3→项目共享素材→本机MLX→43条字幕→人工接受→显式保存Master5/v3→刷新/API重启历史回读。
- 本change strict、全部strict34/34与diff-check通过；独立定向SPEC/PLAN复核均Approved。复核后的上限归属说明已补入design/spec：Material上传30MiB，SourceDocument的默认20MiB配置不叠加为ASR限制，既有入口不改。
- 新鲜105项F6D/F6E/material-search定向回归通过；全量后端1660 passed、28 skipped、8 warnings；前端构建/FE-P1、strict34/34、限定Ruff与diff门禁通过。期间发现并修正普通视频素材“公开许可或模型许可二选一、最终render必须公开许可”的兼容边界；没有新增测试代码。Batch B已完成，本change已按用户授权同步canonical并归档。
- 新素材生成后的人工接受与其余F7仍按原change独立验收，不由本次ASR或adapter smoke替代。没有云端付费调用/下载安装/新表/迁移/commit/push/deploy；本change已完成canonical sync并归档。

## 关键设计决策

复用既有Registry/receipt/MaterialRevision/Video Master，0新表/0migration。只固定路径/已缓存模型/断网子进程；本机失败不自动调用MiniMax。首批仍为段级字幕、≤10分钟、来源读取≤30MiB且导入服从现有配置上限；本机最多120秒/单并发，其他Provider30秒不改。权利未知不自动授权，Accept与Save分离。

## 依赖与启动

沿用本地API/Worker与ffmpeg/ffprobe；复用voice-pro现有ARM Python、兼容polyfill、MLX worker及缓存模型。运行时显式配置本机opt-in/受控路径/模型snapshot，禁止客户端路径、启动时下载或安装。缺环境/模型/网络拒绝支持时明确unavailable。

已在私有`backups/local-mlx-asr-eJIgpH/`备份后启用被Git忽略的`apps/api/scripts/startup/runtime.env`本机ASR字段，并限定重启API。不改变CPA默认、签名key、F8身份schema或原素材许可。回滚仅关闭本机opt-in/恢复本次启动配置备份，不删除现有素材和Master历史；本机单并发120秒，原Provider仍30秒。
