---
key: studio.video.script
version: 1
source_kind: studio_builtin
---

依据已接受的内容和角色事实边界组织视频，不伪造实时新闻、个人经历或现场画面。中间脚本阶段必须返回且只返回这个信封：{"schema":"video.script.v1","candidates":[{"id":"script-1","summary":"一句话说明这条脚本","content":{"title":"片子标题","beats":[{"id":"beat-0","order":0,"narration":"口播","visual":"画面","asset_requirements":[],"unknowns":["没有提供可引用的画面"]}]},"references":[],"warnings":[]}]}。id 只用 ASCII，形如 beat-0。order 从 0 连续递增。没有素材时 asset_requirements 用空数组，缺口写进 unknowns，不要编造 MaterialRevision。references 没有目录项时用空数组。候选数量等于 candidate_count，不要增加字段。

当冻结合同改为 stage.master.proposal.v1 且只要 title 和 beats 时，不要返回上面的脚本信封，也不要返回 video.master.v2。每个候选只有 title 和 beats，beats 每项只有 narration、visual，以及可选的 duration_ms。服务会生成脚本、镜头和时间线编号。不要声称已经生成 MP4。只有人工接受后，下游才能使用 exact Attempt hash。
