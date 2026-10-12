# Provider and model registration

## 2026-10-06 当前 CPA 地址：本机隧道已生效

用户已授权立即切换到`http://127.0.0.1:8317/v1`。通过原CAS API将正式models revision4推进到5，仅修改CPA base_url及同值trusted_private_endpoint；数据库逐字段对比确认Key、profiles、default/routes、media_plugins/capability_routes/policies全部保持。产品模型发现返回200/32模型，三个已登记CPA模型均存在；当前默认仍为gemini-3.8-flash-high。这证明认证/目录连通，不证明生成或文章质量。原401记录是历史证据。

实现只允许管理员明确登记的精确literal127.0.0.1，保存/执行共享目标检查；localhost别名、其他loopback、链路本地/metadata、代理/重定向及媒体下载边界不放宽。页面连接安全文案同步本机隧道。配置修改前保留私有SQLite备份；API/原Worker沿用既有launchd方式刷新，无执行中/保留/计划中任务，四队列为空。未生成、未重试原Unknown、未迁移、提交、推送或归档。

门禁：隔离拒绝→通过探针（精确隧道、6类拒绝目标、Key保留、LAN与CAS）；现有定向后端95 passed/1既有warning；TypeScript/Vite/FE-P1、Ruff、OpenSpec strict38/38、diff-check通过。依赖/启动方式不变，保持SSH隧道在127.0.0.1:8317监听；归档/主规格同步仍需单独授权，真实生成质量继续单独验收。

## PRD / 需求背景
用户要求厂商 API/Key 登记、获取模型、保存后按功能选择；指定 CPA 三个模型，以 gemini-3.8-flash-high 为默认。已进入 apply；登记配置写入本地 SystemSetting，CPA `/models` 实际返回 401，发现保持未验证，未执行生成。

## 目录结构
proposal.md / design.md / tasks.md，specs/provider-model-registration 与 specs/product-settings 两份增量契约。

## 已完成
源码边界核对、两批实施计划；密钥没有放入文件。

本轮独立临时浏览器实际通过手动登记/保存刷新、空key保留与安全空字段、双窗口409且草稿未丢。临时库revision5实际消费者读取generate→model-one、text_master_edit→model-two，未发送模型请求或修改正式配置。现有全量1661 passed/28 skipped、TypeScript/Vite/FE-P1、Ruff/strict33/33/diff通过；限定service/UI独立复核APPROVE，登记4/4。复核员验证源码/独立CAS与组件，不宣称其独立重跑主agent浏览器。

## 待完成 / TODO
规格同步/归档仍需单独授权；CPA鉴权与模型目录已由上述本机产品入口验证，真实模型生成质量保持未验收。不得把目录发现成功误报为生成能力或质量已验证。

## 关键设计决策
复用 SystemSetting 与已有能力路由；精确可信 LAN/literal127.0.0.1隧道 endpoint 而非全局 SSRF 放行；仅保存选中模型；默认不覆盖显式功能选择；API key 写入型、读取脱敏；模型名不证明媒体能力。无新表/迁移，既有安全存储不冒充加密 vault。

## 依赖 & 启动
沿用现有 FastAPI/React/OpenSpec 启动与依赖。规格校验：`OPENSPEC_TELEMETRY=0 openspec validate add-provider-model-registration --strict`。实际模型调用额度另授权；不 push/deploy/生产迁移。
