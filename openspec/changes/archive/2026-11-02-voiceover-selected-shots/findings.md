# findings

- voiceover.generate：_script 拼全部台词 → 一条音轨；_role_lines 按 board.character 分角色但仍全片合成；最后 align_to_voice 按配音重排镜头时长。
- 导演稿 voice 只有 mode(none/recorded/tts)+material_revision_id；整片等长、只在标记镜头处有声的配音轨可沿用该结构，不改 voice 格式。
- 作品 92（作品 90 的副本）11 个镜头，第 10 镜目前无台词、speaker=none，时长 3000ms；voice=none。
- 用户纠正：配音声音必须与角色挂钩（每个角色固定声音），所以镜头上标的是角色（dub_persona），不是声音配置。角色声音见 voice_presets 的 personas 映射。
- 角色声音来自 voice_presets.personas：阿玲聊生活→阅历姐姐、懒羊羊小王→女声、其余男声。
