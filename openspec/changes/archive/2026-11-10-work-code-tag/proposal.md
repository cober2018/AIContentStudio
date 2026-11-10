## Why
我们沟通时都说「作品 97」「项目 62」，但界面上作品编号只在列表的小灰字里（「内容单元 #97」），制作页里基本找不到。用户要求：作品编号做成一个醒目的标签，放在中文标题前面，在三个工作台的制作过程里一直看得到。

## What Changes
标签样式：圆角小标签「作品 97」，放在作品中文标题前面，和标题同一行。出现在：
- **制作页标题**（三个工作台共用，每一步都在页面顶部）：角色内容、商品视频、搜索推广作品的大标题前。
- **作品列表**：角色内容工作台、商品视频工作台的「选择作品，继续创作」每一行；搜索推广项目页的作品列表每一行。
- **待审成稿页**（用户确认时追加）：作品列表每一行、作品详情标题。
- 列表里原来的小灰字「内容单元 #97」去掉，避免重复。

## 不做
- 不改编号本身（就是现有作品 id），不加搜索、复制等功能。
- 不改后端。

## Impact
- apps/web/src/product/ProductionContextHeader.tsx：三种标题
- apps/web/src/product/ProductionQueuePage.tsx：作品列表行
- apps/web/src/product/SearchPromotionWorkbench.tsx：搜索推广项目页作品列表
- apps/web/src/product/ProjectReviewCenter.tsx：待审成稿列表与详情标题
- apps/web/src/components/ui.tsx：标签组件 WorkCode
