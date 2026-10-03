# FE-F8 启动与就绪失败路径

日期：2026-10-03

正式范围：本机 loopback API，SQLite + local storage；这里验证失败时 fail-closed 和安全 reason，不启动生产模式、不执行迁移。

## 实际探针

- 数据库不可用的临时探针返回：`ready=false`、`status=degraded`、`reasons=["database_unavailable"]`；原始异常内容没有进入响应。
- 早期未批准生产身份draft曾用 `validate_production_settings` 验证固定配置错误；本次本机提交不纳入该validator、JWT或启动改动，不将这个探针算生产启动验收。拟提交版本对production readiness直接返回auth=false及固定 `production_configuration_invalid`，不能声称生产身份已可用。
- 已有 `test_observability.py`、`test_migrations.py` 和设置安全回归覆盖健康接口、schema-head 失配、存储不可用、队列/worker 失败和敏感配置投影；本轮只做临时 failure probe，不新增永久测试代码。

## 本机结论

本机正式profile不要求开启production auth、Celery或MinIO；队列关闭时本机同步路径仍可用。JWT/生产启动切换/MinIO实现不纳入本次本机提交，不能以本机代码对外部署。未来切到production必须单独完成身份/启动/schema/secret/storage义务，不能用readiness失败替代完整生产启动验收。
