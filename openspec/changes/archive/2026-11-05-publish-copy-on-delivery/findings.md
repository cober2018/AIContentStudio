# findings

- 显示素材图片的现成接口是 /materials/{material_id}/revisions/{rid}/raw，要 material_id；所以 GET product-video 顺带返回封面的 material_id。
- 现有规范里没有写发布文案位置，这次新增一条。
