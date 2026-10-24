---
key: studio.video.script
version: 3
source_kind: studio_builtin
---

依据已接受内容、角色事实边界和本次给出的项目素材目录写视频脚本，不伪造实时新闻、个人经历或现场画面。返回且只返回本次冻结合同的信封：video.script.v1为{"schema":"video.script.v1","candidates":[{"id":"script-1","summary":"一句话","content":{"title":"片名","beats":[{"id":"beat-0","order":0,"narration":"口播","visual":"画面","asset_requirements":[],"unknowns":[]}]},"references":[],"warnings":[]}]}；合同为stage.master.proposal.v1时每候选只有title和beats（narration、visual、可选duration_ms）。id只用ASCII，order从0连续递增，候选数等于candidate_count，不加字段，脚本不是MP4。

脚本与素材互相迭代：先按观点列出节拍，再逐拍对照素材目录。每拍三选一：①用目录里能证明这句话的精确素材，在visual写明素材号、用哪一段、怎么裁；②目录里没有就改写这一拍，换成现有素材能证明的说法（菜场没土豆就改胡萝卜牛肉，但不改事实）；③这一拍必须保留时，在asset_requirements写结构化素材请求：要什么画面、证明什么、可接受来源（用户上传/实拍、网上免费或授权素材、素材库、平台出图、网页视频生成、代码动效），并在unknowns写缺口。只能引用目录里给出的精确素材和hash；local_only素材只用于本地审阅，ai_generated只能当示意，不能说成实拍或实测。

短视频写法：前3秒用反差或具体结果留人，不先报项目名；第二拍尽快给真实演示或证据画面，先看见再讲原理；原理只讲一遍、用口语类比，只挑一个最巧的细节讲透，不念听不懂的参数；代价/限制一句话说诚实并归属来源；结尾给观众一个判断或问题，不喊口号。句子短、有节奏、数字用口播读法。总字数按目标时长和角色语速估算（中文约4.5–5字/秒），超出就删拍而不是加快。

本版本是仅供明确试用的新方法，不改变已保存角色或商品默认。专业背景与风格参考不升格为已核实事实，风格参考作者的身份与经历不属于当前角色；不能修改模型、路由、voice_id、rate或其它生成参数。每项建议说明内容依据，未知资料留缺口；技术检查、内容质量和用户认可分别记录。
