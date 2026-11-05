## 1. 指定读音
- [x] 1.1 `video_documents`：voice.pronunciation 校验
- [x] 1.2 `model_capability_routing` 放行；`minimax_cli_provider._synthesize` 带 pronunciation_dict
- [x] 1.3 `voiceover`：整条 / 多角色 / dub_persona 都传读音；复用判断算读音；保存 voice 保留 pronunciation
- [x] 1.4 `video_chain.brief` 和 MCP 工具说明

## 2. 只重配几句
- [x] 2.1 `creative_mcp`：`lines` 参数
- [x] 2.2 找每句起止（逐句时间 / 停顿检测 + 分组 + 核对）
- [x] 2.3 逐句重配、去首尾空白、放置与放不下报错
- [x] 2.4 拼接（停顿里切、1 帧淡变、总长不变）、存素材、更新导演稿
- [x] 2.5 保存类型按用户决定处理是否需要再通过

## 3. 验证
- [x] 3.1 校验：合格 / 不合格的读音条目
- [x] 3.2 请求体：截获发给 t2a_v2 的请求，看 pronunciation_dict 是对象
- [x] 3.3 只重配：用测试音频替身验证分段、放置、拼接（其余段逐样本一致、总长不变）、放不下报差多少秒
- [x] 3.4 已有测试
- [ ] 3.5 （经用户同意，付费）「去重/(qu4)(chong2)」实配一次，用音高和听写核对 chóng
