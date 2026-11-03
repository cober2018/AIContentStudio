# findings

- 来源：sdr-render-compensation-and-source-check 实测——导演稿时间线无 trim，检查回退到镜头内偏移；任务 42 shot-6 +7.9 贴近提示线；按剪辑清单真实截取点比任务 41 为 −15.9～−18.9、任务 42 为 −1.7～−0.1。
- 剪辑清单（edit_manifest）含每段 trim_start/trim_end，但要列 output_hashes（含成片指纹），只能在成片之后交，检查成片时拿不到。
- 成果信息字段有白名单 creative_contracts._METADATA_KEYS，执行方带的字段需登记并校验。
- 拒收码用 `video_chain_shot_sources_invalid`：creative_mcp.domain_error 对 video_chain_ 前缀已透传 message，不必新增前缀。
- 执行方成果信息原本单值 ≤2000 字符、总量 ≤4000 字节；100 条 shot_sources 约 7100 字符，故 shot_sources 单值放宽到 8000，总量按其长度加额度。
- 清单补算复用已存的成片逐镜读数，只重新取原片帧；优先级 清单 > shot_sources > 估计；读数与提示带 source_basis（manifest / reported / estimated）。已存读数被截断（truncated / 无镜头）时不补算。
- 清单 speed_percent 缺省按 100；同镜多段取覆盖镜头中点的那段。
