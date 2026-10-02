## 1. Batch A — 登记与持久化闭环

- [x] 1.1 /// 确认本方案 apply 授权；复核实际配置/CAS与密钥存储，不打印凭据；实现复用 SystemSetting 的厂商、注册 profile、default_profile 安全读写及旧配置兼容。
- [x] 1.2 /// 实现精确可信 endpoint 策略、限时限量 /models 发现与手动补录；前端登记页、获取/勾选模型、设默认、只读权限及 409 保留草稿完整接入；不执行生成。CPA 本次实际 /models 返回 401，发现结果保持未验证。

## 2. Batch B — 各功能选择与验收

- [x] 2.1 /// 接入实际 purpose/Workflow 消费者选择和既有 media plugin 路由；保存默认不覆盖显式 routes，冻结运行 provenance；无新表/迁移，无未授权付费调用。
- [x] 2.2 /// 按用户批准的验收方式验证保存刷新、脱敏、冲突、默认/显式模型路由、遗留兼容与浏览器；运行 TypeScript/Vite、FE-P1、现有相关后端测试、Ruff、OpenSpec strict、diff-check；记录实际 CPA 登记结果，独立复核后请求归档授权，不推送/部署。证据校准重新开放后，2026-10-02 主agent实际隔离浏览器完成保存/刷新、空key保留、两模型默认/显式选择及双窗口409草稿保留；隔离DB实际消费者路由核对通过；新全量1661 passed/28 skipped、实际build/预算、Ruff/strict33/33/diff通过。独立service/UI CAS/脱敏/清key/路由/组件draft复核APPROVE（未独立重跑浏览器）。CPA `/models` 既有实际401继续未验证，未发起生成或付费请求。证据见 docs/FE_F7_FINAL_LOCAL_GATES.md；不以本任务推断供应商可执行/verified。
