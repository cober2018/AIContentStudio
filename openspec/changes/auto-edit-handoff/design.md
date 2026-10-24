## Flow after 采用这版

```
采用这版 → 补齐空行 → 单一选择的行放入主稿 → 判断哪些行需要 AE → 写后期设置 → 保存主稿 → 重做并接受 导演包
```

Each step reuses an existing service. If one fails, the chain stops there, the page says which step and why, and a retry continues from that step. The user's own picks and overrides are never replaced.

## Decisions

- One model call decides AE rows for the whole table (rows in, `{row, ae: bool, reason}` out). If the call fails, every row is DaVinci only, with the reason 「自动判断失败，按只剪辑处理」.
- Rows with several picks are not placed automatically; they show 待你选 in the 素材 column.
- The user can still change any of this under 更多; a later re-run keeps the user's manual AE ticks.
