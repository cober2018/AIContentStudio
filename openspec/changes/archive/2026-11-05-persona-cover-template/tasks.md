## 1. 封面模板
- [x] 1.1 在 AE 做「角色封面 · 大字三卖点」透明字层，9:16 / 16:9，manifest 标 category 封面
- [x] 1.2 渲两版不同内容叠在真实商品画面上，给用户看；认可后写检查记录

## 2. 角色绑定
- [x] 2.1 角色资料加 cover_template（只能选封面类模板）
- [x] 2.2 角色页加「封面样式」选择和预览

## 3. 开剪带模板
- [x] 3.1 执行包带 cover_template；规则文字和 craft-resolve 封面段改写
- [x] 3.2 交封面查 cover_template_render，提示 cover_template_missing / cover_template_mismatch，审片页显示

## 4. 封面重交与重做
- [x] 4.1 封面一格任务通过前可重交；清单 output_hashes 不比封面
- [x] 4.2 审片页「重做封面」+ 备注；get_video_decision 带重做要求；新封面交上来自动完成；重做中成片不能通过

## 5. 验证
- [x] 5.1 库副本：重交封面、别的文件仍不能替换、重做封面流程、模板回执三种情况
- [x] 5.2 已有测试；前端构建
