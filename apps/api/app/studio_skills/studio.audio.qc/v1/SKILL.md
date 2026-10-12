---
key: studio.audio.qc
version: 1
source_kind: studio_builtin
---

检查精确音频MaterialRevision的真实字节、哈希、MIME和有限时长，复用本机可用媒体工具分析明显爆音、长时间静音和响度。已请求voice、Provider、model、rate必须从原ProviderGenerationTask receipt核对，不能凭人工标签宣称已验证。结果绑定MaterialRevision hash，撤权或替换后失效。不发起隐藏付费调用；ASR对稿只有用户启用且存在精确来源和真实时间对齐证据时才记录verified。仅估计的字幕时间必须标estimated。可听性最终由人工确认，不以合成夹具证明创作质量。
