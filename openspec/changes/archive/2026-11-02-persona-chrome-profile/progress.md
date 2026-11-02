# progress

- 2026-11-02 方案已写，等用户确认。
- 2026-11-02 已本地实施，未提交：
  - 后端：新 `services/chrome_profiles.py`（读 Chrome 个人资料名、角色选择存系统设置 persona_chrome_profiles、重复占用 409、账号打开只允许自己的入口/主页、用 `open -na` 指定个人资料打开）；路由 GET /settings/chrome-profiles、PUT /content-personas/{id}/chrome-profile、POST /content-accounts/{id}/open-link。
  - 前端：新 `PersonaChromeProfile.tsx`；角色编辑页「浏览器」、概览「浏览器」块；账号页按钮有个人资料时由后端打开，否则新标签；同名个人资料后面带目录名区分。
  - 验证：在正式库副本上验证选择、重复占用、不存在的个人资料、非本账号网址被拒；全量 2441 通过（5 个已知失败）；tsc 通过；API 已重启，接口读到本机 6 个个人资料。
  - 未验证：真正弹出 Chrome 窗口（不在用户屏幕上擅自打开），等用户点。
- 2026-11-02 用户反馈概览里「浏览器」只显示未设置、没地方选：概览的「浏览器」块直接放选择框（编辑资料里的保留）；tsc 通过。
