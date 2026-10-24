# 懒人沙发关键帧候选

2026-10-18追加儿童拖鞋两Skill方法试验：`children-slippers-skill-trial-touch-v1.png`及同名前缀prompt.txt，现有内置imagegen生成一张。局部商品保真未通过，仅试验候选，未入选或绑定Master。依赖/执行与完整复核见上级`skill-trial-product-photo-ad-script-20261018.md`。

## 需求背景
支持本次约30秒场景型分镜的静态审阅，图片确认后才进入视频阶段。

## 目录结构
source.png原图；S01-v1.png历史候选；S01-v2.png当前场景开场；S02–S05-v1.png当前整品/细节/使用/多色候选；manifest.json含逐图提示词、原图/连续性参考、尺寸与SHA256；S01-v2-prompt.txt为修订提示词副本。

## 已完成
实际生成6张候选文件，对应5个镜头；S01 v2解决与S02重复构图。所有图已查看，用户选择状态均为pending。

## 待完成
用户逐图确认；E01尺寸答疑需要真实资料，未生成假测量图。尚无视频提示词、视频生成或正式平台素材导入。

## 关键设计决策
每次生成真实输入原图。其他生成图只用于场景连续性，不能覆盖原图身份。表面细节、人物接触/比例、精确色彩仍是生成演绎，不作为性能或尺寸实证。

## 依赖与使用
PNG直接预览；图像来自Codex内置imagegen，不代表平台原生API新增参考图能力。无新依赖和启动命令。


## 儿童拖鞋新增候选（2026-10-18）
children-slippers-shot-1-v1.png为SKU-000003/Project34/Unit40首镜开场候选，提示词同名前缀-prompt.txt，素材61/65、项目引用已回读。该图待用户选定，不是旧沙发批准的延续，后续视频未生成；没有新依赖。


## 儿童拖鞋四镜候选与提示词
- children-slippers-shot-1-v1.png：两色同框开场，素材61/65；用户方向/配色确认。
- children-slippers-shot-2-v1.png：家长手部拿起灰色款，素材62/66。
- children-slippers-shot-3-v1.png：手持灰色款装饰近景，素材63/67。
- children-slippers-shot-4-v1.png：放回后两双同框，素材64/68。
每图同名前缀-prompt.txt为完整生图提示词；工具为Codex内置image_gen。用户原图是商品依据，首张为连续性参考；后三张待审阅，四张精确选图未代签。没有视频生成，新图未覆盖旧沙发文件。
