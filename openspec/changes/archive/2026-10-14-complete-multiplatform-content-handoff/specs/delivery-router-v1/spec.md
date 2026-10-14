## MODIFIED Requirements

### Requirement: Copy package is universal fallback

对没有 verified draft publisher 的平台，系统 SHALL 保证 approved Candidate 至少可以生成格式完整的 Copy Package，包 MUST 保留 media order/placement 和平台交付说明。十二平台/十七形态的现代本地包 SHALL 从 approved frozen v5 payload/render/refs 构建，保留 exact source/target/schema/profile/check/citation/rights/hash，执行实时权利与完整性校验；缺真实素材或不支持 schema MUST fail closed，不回退 v4/v3/Draft。包 SHALL 含平台专属正文/结构、安全来源/声明、实际素材和人工发布指南，MUST NOT 泄露整个事实库/模型受限上下文/私有路径/凭据。

#### Scenario: 无发布器的平台交付

- **WHEN** 平台没有 verified draft publisher
- **THEN** approved Candidate 至少可以生成格式完整的 Copy Package
- **AND** 包保留 media order/placement 和平台交付说明

#### Scenario: 平台独立本地包
- **WHEN** 用户为已批准的知乎回答、B站图文或 X Articles 生成本地包
- **THEN** 包使用对应冻结结构和精确媒体，不调用远端 API
- **AND** 包就绪仅表示人工交付包可用，不自动等同发布或其他形态完成

## ADDED Requirements

### Requirement: Current rollout is local handoff except verified WeChat drafts

本阶段所有十二平台 SHALL 提供 copy_package/manual_handoff，非公众号平台 MUST NOT 因目录/profile/本地验收而启用远端投递或公开发布。公众号既有 auto_draft SHALL 继续受 approved exact Candidate、账号/形态/动作/runtime Verification、独立授权和 durable Attempt 约束；既有成功 media_id/人工确认及 Unknown 不自动重发契约 MUST 保持。此范围确认 MUST NOT 被当作任何新草稿、浏览器发布或公开发送授权。未验证的长帖/Articles 账号资格 SHALL 明确展示，不阻断合法本地包。

#### Scenario: Local target without remote verification
- **WHEN** X/微博等目标没有 remote capability verification
- **THEN** 可选人工交付动作，但远端动作 unavailable，下载不创建发布记录

#### Scenario: WeChat draft is not publication
- **WHEN** 一个明确获准的公众号 auto_draft 成功并经同账号人工确认
- **THEN** 系统只记录该草稿能力/结果，不把它标成公开发布或十二平台远端通过

### Requirement: Exact target account for modern variant delivery

The Delivery Router SHALL authorize modern v5 Variant Candidates independently per concrete destination ContentAccount and MUST NOT enforce `unit.account_id` equality as an unconditional target-account rule for modern cross-platform or same-platform multi-account distribution.

#### Scenario: WeChat-origin unit delivers to Xiaohongshu target
- **GIVEN** a modern Unit created with an explicitly selected WeChat origin Account
- **AND** a reviewed Xiaohongshu Variant Candidate from the same Persona
- **WHEN** delivery to a valid Xiaohongshu Account is authorized
- **THEN** the operation is not rejected solely because the Account differs from `unit.account_id`
- **AND** all normal channel/form/rights/approval checks still run

#### Scenario: Same-platform target B differs from origin A
- **GIVEN** the origin Unit uses Xiaohongshu Account A
- **AND** the Persona also owns Xiaohongshu Account B
- **WHEN** the user prepares and reviews a target-specific modern Candidate for B
- **THEN** B can receive its own authorization and receipt
- **AND** A's authorization/receipt is neither reused nor modified

#### Scenario: Reject target from a different Persona
- **WHEN** a modern Variant Candidate from Persona A is targeted to an Account from Persona B
- **THEN** authorization fails closed even when both Accounts share the same platform

#### Scenario: Account profile requires different candidate
- **GIVEN** Account B needs additional required declarations or a different Account creative/style profile
- **WHEN** a Candidate frozen for Account A is targeted to B
- **THEN** the system requires a valid target-specific adaptation/review or explicit compatibility verification
- **AND** does not silently repoint the Candidate or drop required declarations

#### Scenario: Legacy account pin remains enforced
- **GIVEN** a legacy Candidate was created under account-pinned delivery semantics
- **WHEN** its target Account differs from the frozen historical Account
- **THEN** legacy authorization remains blocked as before, unless a separately specified explicit migration creates a new modern Candidate

### Requirement: Separate authorization and result truth per target

Each target account SHALL receive independent Authorization/Attempt/Receipt with exact frozen account identity, content hashes, delivery method and review evidence; platform type alone SHALL NOT identify a delivery target.

#### Scenario: Two accounts on same platform
- **WHEN** one approved source is intentionally prepared for two Accounts on the same platform
- **THEN** each target has a separate authorization and attempt identity
- **AND** duplicate prevention applies per exact authorized side effect without forbidding a legitimate second account

#### Scenario: Possible dispatch outcome is unknown
- **WHEN** any external delivery action may have been dispatched but confirmation is missing
- **THEN** it remains `unknown`, requires reconciliation/readback or operator confirmation as supported
- **AND** is never automatically retried on the assumption it failed

#### Scenario: Local package is not publication
- **WHEN** a non-WeChat target's approved package is exported or handed to an external operator
- **THEN** the result is a local/manual handoff with provenance
- **AND** no published-content success is recorded merely from export
