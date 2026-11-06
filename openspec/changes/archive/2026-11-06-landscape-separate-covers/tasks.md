## 1. 后端
- [x] 1.1 16:9 成片任务交付清单加 cover_vertical；提交目录、项目素材挂载同 cover
- [x] 1.2 带 cover_vertical 的任务跳过 _cover_check，模板检查两张都做；清单 output_hashes 两张都要列
- [x] 1.3 审片结果返回两张及尺寸 / 缺失提示
- [x] 1.4 通过后主稿 cover 记 vertical_material_revision_id；重做封面两张都交才完成
- [x] 1.5 RULES、prepare_edit files 说明分竖版 / 横版
## 2. 前端
- [x] 2.1 审片页并排两张、提示文字
- [x] 2.2 交付步骤两张显示与下载（商品处 + 非商品横版新加一块）
## 3. 验证
- [x] 3.1 库副本：横版新任务交一张 / 尺寸错 / 两张对；竖版任务照旧；任务 56 不变
- [x] 3.2 测试、tsc、规范校验
