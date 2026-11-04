# 审计：host-parallel v2

审计时间：2026-11-04。对象：提交 7988d2a，本机模板库 `~/AIContentStudio/ae-templates/host-parallel/v2/`，检查渲染 `output/_平台/模板审片/host-parallel-v2/`。

## 结论

通过，没有缺陷。

## 核对了什么

| 项 | 结果 | 证据 |
| --- | --- | --- |
| v1 没动 | 对 | 提交没碰 `templates/host-parallel/v1/`；v1 两个工程的 SHA256 和说明书一致；平台列表 v1 仍是 ready，字段和时长没变 |
| v2 字段 | 对 | img1–img4（前两张必填）、item1–item4 各 ≤8 字、beats ≤80 字、时长 4–60 秒（默认 7 秒） |
| v2 工程和说明书一致 | 对 | 竖屏 `template.aepx`、横屏 `template-16x9.aepx` 的 SHA256 都和 manifest 一致 |
| 平台状态 | ready | `list_ae_templates` 里 v2 是 ready、带透明通道；manifest 里有 4 条 checks |
| 4 张排版 | 对 | 检查渲染 A（竖屏、41 秒）每 4 秒抽一帧看过：四张小图一排在上方，依次展开、收回，标签按小图宽度自动缩小，结尾淡出 |
| 脚本改动不影响其他模板 | 对 | 合成长度只有 host-parallel 设 60 秒，其余仍是 10 秒；`check_safe_area.py` 的 `--until` 默认 6 秒；`check_safe_area.py` 引用 `make_templates.py` 时有 `__main__` 保护，不会顺带跑搭建 |

## 可选建议（不阻塞）

- `check_safe_area.py` 现在按 `VERSIONS` 取最新版本，所以 compare-pair 也改成查 v2，不再查 v1。查最新版更合理，只是行为变了，在说明里提一句更清楚。
