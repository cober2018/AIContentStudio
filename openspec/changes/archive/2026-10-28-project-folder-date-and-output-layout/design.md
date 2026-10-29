# 设计

## 命名

- `folder_name(db, project_id)`：首次生成时取 `project.created_at` 的本地日期 `YYYYMMDD` + `_` + 现有短名（`_clean(标题第一个｜前)`，空则 `项目{id}`）；重名加 ` (#id)`。仍然只生成一次并存进设置 `project_folders`，之后标题改动不改文件夹。
- 保留名（外部素材库、通用素材库、平台目录、样板 `项目1`）不受影响。

## 已有项目迁移（一次性脚本，接口不暴露）

1. 读设置 `project_folders`，算出每个项目的新名字；列出「旧名 → 新名」，旧名已带日期前缀的跳过。
2. 素材库盘可写时逐个处理：`os.rename` 文件夹 → 更新设置里的名字 → 所有 `metadata_json.placement.path` 以「旧名/」开头的素材版本改成「新名/」→ 全库扫描指向旧路径的符号链接（项目间快捷方式）改指新路径。每个项目一个事务，失败把文件夹改回原名。
3. 素材库盘没连接时不动，脚本提示后退出。
4. 迁移结果写进 findings.md（旧名、新名、改动的素材数、快捷方式数）。

## output/ 归位

| 现在 | 去处 |
|---|---|
| `template-preview/`、`template-preview-landscape/` | `_平台/模板审片/竖屏/`、`_平台/模板审片/横屏/` |
| `安全区/` | `_平台/规格/播放安全区/` |
| `absorb/` | `_平台/吸收资料/` |
| `editing-techniques/` | `_平台/剪辑技法/` |
| `playwright/` | `_平台/测试/playwright/` |
| `ai-tech-eval-*`、`tech-audio-project35*`、`persona-35-graphic.zip` | `<项目35 的日期前缀名>/` |
| `lifestyle-*project36*`、`persona-36-graphic.zip` | `<项目36 的日期前缀名>/` |

- 项目相关文件夹名与素材硬盘上的同一规则（`YYYYMMDD_项目名称`）。
- 审片页引用的视频路径是相对路径，整体搬家后仍可打开。
- 根 README「目录结构」写明 `output/` 规则；审片脚本、预览脚本里写死的 output 路径同步更新。
