# 发现

- 没有形象照时的人物规则在 `product_video.person_rule` / `SCENE_WITHOUT_PERSON(_EN)`，单镜提示词、单张生首帧、九宫格（`grid_prompt`、`_alone_prompt`）都从这里取，改一处要覆盖这几处。
- board 字段是白名单校验，可选字段都是「写了才存」，加新字段不影响旧导演稿的哈希。
- `_people(board)` 看 speaker / character / attitude / 画面里的人称词判断「人物镜头」，用于人物提示；标了 other_people 的镜头单独出提示，不再按「不会出现人物」提示。
- 审计建议的「默认手机实拍写法」「英文提示词夹中文」不在这次范围。
