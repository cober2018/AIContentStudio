# persona-shot-generation

## 需求背景
角色作品（如作品 94）导演稿采用后，没有用户素材的镜头也要能出视频：自动图生视频，或手动（文生视频提示词 / 平台出图 + 图生视频提示词，网页生成后上传）。九宫格只给需要同一人物或同一场景的一组镜头，分组由模型写进导演稿，在弹框里做；商品作品一起换，旧面板删除。详见 proposal.md。

## 当前阶段
本地开发完成、本地验证通过（progress.md）；2026-11-03 已重启 API 和 worker；已归档，和 persona-faceless-others 一次提交。

## 成果文件
| 文件 | 内容 |
| --- | --- |
| proposal.md | 改什么、不做什么、验收 |
| specs/product-video-production/spec.md | 规范增量 |
| tasks.md | 开发清单（已完成） |
| task_plan.md / progress.md / findings.md | 计划、改动文件和验证结果、发现 |

## 代码位置
工作区 main 分支未提交改动，文件清单见 progress.md。

## 下一步
无（已提交；推送等用户说「推送」）。
- 审计：review.md（2026-11-03 按确认方案通过；两条建议修：角色作品提示词缺「拍摄方式」、英文提示词夹中文）
