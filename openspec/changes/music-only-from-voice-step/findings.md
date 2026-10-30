# 发现

- 视频作品是简化流程（simpleVideo），制作设置只在「目标」一步显示，`view=style` 的「视觉与声音定样」对视频作品已到不了。
- 制作设置经 creative_packages.profile_snapshot 整份进任务包，所以默认值「不使用配乐」会被剪辑方读到。
- 主稿 music 现在只有 {material_revision_id} 或 {}，没有「明确不用」的表示。
- 用户确认：配乐未定时不能开剪（2026-10-30）。第三方模型仍可自己选一首放进主稿；「不用配乐」只有用户能在页面上点。
- 旧任务包里冻结了 music_direction，和新快照不一致，复用旧包时会提示 production_profile_changed_prepare_new_package，需要重开任务——正是想要的效果。
- 渠道改编（channel_adapters）原来见 music 非空就拒绝，改成只看是否有音乐素材，避免「不用配乐」被当成有配乐。
- 主稿上下文哈希含制作设置快照，改快照内容等于让所有旧主稿失效；要隐藏旧字段只能在下游（任务包）过滤。
- 在 app 外跑脚本要先 runtime_config.load_from_db，否则素材库根目录为空、素材会被误判为文件缺失。
