# progress

- 2026-11-03 方案写好，待用户确认
- 2026-11-03 开发完成（未提交、正式库未迁移）：迁移 websearch0001；services/web_material_search.py；routers/web_material_search.py；retention 30 天清理；MCP search_web_materials / get_web_materials；页面 WebMaterialSearch（商品编辑页、非商品作品素材步骤）、设置 WebMaterialSiteSettings
- 2026-11-03 库副本实测：商品「敏贝贝动物小饼干」18 秒读完 10 个网页，跳过 17 个对不上的；「OPPO Find X8」10 个官网页直接读全被拒（压缩响应），后台 Chrome 救回 3 页（22/25/15 张图，含参数页）；预览、勾选入库（来源网页、项目引用）、重复入库复用、存为资料（解析成功）、优先站点保存与校验都通过；MCP 发起和读取通过，非商品作品不给 query 时返回中文说明
- 2026-11-03 测试：后端全量 2441 通过，只剩原来 5 个已知失败（MCP 工具白名单测试已按新增的 2 个工具更新）；前端类型检查通过；openspec validate 通过。库副本已删除。等用户同意后迁移正式库、改 REQUIRED_SCHEMA_HEAD、重启
- 2026-11-03 已上线：正式库先备份（任务临时目录 live-before-websearch.db），再迁移到 websearch0001；REQUIRED_SCHEMA_HEAD 改为 websearch0001；API / worker 已重启；新接口与 health/ready 返回 200。还没在正式环境真搜一次（由后台服务启动 Chrome 这一步未验证），等用户在页面上试；未提交
- 2026-11-03 用户追加：商品资料页「保存资料新版本」改成浮在屏幕底部（sticky），旁边显示有没有未保存的修改；加图在下面、改类别在上面时不用来回翻
- 2026-11-03 用户验收（「提交吧」），归档并提交
