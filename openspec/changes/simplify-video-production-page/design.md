## Page layout

```
内容方案
  [9 列分镜表]  素材列显示自动补齐结果与来源
  主按钮：生成导演稿 → 采用这版 → 补齐中 n/N → 去制作
  ▸ 更多：流程阶段与子步骤、历史版本、检查、冻结候选

制作内容
  [同一张分镜表]  素材列可改
  ① 生成配音 → 试听
  ② 准备剪辑包 → 回片预览
  ▸ 更多：字幕、时间线、ASR、逐镜工具、导演包详情
```

## Decisions

- One primary button per page. Its label comes from data that already exists: no draft → 生成导演稿; a draft waiting → 采用这版; autofill running → progress; master saved and filled → 去制作.
- 采用这版 runs: accept stage candidate → save master → start autofill. Each call is the existing one; if one fails, the page stops there and shows the reason in plain words, and the button retries from that point.
- Autofill never replaces the user's picks (unchanged rule from `storyboard-auto-material`).
- 更多 is a single collapsed block that renders the existing panels unchanged, so nothing has to be rewritten to keep working.
- The step list for non-product video stays 目标 / 内容方案 / 制作内容 / 审阅 / 交付; only the content of 内容方案 and 制作内容 changes.
