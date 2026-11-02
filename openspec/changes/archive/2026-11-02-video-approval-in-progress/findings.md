# findings

- 回归来源：9f5ad13（封面取自成片）给成果写 cover_check，但 creative_contracts._METADATA_KEYS 未登记；creative_executions 交付时已先去掉执行方自带的 cover_check。
- video_chain.decide 通过小样/成片时先 _accept_outputs（逐个 decide_output，单个视频约 9 秒）再追加 decision，期间 state() 仍按 result_ready 无决定 → 「待你看」。
