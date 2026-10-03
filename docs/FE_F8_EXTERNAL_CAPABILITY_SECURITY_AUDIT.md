# FE-F8 外部能力安全审计

日期：2026-10-04

本记录以正式验收基准 `SQLite + 本地素材库 + loopback-only` 为范围。它只记录当前代码中已经存在并可在本机复核的边界；不把远程账号、生产 secret provider 或多主机部署冒充为已验收。

## 结论

| F8 项 | 本机结论 | 证据边界 |
|---|---|---|
| 6.1 统一超时/响应体上限 | 本机实现/探针/回归与独立复审通过 | `url_fetch.OUTBOUND_HTTP_POLICIES`集中按能力的预算，TCP/TLS/read/send使用绝对剩余deadline；不把所有生成操作压成抓取的10秒。见下表。 |
| 6.2 可配置 outbound host 限制 | 本机实现/探针/回归与独立复审通过 | 可选 `OUTBOUND_ALLOWED_HOSTS` exact-host CSV，在可控制 HTTP 路径的 DNS/发送前拒绝不允许的 host。CLI 内部网络明确不在该 HTTP policy 下。 |
| 6.3 最小权限凭据 | 本机凭据隔离与独立复审通过 | HTTP 使用对应 provider/endpoint/account 的凭据，跨域不转发；MiniMax CLI 只继承基础环境变量，不继承 CPA/微信/其他 secret。供应商后台 grant 和 production Secret Provider 不由离线探针证明。 |
| 6.4 显式副作用授权 | 已满足 | DeliveryTarget/CapabilityVerification 绑定 channel、form、action、账号和 publisher；只读库存不触发远端动作。 |
| 6.5 幂等与 Unknown | 已满足 | DeliveryAttempt/Receipt 使用幂等键；超时和无法确认进入 `unknown`/reconciliation，不自动重发，也不进入已发布历史。 |
| 6.6 只读库存无 probe/pull | 已满足 | Legacy Settings 原有 dsh 自动探测已移除，零 HTTP 调用，UI 如实显示 `not_probed`。 |
| 6.7 verify/probe/delivery 审计 | 已满足 | 读取历史 audit 时重建字段和类型白名单，worker 及 Source URL 传输错误仅固定分类，无 raw exception/chain。 |
| 6.8 安全回归 | 已满足（本机范围） | 既有回归加临时 RED/GREEN 覆盖日志、字段类型、method cardinality、no-probe、流式读取和跨域 query；不新增永久测试。 |

## 关键实现边界

- `resolve_publisher()` 和 `authorize_target()` 先验证精确渠道/形态/动作，再允许进入副作用路径。
- 公众号官方适配器要求精确账号范围、运行时指纹和能力验证；不满足时返回 unavailable/blocked，而不是调用未知账号。
- `safe_publisher_result()` 只允许有限的状态、远端 ID、渠道和原因码，远端原始错误不会进入持久审计。
- `CapabilityVerification` 的 scope 与 registration、运行时 fingerprint 和 evidence hash 必须一致。
- `product_settings.capability_inventory()` 只投影已存状态；`probe_data_source_capability()`、publisher verification 等动作均为显式写操作。
- local package/manual handoff 不会创建 `PublishedContentRecord`；只有真实 `human_confirmed` receipt 才能进入发布历史与学习链路。
- OpenAI-compatible 注册模型和旧环境配置共用 `provider_request()`：请求体上限 1 MB、响应体上限 2 MB，发现 10 秒、聊天生成 120 秒；禁止环境代理并固定已验证目标，请求大小/host 拒绝在 DNS 前完成。

## 本机结论与未来义务

6.1–6.3在本机实现、探针、回归及独立批准后关闭；没有因loopback而豁免出站安全。供应商后台grant、CLI内部HTTP、生产Secret Provider仍明确不由本次证明。此前总体安全审查和最终定向blocker闭环共同构成本机结论，不把定向审查描述为从零重做全路径审计。

本批已修：HTTP method 仅有限集合，未知值归 `OTHER`；entity ID 只接收真实 int（非 bool/正文），trace 拒绝 JWT 形状；legacy fetch 在超限时停止读取，跨域含 header/body 或任一 hop/query 时拒绝转发；backup integrity 使用只读源连接；OpenAI-compatible 模型请求已迁入统一有界路径，并补齐 deadline 耗尽拒绝与非法响应结构分类。安全独立复核此前指出的残余各自RED/GREEN验证，最终Harvey定向复审APPROVE，6.1–6.3和10.8已关闭。
## Batch L 历史修补（由 Batch M 校准）

此前 Batch L 将 Commons、生图、聊天都压为 10 秒，虽有界但会损害既有生产能力，不能作为最终设计。Batch M 改为统一策略入口、按能力预算；以下是当前实现。

这批只证明本机安全边界、凭据分离与既有回归兼容性，不等同于供应商能力验证、后台grant最小权限证明或生产部署验收。此前“复核前开放”状态已由下方2026-10-04定向批准替代。

## Batch M：当前策略与证据

| 能力 | 时间预算 | 请求字节 | 响应字节 |
|---|---:|---:|---:|
| URL Import | 10 s | 1,000,000 | 5 MiB |
| bounded Connector | 10 s | 1,000,000 | 1,000,000 |
| 模型发现 | 10 s | 1,000,000 | 2,000,000 |
| 聊天生成 | 120 s | 1,000,000 | 2,000,000 |
| OpenAI 生图 | 25 s | 1,000,000 | 8 MiB；解码图片另限 5 MiB |
| Commons | 15 s | 0（GET） | 5,000,000；元数据另限 1,000,000 |
| 微信官方 HTTP step | 25 s | 11 MiB | 1 MiB |
| MiniMax 下载 | 120 s | 0（GET） | 30 MiB |
| dsh 显式状态探测 | 2.5 s | 0 | 只读响应头，不消费响应体 |

抓取/模型共用 DNS 解析最多两个并发槽/工作线程，单次等待最多 4 秒且不得超过剩余 deadline；微信 DNS 使用独立两个槽和 step 剩余时限。已验证 IP 用于 TCP，原 host 继续用于 TLS/SNI。HTTP 禁止环境代理。URL Import 可受控跳转，但任何 hop 的敏感 header/body/query 跨域都拒绝；其他能力禁止自动跟随重定向。权限和私网限制仍按能力执行，optional host allowlist 不会放宽 SSRF 或 CPA trusted endpoint 校验。

`OUTBOUND_ALLOWED_HOSTS` 默认空字符串，保留既有逐能力 allowlist。若设置，只接受最多 100 个精确域名/IP、总配置最多 5,000 字符；拒绝 wildcard、URL、空条目和非法 DNS label，不匹配 suffix。配置仅为 backend environment，不包含凭据，不自动修改个人环境或 Key。MiniMax CLI 自身的 API 网络不被该 HTTP helper 强制约束；仍由固定命令/region、已批准本地 CLI 配置、300 秒子进程总界限、stdout+stderr 512 KiB 和进程组回收约束。CLI 只继承 PATH/HOME/LANG/LC_ALL/LC_CTYPE/TMPDIR/SSL_CERT_FILE/SSL_CERT_DIR，凭据由其已有配置提供，未读取或变更配置值。

本机临时探针先确认原预算与配置缺口，再验证：聊天 120 秒/生图 25 秒保留、不允许 host 在 DNS 前拒绝、非法 allowlist 拒绝、允许的 CPA LAN host 不被误伤、MiniMax 子进程不继承注入的其他服务 key、dsh query URL 不可执行。没有网络/付费生成/微信请求，没有新永久测试。186 项既有定向通过；全量 1660 passed / 28 skipped / 8 warnings（84.92 秒）；socket-family 兼容修正后生图 28 项及 app/scripts Ruff 通过。独立安全/运维结论仍待返回。

## 2026-10-04 总 deadline 与 URL 日志补验

独立安全 reviewer 指出 idle timeout 与总 deadline 不等价，以及默认 HTTPX INFO 可泄漏查询凭据。真实 loopback RED（仅 127.0.0.1，无远端）在 0.25 秒预算下实际等了 1.278 秒且合成 query token 进入日志。现已用共用 `DeadlineBackend/_DeadlineStream` 对 TCP/TLS/read/每次 socket send 设置剩余总预算，DNS/redirect 沿用相同截止时间；`outbound_scope` 仅抑制当前 HTTPX/HTTPcore 日志，范围外 control 日志正常。模型/image/Commons/MiniMax download/dsh/URL Import/Connector 接入；微信保留原固定 host deadline transport。真实 socket stream 逐 send 截止；无 socket 的内存 transport 通过其有限 write 接口兼容。

GREEN 慢响应头0.251秒、慢响应体0.252秒中止，合成token零日志、普通日志恢复。186既有定向全部通过，Ruff PASS；最终正确apps/api cwd全量1660 passed/28 skipped/8 warnings（84.32秒、exit0）。根cwd的32路径失败保留，不计PASS。

最终独立定向复审Harvey（`01a10298-737c-7562-a81d-23f5d3320ed2`）APPROVE：绝对deadline/query日志两blocker闭合，所有指定调用路径IP pin/TLS原host/host与redirect/字节/Unknown gate保持，CLI环境隔离保持。reviewer只读复审源码，未亲跑全量/浏览器；其loopback bind被沙箱拒绝，不计为测试结果。没有新永久测试、真实生成/微信外发或正式库修改，不把这些探针当供应商grant验证。
