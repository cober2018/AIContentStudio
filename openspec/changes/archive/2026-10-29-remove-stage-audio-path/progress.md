# 进度

## 2026-10-29 清理旧项目（用户决定只留 3 个项目）
- 备份：`~/AIContentStudio-deleted-20261029/content_studio-before-purge.db`（删除前整库），两个旧成果文件夹 `output/20261019_生活观察`、`output/20261019_AI科技实作` 挪到同一备份目录。
- 删除（按外键从下往上删，不留悬空）：项目 36、作品 63、导演稿 / 定稿 99、检查 362、制作记录 43 次（步骤 206、尝试 241）、产出 90、专用配方 36、身份快照 50（只被删掉的稿子用过）、素材 74 条（只被这些项目用到；对应文件早已不在库里，未找到可挪的文件）等，共 39 张表。被保留项目也用到的 4 个素材保留。
- 另清掉 2 条早就悬空的制作设置记录（指向早已删除的作品 81）。
- 核对：项目列表只剩 41 / 42 / 43；外键检查无问题。

## 2026-10-29 删代码与数据迁移（工作区未提交）
- 数据：角色 2（rev 10→11）、角色 3（rev 4→5）存了去掉 audio_creative_profile 的新修订；账号 / 栏目当前修订无此字段。旧修订、身份快照原样保留，读取走原始 JSON 不再校验。脚本在 `~/.claude/jobs/1765d66a/tmp/drop_audio_creative_profile.py`。
- 后端：删 `stage_audio.py`、`stage_audio_asr.py`、`audio_quality.py`（母带响度挪到 `audio_mastering.py`，`POST …/loudness-master` 已改指向）；删 TTS v4 / ASR / 音频质检节点及各阶段分支、音频形态、两套音频质量标准、三个音频 skill 包；口语稿改为 text 形态，输出改名 `text.spoken-adaptation.v1`；商品制作设置去掉 audio_creative_profile / voice_id（旧记录读回时丢弃）和失效的 include_sound。
- 前端：创作配置去掉音频页；角色声音挪到「编辑资料」；结果面板对已下线阶段显示「已下线的阶段」；去掉 ASR 配方提示、商品默认音色区、媒体面板读已存声音的逻辑。
- 验证：后端 2449 passed / 28 skipped / 5 failed（全为已知基线失败）；前端 tsc 通过、node 测试 37/37、build 通过；重启 API 后 creative-catalog 只剩 spoken-adapt、无音频质量标准，`/settings/voice` 200，配音 GET 200。
