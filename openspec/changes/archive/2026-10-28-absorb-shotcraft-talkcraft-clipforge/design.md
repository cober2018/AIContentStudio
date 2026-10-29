## 顺序

| 步骤 | 内容 | 停下给用户看 |
|---|---|---|
| 1 | 两套体系分开（代码小改） | 否，做完汇报 |
| 2 | 下载三个仓库到 `output/`（固定提交号） | 否 |
| 3 | clipforge 提炼 → 商品 skill 映射表 | **是** |
| 4 | 按映射表写 / 改商品 skill，校验能被平台加载 | 否 |
| 5 | shotcraft、talkcraft 提炼卡片 | 否 |
| 6 | 对照现有武器库出梳理表（新增 / 合并 / 替换 / 舍弃） | **是** |
| 7 | 按梳理表换算写入 techniques 与 choose.md | 否 |
| 8 | 通过 MCP 读取验证，记 log，归档 | 否 |

## 体系划分

- 商品：`studio_creative_catalog.PRODUCT_CONTEXT_SKILLS` 及本次新增的商品 skill。
- 角色：其余 `kind == skill` 的写作 skill。
- 共用：craft-resolve、craft-ae（不在写作开关内，一直可用）。
- 商品作品 = `production_domain == "product"`。

## 换算规则

沿用 `craft-arsenal/rules.md`：每条有 用在 / 不用在 / 做法（DaVinci 或 AE）/ 检查 / 常见错误 / 状态 / 来源；接口名用 DaVinci Resolve MCP 核对；值得做 AE 模板的只标「模板候选」。Remotion 专有、无法用 AE / 达芬奇实现的配方舍弃并写明原因。

## 不做

- 不引入 Remotion、不安装 Node 渲染链。
- 不把仓库原文、代码、素材、音乐放进平台。
- 不自动把新商品 skill 设为默认方法；默认开关不变。
