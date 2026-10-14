# 生活日常音频独立实物复核

## PRD / 需求背景
受用户委托，独立复核本次单次真实TTS77及已审阅口播候选74。逐段核对完整假想生活叙事、明确AI结尾与真实WAV声学，不重新生成或操作正式采用。

## 目录结构
`quality.json`保存完整转写27段、7个原稿段落的精确归一对齐、全部17处替换、声学及安全供应商任务回读。原口播在同级`accepted-spoken-candidate.json`，原WAV保留在正式media目录。

## 已完成
结论：**ACCEPTED_WITH_SCOPE_BOUNDARIES**。真实WAV为129.22634375秒、32000Hz/16bit/单声道PCM，8,271,650字节；SHA为`79c8709d4795b33cf7764cd99e34c2697ff411f46e042d9eb116411a8fe1486c`。只读正式任务9a5c1dec5109480dbc01a83431a30ee3的path/hash/MIME/size与原件一致，复核前后原件SHA不变。

完整离线ASR覆盖至129.080秒，明确包含“本段内容由AI辅助创作，声音为AI合成”。原稿与转写繁简/标点归一后均621字符，整体对齐96.9404%；无插入或删除，17个替换片段涉及19字。六段假想生活及结尾均保留；未发现整段遗漏、重复、截断或额外疗效宣称。逐段文字精确对齐如下，时间定位仅精确到原ASR cue，不冒称强制逐词对齐。

| 原稿段落 | 归一字符数 | 对齐率 | 替换片段 |
| --- | --- | --- | --- |
| 1 | 83 | 98.795% | 1 |
| 2 | 76 | 100.000% | 0 |
| 3 | 107 | 92.523% | 7 |
| 4 | 123 | 94.309% | 6 |
| 5 | 121 | 98.347% | 2 |
| 6 | 93 | 98.925% | 1 |
| 7 | 18 | 100.000% | 0 |

全文件PCM满幅及near-full-scale样本均0，true peak -4.9dBFS、integrated loudness -23.7LUFS、LRA3.2LU；-45dBFS/至少0.5秒静音的最长停顿0.79625秒。无已确认需要重合成的缺陷。

## 待完成 / TODO
未直接试听，实际音色、自然度、韵律、发音仍保留`human_review_required`。ASR“瓷碗→此晚”“木筷→木块”“锁舌→锁蛇”“轻声→亲身”等均原样记录；同音/近音识别结果不足以证明TTS实际错读，未将识别文本悄悄改成原稿。正式采用及当前QC由主任务完成，报告不把审阅开始的result_ready快照当作后续最新状态。

## 关键设计决策
沿用已验证的完整文件离线复核方法，复用LocalMLXASRProvider与本机Whisper medium缓存，sandbox-exec禁网，零模型下载/收费ASR/供应商调用。归一仅处理繁简、标点、空格及拉丁字母大小写，不抹除任何词句差异；不以ASR/声学代替人类试听，不改素材权限或字节。

## 依赖与启动方式
既有API venv、voice-pro MLX worker、Whisper medium缓存、ffmpeg/ffprobe与macOS CoreFoundation。临时脚本`/tmp/aics-daily-lifestyle-audio-review.py`、`/tmp/aics-daily-lifestyle-audio-finalize.py`；无源码/tests/产品依赖变更，未写正式DB。
