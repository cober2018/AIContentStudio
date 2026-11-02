# findings

- 报错来自 content_identity.hierarchy：persona_id 为空时 db.get 返回空 → 404「内容角色不存在」。作品 90：persona_id、identity_snapshot_id 都为空，production_domain=product；product_sku_work 31（sku 8、版本 11）；5 版制作设置。
- 商品视频启动时建 ProductSkuWork 与 ProductionProfileRevision（routers/product_skus.py 约 409–416 行），copy_unit 都没复制。
