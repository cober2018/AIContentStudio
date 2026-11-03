## 1. 后端
- [x] 1.1 `video_documents.canonical_board`：`other_people` 只在写了时存，1–60 字，错误写清理由
- [x] 1.2 `product_video.py`：标了的镜头的人物规则（中英文）；`shot_prompt`、`generate_shot_image`、`person_notices` 用它；镜头状态返回标了谁
- [x] 1.3 `shot_image.py`：九宫格整张规则、格子描述、单格重画按标注写

## 2. 规则和说明
- [x] 2.1 `video_chain.RULES`、`creative_mcp.py` 三个工具说明
- [x] 2.2 `studio.video.prompt-direction` 第 4 条

## 3. 页面
- [x] 3.1 `ShotWork.tsx`、`StoryboardGridDialog.tsx`：标了的镜头写「这一镜可以出现…（不露脸）」

## 4. 验证
- [x] 4.1 副本上作品 94 标一镜「宝宝」：提示词、页面数据、person_notices；没标的镜头逐字不变
- [x] 4.2 九宫格打桩：一镜标一镜没标
- [x] 4.3 作品 93 只读比对；作品 93、94 导演稿哈希不变；校验拒绝坏值
- [x] 4.4 全量测试、前端类型检查；写 progress.md
