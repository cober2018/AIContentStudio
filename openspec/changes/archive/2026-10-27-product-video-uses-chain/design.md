## 做法

- `simpleVideo` 改为 `unit.modality === "video"`（含商品），视频链路状态读取、步骤跳转、锁定判断都随之覆盖商品作品。
- 步骤表：商品作品第一步标题用「商品与本条目标」，内容仍是商品目标组件（`GuidedProductionGoal` / 商品资料）；其余步骤与角色视频共用。
- 旧商品步骤（plan 下的导演方案、style、materials 旧版、edit、review）不再渲染；旧网址参数（`workstep=style|edit|review`）映射到新流程对应步骤或当前步骤。
- 第三方模型的 brief 里 `review_url` 已指向 `workstep=plan`，与新流程导演稿一步一致。

## 不做

- 不改后端视频链路。
- 不迁移旧商品流程已有的数据；项目 42 的作品还没开始，不受影响。
