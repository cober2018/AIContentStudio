# 科技日常音频独立实物复核

## PRD / 需求背景
受用户委托，对本次单次真实TTS输出及已审阅口播候选做完整离线AI代理验收。此报告不执行采用、改音频或再次生成。

## 目录结构
`quality.json`包含原件SHA、完整WAV元数据、全文件声学、65段完整离线ASR、精确对稿差异和评审结论。来源为同级`accepted-spoken-candidate.json`；原WAV保留在正式media路径。

## 已完成
结论：**ACCEPTED_WITH_SCOPE_BOUNDARIES**。159.67934375秒、32000Hz/16bit/单声道PCM WAV完整可解码；原件SHA为`841a8d481d1aff15876b7eba2f4876d26564dd7578680058d944f48a429541f0`，复核前后相同。完整转写覆盖到159.6秒并包含AI辅助创作/合成声音说明。繁简及标点归一后的精确口播对齐98.8060%，保留6处替换片段；未发现整段遗漏、重复或提前截断证据。

PCM满幅及near-full-scale样本均0，true peak -1.1dBFS、integrated loudness -23.2LUFS、LRA3.2LU；-45dBFS/至少0.5秒静音的最长停顿0.994938秒。无已确认的成品缺陷要求重合成。

## 待完成 / TODO
未直接试听；实际音色、自然度、韵律、发音仍保留`human_review_required`。ASR原样记录了“产出→铲除”“校验→教练”等差异，不能仅凭识别文本认定真实错读，也不将其悄悄纠正为完全一致。正式页面明确采用及当前QC由主任务独立完成。

## 关键设计决策
全文件处理而非10秒样本；复用已安装`LocalMLXASRProvider`及缓存Whisper medium，子进程`sandbox-exec`禁网、离线开关启用，零下载/收费ASR/供应商请求。不以ASR与声学代替人类感官判断，不授予或更改素材权限。

## 依赖与启动方式
已存在的API venv、voice-pro MLX worker、本机Whisper medium缓存、ffmpeg/ffprobe及macOS CoreFoundation。临时复核脚本位于`/tmp/aics-daily-technology-audio-review.py`；无产品依赖或源码改动。
