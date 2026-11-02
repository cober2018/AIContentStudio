# findings

- 作品 90 → product_sku_work 31：sku 8，冻结 sku_revision_id 11（第 1 版，主图 315）；商品已有第 2 版（318）、第 3 版（319）。作品自己没有手动商品参考图（shared_references 为空）。
- 镜头静帧（shot_image.py 386/455）、一致性检查、图生视频（product_video.py 296/544/611）、任务书规则（148）都调用 product_video.references()；任务书展示的主图来自 direction() 第 132 行，读冻结版。
- references() 现有逻辑只在冻结版没有主图时才找最新版。
