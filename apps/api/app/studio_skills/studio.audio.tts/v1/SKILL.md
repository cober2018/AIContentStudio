---
key: studio.audio.tts
version: 1
source_kind: studio_builtin
---

复用现有ProviderGenerationTask生成真实语音，不创建另一套生成任务真源。输入必须是接受的口语稿与声音方向，voice是Provider支持的精确标识，rate必须经过该适配器能力校验并真正传给执行器。不得偷偷替换用户钉死的模型或声音；无可执行TTS路由就阻断。预览不调用模型，发送后Unknown不自动重试。成功返回的音频仍是待接受结果，人工接受才创建MaterialRevision，且不会自动修改Master。当前包本身不执行脚本，具体Stage连接须以运行时合同为准。
