# 字段对照

## save_reference_breakdown

| 字段 | 写什么 | 例子 |
| --- | --- | --- |
| analysis | 整体分析，普通段落，几百字以内 | 真实家庭场景做信任：孩子在家吃、妈妈手拿包装…… |
| timeline[].start_ms / end_ms | 原视频里的毫秒时间，取自 cuts.json 的段 | 0 / 3200 |
| timeline[].speech | 这一段的口播（转写原话，错字按意思改正） | 家里有敏宝，想吃点小零食真的太难了 |
| timeline[].picture | 画面：谁、在干什么、景别、机位 | 孩子坐沙发背对镜头吃薯片，中景，手机平拍 |
| timeline[].overlays | 叠加元素和它的出现方式 | 底部小号白色手写体字幕常驻 |
| timeline[].purpose | 这一段对观众的作用 | 抛出痛点，让敏宝家长对号入座 |
| shot_list[] | 本作品要实拍的镜头：shot_id（导演稿镜头 id，可空）、what、who、framing、camera、seconds、notes | what=孩子第一次尝到饼干；who=4 岁孩子；framing=中近景；camera=手机平拍固定；seconds=3；notes=自然光，别摆拍 |
| brand_material[] | 需要品牌真实资料的地方 | 过敏原检测报告；医院联合研发证明 |

## 导演稿每镜 board 新增的两个字段

- source_kind：shoot | product_image | generated | ae_template | library。shoot 的镜头没有另交 shot_list 时，平台会把它们汇总成拍摄清单。
- attitude：人物态度和对谁说，一句话。没有人物的镜头不写。

## 判断 source_kind

- 人在真实生活里的反应（孩子吃、宝妈涂抹、开箱上手）：优先 shoot；用户说不拍时用 generated，并在 notes 写明「AI 示意」。
- 商品本身的特写、亮相、下单引导：product_image，只用商品原图，不让 AI 改商品。
- 卖点卡片、对比、证书展示（有真实资料时）、下单箭头：ae_template。
- 空镜、氛围、通用画面：library。

## 拼图怎么读

每行是一段，左边 #N 是段号，三张图下面是原视频时间。一行三帧都一样，说明这一段画面基本不动；三帧差很多，说明段内有运镜或动作，回到 cuts.json 看这一段的时长。
