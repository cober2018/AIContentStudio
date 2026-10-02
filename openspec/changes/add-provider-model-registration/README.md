# Provider and model registration

## PRD / 需求背景
用户要求厂商 API/Key 登记、获取模型、保存后按功能选择；指定 CPA 三个模型，以 gemini-3.8-flash-high 为默认。已进入 apply；登记配置写入本地 SystemSetting，CPA `/models` 实际返回 401，发现保持未验证，未执行生成。

## 目录结构
proposal.md / design.md / tasks.md，specs/provider-model-registration 与 specs/product-settings 两份增量契约。

## 已完成
源码边界核对、两批实施计划；密钥没有放入文件。

本轮独立临时浏览器实际通过手动登记/保存刷新、空key保留与安全空字段、双窗口409且草稿未丢。临时库revision5实际消费者读取generate→model-one、text_master_edit→model-two，未发送模型请求或修改正式配置。现有全量1661 passed/28 skipped、TypeScript/Vite/FE-P1、Ruff/strict33/33/diff通过；限定service/UI独立复核APPROVE，登记4/4。复核员验证源码/独立CAS与组件，不宣称其独立重跑主agent浏览器。

## 待完成 / TODO
规格同步/归档仍需单独授权；CPA鉴权/真实模型执行保持未验证。不得把登记与本地验收成功误报为供应商鉴权或生成能力已验证。

## 关键设计决策
复用 SystemSetting 与已有能力路由；精确可信 LAN endpoint 而非全局 SSRF 放行；仅保存选中模型；默认不覆盖显式功能选择；API key 写入型、读取脱敏；模型名不证明媒体能力。无新表/迁移，既有安全存储不冒充加密 vault。

## 依赖 & 启动
沿用现有 FastAPI/React/OpenSpec 启动与依赖。规格校验：`OPENSPEC_TELEMETRY=0 openspec validate add-provider-model-registration --strict`。实际模型调用额度另授权；不 push/deploy/生产迁移。
