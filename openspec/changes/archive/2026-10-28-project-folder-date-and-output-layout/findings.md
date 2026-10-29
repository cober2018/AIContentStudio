# 发现

- 素材位置记在 MaterialRevision.metadata_json.placement.path（库根下的相对路径，以项目文件夹名开头）；项目间复用用符号链接；文件夹名存在设置 project_folders 里，只生成一次。
- 素材盘现有项目文件夹：儿童麸质饼干、海底光缆（另有 AIContentStudio、Z素材文件结构模板 两个目录，需确认是否为项目）。
- 2026-10-29 独立脚本必须先 runtime_config.load_from_db 才能拿到素材库根路径，否则判成未连接；项目 35/36 没有素材文件夹记录，output 归位用同一命名函数算名字。
