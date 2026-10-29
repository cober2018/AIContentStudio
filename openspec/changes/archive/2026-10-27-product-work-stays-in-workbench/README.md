# product-work-stays-in-workbench

**阶段：** 已本地实施并验证，2026-10-28 归档；未提交 Git。

**做什么：** 工作台点商品不再新建项目；商品 / 角色作品的制作页归各自工作台（菜单、返回、位置），网址不变。

**代码位置：** `apps/web/src/product/ProductWorkbench.tsx`（进入商品、`?sku=`）、`ProductionWorkspace.tsx`（返回链接、标记所属工作台）、`taskNavigation.ts`（`setProductionWorkbench` / `useProductionWorkbench`）、`apps/web/src/App.tsx`（菜单高亮）。

**下一步：** 用户决定是否删除多出来的空项目 45、46、47。
