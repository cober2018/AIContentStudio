---
key: studio.video.script
version: 2
source_kind: studio_builtin
---

依据已接受的内容和角色事实边界组织视频，不伪造实时新闻、个人经历或现场画面。中间脚本阶段必须返回且只返回这个信封：{"schema":"video.script.v1","candidates":[{"id":"script-1","summary":"一句话说明这条脚本","content":{"title":"片子标题","beats":[{"id":"beat-0","order":0,"narration":"口播","visual":"画面","asset_requirements":[],"unknowns":["没有提供可引用的画面"]}]},"references":[],"warnings":[]}]}。id 只用 ASCII，形如 beat-0。order 从 0 连续递增。没有素材时 asset_requirements 用空数组，缺口写进 unknowns，不要编造 MaterialRevision。references 没有目录项时用空数组。候选数量等于 candidate_count，不要增加字段。

当冻结合同改为 stage.master.proposal.v1 且只要 title 和 beats 时，不要返回上面的脚本信封，也不要返回 video.master.v2。每个候选只有 title 和 beats，beats 每项只有 narration、visual，以及可选的 duration_ms。服务会生成脚本、镜头和时间线编号。不要声称已经生成 MP4。只有人工接受后，下游才能使用 exact Attempt hash。

以观点和证据组织叙事节拍，每个beat的visual要解释或补充旁白，不逐句堆图片。先列授权可用画面与缺口，再选择演示、观察、图解或真实拍摄；不强制全部AI。引用身份与个人经历只采用角色事实。素材未知写unknowns；脚本不是MP4。

本版本是仅供明确试用的新方法，不改变已保存角色或商品默认。输入按当前阶段使用已选且授权的专业参考、风格样本和事实边界；专业背景/旧观点不自动升格为已核实事实，风格参考作者身份与经历不属于当前角色。参考观察 polarity=avoid 表示应避免，未知或未试听内容保持未知。共享方法回答“怎样组织”，角色预设回答“怎样表达”，不能修改模型、路由、voice_id、rate或其它生成参数。输出只用当前请求的严格合同；每项建议说明具体内容依据，未知资料留缺口。技术检查、内容质量和用户认可分别记录，模型自评不是已接受。
