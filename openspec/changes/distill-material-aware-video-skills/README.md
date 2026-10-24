# distill-material-aware-video-skills

## PRD / 需求背景
用户确认科技新题第二版路线已打通（网上找到真实素材、代码动效与实拍拼接加工），但能力只在执行模型会话里。要求沉淀为平台已有的 skills：脚本/分镜与素材互相迭代（没土豆就改胡萝卜牛肉）、何时去哪找素材、动效审美武器库、组合剪辑技巧。

## 当前阶段
用户确认后已 apply（2026-10-21），strict 校验通过；未提交、未归档。

## 目录结构
proposal.md / design.md / tasks.md / specs/（studio-creative-skill-pack、web-video-production-handoff）

## 已完成
- 平台内置 `studio.video.script@3`、`studio.video.shot-director@3`（素材驱动规划，@2不变）
- 执行端技能 `.codex/skills/video-material-scout`；`video-production-handoff` 新增动效武器库、组合剪辑、收尾规则与参数化AE构建器 `scripts/ae_build.py`
- 方法记忆候选修订45–48（画面节奏、字幕、AE包装、终混），角色默认未改
- 验证记录见 tasks.md
- 用户确认后已采纳为科技角色2默认（角色修订6）：script只启用@3，storyboard启用shot-director@3，剪辑四阶段用修订45–48；旧方法保留关闭；新作品快照52生效。生活角色未改。

## 待完成 / TODO
- 授权后提交与归档

## 关键设计决策
按执行者分层：平台阶段模型管规划与素材请求；执行端管搜索/抓取/核验/登记/制作；方法记忆存角色剪辑偏好。新版本与候选修订都不自动成为角色默认。

## 依赖与启动方式
仓库根目录 `openspec validate distill-material-aware-video-skills --strict`。
