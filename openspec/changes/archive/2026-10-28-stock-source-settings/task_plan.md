# 实施计划

/// 1 后端存取：`open_media_sources` 设置行 + runtime_config；env 兜底；mask_secret
/// 2 open_media：各来源 configured()/enabled 读设置；available() 过滤关闭的
/// 3 CoverrProvider（视频，Key，下载域名白名单，许可登记）
/// 4 settings 路由：GET / PUT /settings/open-media，POST /settings/open-media/{source}/test
/// 5 前端设置页 + 导航
/// 6 实测、测试、文档、归档
