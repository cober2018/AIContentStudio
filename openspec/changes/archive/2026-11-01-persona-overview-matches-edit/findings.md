# findings

- 概览由 `IdentityProfileView.ProfileOverview` 渲染，不在 `KNOWN` 里的键全部进「其他资料」原样显示；`brand`（品牌拆分后由 effective() 加入）、`portrait_material_revision_ids`、`speech_sample_folder` 都没登记。
- 编辑页顺序：声音、形象照、逐字稿样本、身份/表达/边界、高级。
