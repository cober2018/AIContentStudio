## 2026-11-10
- 导出文件名原来由剪辑模型自己起，平台不管，所以叫法不一。现在平台在开剪 / 重做封面结果里给 file_names。
- 数据库里只有 material_revision.file_path（external/<源>/<哈希>/<相对路径>）和 creative_execution_output.staging_key 用到导出路径；verified 记录里的路径一并改，避免整片重算哈希。
- 12 条交付记录指向旧硬盘（/Volumes/T1000、/Volumes/500g），本来就打不开，没动。
- 5 条素材记录（敏贝贝薯乐酥 任务27/33/成片v14、如何判断过敏体质 任务43、量化数据质量 任务68）的文件改名前就不在了（旧版本已删），没动。
- 比例按作品最新导演稿读，不写进存着的标题。
- 改名前备份：backups/content_studio_before_export_rename_20261110201338.db
