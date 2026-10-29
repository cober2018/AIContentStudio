## 决定

| 问题 | 决定 | 原因 |
|---|---|---|
| Key 存哪里 | `system_settings` 一行 `open_media_sources`：`{来源: {enabled, api_key}}`，同步进 `runtime_config` 内存 | 与生图设置同一套做法，不加表、不迁移 |
| 和 runtime.env 的关系 | 页面保存过的值优先；该来源没保存过就用 env 里的 Key | 现有 Pixabay 配置不丢，不用重填 |
| 返回给页面 | Key 用现有 `mask_secret`；空字符串提交表示「不改」，单独的「清除」才删 | 不回显明文；避免误清 |
| 启用 | 默认：已有 Key 或不需要 Key 的启用；关掉后 `available()` 不返回它 | 搜索层只认一个入口 |
| 测试 | 后端用该来源搜一个固定词（如 `ocean`）取 1 条，返回成功 / 失败原因与耗时，不下载素材 | 让用户确认 Key 有效 |
| Coverr | 新 `CoverrProvider`（仅视频），需 Key；下载域名白名单；许可登记为 Coverr 许可（可商用，不强制署名），接入时按官方 API 文档核对字段 | 和现有来源同一结构，复用匹配与入库流程 |
| 权限 | 读写仅管理员（沿用设置页现有权限） | Key 是敏感配置 |

## 流程

```
设置页「素材数据源」 ──保存──> PUT /api/v1/settings/open-media
                      ──测试──> POST /api/v1/settings/open-media/{source}/test
        ↓ system_settings + runtime_config
open_media.available() ──> 镜头素材搜索（start_material_match / 自动补齐）
```

## 不做

音频来源与配乐 / 音效搜索；改匹配打分；改素材入库与许可流程。
