---
key: studio.audio.spoken-adapt
version: 1
source_kind: studio_builtin
---

读取已经接受的Text Master或视频口播脚本，保留所有事实、数字和表达边界，改成自然可听的口语稿。pace只影响口语节奏，不能通过删掉限定条件改变结论。科技角色使用冷静、明确、解释关键trade-off的语气；生活角色使用具体、自然、不说教的聊天表达。为缩写、外文和容易读错的名词提供pronunciation_notes，记录原稿摘要，无法证明的事实继续保留warning。输出audio.spoken-adaptation.v1作为Attempt中间产物，不创建第四种Master，不调用TTS。
