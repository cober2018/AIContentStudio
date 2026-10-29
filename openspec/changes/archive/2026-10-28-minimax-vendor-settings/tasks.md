## 1. 后端

- [x] 1.1 `minimax_cli_provider`：`SETTINGS_KEY="minimax_vendor"` 读取（页面优先/env 回退）、`page_config()`、`_run()` 统一拼覆盖参数、`vendor_status()` 增加 `key_from`/`base_url_configured`/页面优先 enabled
- [x] 1.2 `model_registration._minimax_view()` 透出新字段
- [x] 1.3 `routers/settings.py`：`PUT /model-registration/minimax` 保存/清除（endpoint/region 校验、掩码回显）、`POST /model-registration/minimax/test`

## 2. 前端

- [x] 2.1 `ModelRegistrationSettings.tsx`：MiniMax 卡片可编辑（启用、Key 保存/清除、访问地址、区域、测试与结果文案、来源标识）

## 3. 验证

- [x] 3.1 后端测试套件通过；`npx tsc --noEmit`、前端 build 通过
- [x] 3.2 手工验证：未配置时行为与现状一致；页面存假 Key → 测试报 Key 无效；清掉后回退 mmx 登录；一键配音仍可用
