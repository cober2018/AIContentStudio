## 1. 导演稿分组
- [x] 1.1 `video_documents.py`：`consistency_groups` 校验（镜头存在、≥2、不重复、不是模板 / 素材库）
- [x] 1.2 导演稿审阅页列出分组

## 2. 后端
- [x] 2.1 `product_video.py`：作品类型判断（商品、角色放行，其他拒绝）；`_mode`、`_keyframe`、`_frames` 不依赖商品链接；改运镜仍只给商品作品
- [x] 2.2 `shot_prompt`：组内镜头带共用人物、场景；角色作品不提商品，另返回文生视频提示词（中英文）
- [x] 2.3 `generate_shot_image`：角色作品不带商品参考、不检查、不拦亮相镜头，人物规则不重复
- [x] 2.4 `start_shot_video`：角色作品没首帧时的提示
- [x] 2.5 `shot_videos`：角色作品返回镜头状态（`persona: true`），两类作品都返回分组
- [x] 2.6 `shot_image.py`：九宫格按组出图（`group_id`），去掉默认画全部；放行角色作品；保持一致说明、人物规则不提商品
- [x] 2.7 `motion.json`：加不提商品的视频规则

## 3. MCP、规则、skill
- [x] 3.1 `creative_mcp.py`：七个工具说明；`generate_storyboard_grid` 改传 `group_id`
- [x] 3.2 `video_chain.RULES`：第 3 条、分组规则、角色作品规则
- [x] 3.3 `studio.video.prompt-direction`：九宫格改成按组

## 4. 页面
- [x] 4.1 `ProductionWorkspace.tsx`：素材步骤对角色作品也挂镜头面板；去掉旧九宫格面板
- [x] 4.2 `ProductShotPanel.tsx`：每镜一块抽成可复用的部分；归组镜头显示「打开九宫格」；角色作品文字、无形象照提示、文生视频 / 图生视频两栏带复制、首帧输入自动填
- [x] 4.3 九宫格弹框（替换 `StoryboardGridPanel.tsx`）

## 5. 验证
- [x] 5.1 副本上作品 94：入口、两种提示词、上传、shot_slots、prepare_video_edit
- [x] 5.2 副本上分组校验、按组九宫格（打桩，商品 / 角色各一次）、生首帧、自动图生视频（打桩）
- [x] 5.3 项目 48 商品作品照旧
- [x] 5.4 全量测试、前端类型检查；写 progress.md
