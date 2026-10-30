# 进度

- 2026-10-30 写好方案，待确认
- 2026-10-30 实施完成：product_video._after_approval 拦住采用前的 set_shot_mode / set_shot_first_frame / generate_shot_image / start_shot_video；ProductShotPanel 分 draft（运镜、光线、强度、发布文案）和 materials（汇总 + 只列缺画面镜头的手动 / 自动、首帧、提示词）两种视图；导演稿翻页视图不再显示素材状态；规则和 MCP 工具说明写明顺序。
- 验证：相关 170 passed；前端 tsc 通过；真实数据：作品 85（导演稿待审）生成被拒并给出提示，作品 83（已定稿）不受影响；API 已重启。
