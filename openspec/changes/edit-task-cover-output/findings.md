# 发现

- 剪辑交付在 creative_executions._project_output 里按角色限定目录：rough_cut / final 在 导出/小样|成片，其他在任务的 工作 文件夹。
- 剪辑任务的输出合同里每个角色都是必需的（role() 固定 required=True），封面要单独设成可选。
- 成片通过后存的新主稿要算作「保留导演稿」的保存（_KEEPS_DRAFT 加 cover），否则视频进度会回到「待开始」。
