# task_plan

## 分阶段
1. 数据与资料页：推广对象（两层分类、版本）、搜索规划（草稿→确认锁版本）；接口；导航与工作台页面。
2. 开作品与生产链：`production_domain=search`（迁移）；从规划的问题开文字/图文/视频；search 域按「无角色」走链条（与商品同样不要身份快照），上下文用 search_context（推广对象版本+规划版本+问题），冻结进稿件；写作简报带搜索规划与可引用事实。
3. 检查：`seo.search_promotion` 规则与机械检查；语义项交写作模型判断。
4. 平台版本与交付：search 域版本不绑账号，只给复制/稿件包；不进草稿箱、回执、复盘。
5. 验证：库副本走通、全量测试、tsc、build；README/progress 回写。

## 关键设计
- 「无角色」判断集中成一个函数 `persona_free(unit)`（product、search 都算），替换各处 `== "product"` 里表示「不要身份快照」的判断；商品专属内容（SKU、购买理由检查）仍只认 product。
- search_context 只在 search 域出现，和 product_context 平行，不复用商品数据。
