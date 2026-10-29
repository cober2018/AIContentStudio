# 进展

- 2026-10-29 提案建立；用户选择已有文件夹一起改名。
- 2026-10-29 用户确认。project_folders.folder_name 改为 YYYYMMDD_短名（创建时间转本机时区）；新增 date_existing_folders(db, apply) 一次性迁移：改文件夹名、设置、placement.path 与 links 前缀、指向旧路径的符号链接，失败回滚。实跑：41 海底光缆 → 20261022_海底光缆（58 个素材版本，改前改后 58/58 可解析、无旧路径残留），42 儿童麸质饼干 → 20261027_儿童麸质饼干。output/ 按设计表归位（项目 35 → 20261019_AI科技实作、36 → 20261019_生活观察，平台类进 _平台/），根 README、craft-arsenal log、记忆同步。
- 测试：完整后端 2620 通过。与 HEAD 干净副本对比，多出的 3 个失败中 1 个是此前 MiniMax 厂商设置引起（启动注册读了页面配置）已修：bootstrap 只看启动标志，页面开关改由 register_if_enabled 在启动加载配置后和保存时补注册；另 2 个（test_models_plugins 的 minimax profile 密钥）来自工作区里他人未提交的「MiniMax 只认卡片密钥」改动，未改动、已告知用户。原有 6 个失败不变。
