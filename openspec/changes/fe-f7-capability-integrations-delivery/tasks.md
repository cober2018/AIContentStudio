## 0. Baseline and registry audit
- [x] 0.1 Start after F6E implementation gates pass.
- [x] 0.2 Inventory current PluginRegistry, Connector, Settings, provider and Publisher code.
- [x] 0.3 Map current keys to North Star capability kinds without breaking existing resolvers.
- [x] 0.4 Record backend/frontend/OpenSpec/migration baseline.
- [x] 0.5 No provider capability is promoted from assumption.

## 1. Durable capability persistence
- [x] 1.1 Add CapabilityRegistration model.
- [x] 1.2 Add CapabilityVerification model.
- [x] 1.3 Add kind/status/scope/index constraints.
- [x] 1.4 Exclude secret/token/cookie/raw path fields by schema.
- [x] 1.5 Add config fingerprint/version identity.
- [x] 1.6 Add additive migration.
- [x] 1.7 Add downgrade preflight for retained verification history.
- [x] 1.8 Validate SQLite/PostgreSQL paths.
- [x] 1.9 Add authorization/audit tests.
- [x] 1.10 Prove runtime availability rechecks exact registration version/config fingerprint, verification scope/expiry and loaded implementation; never infer executable from a DB row.
- [x] 1.11 Keep the explicit Data Source Plugin → ConnectorEndpoint mapping inside planned registration/config fields; stop for spec revision if another durable business object is truly required.

## 2. Registry expansion
- [x] 2.1 Add model_provider kind.
- [x] 2.2 Add tool_provider kind.
- [x] 2.3 Add data_connector kind.
- [x] 2.4 Add search_provider kind.
- [x] 2.5 Add image_provider kind.
- [x] 2.6 Add video_provider kind.
- [x] 2.7 Add tts_provider kind.
- [x] 2.8 Add asr_provider kind.
- [x] 2.9 Add channel_adapter/browser_automation kinds.
- [x] 2.10 Preserve existing node/rule/renderer/publisher/skill compatibility.
- [x] 2.11 Exact version resolution only.
- [x] 2.12 Add descriptor/inventory tests.

## 3. Connector→Data Source execution
- [x] 3.1 Add explicit typed `data_source_plugin_key` and endpoint mapping on CapabilityRegistration; Data Node source_ref pins registration ID/version. Use endpoint ID plus effective configuration/credential-version fingerprint instead of inventing an Endpoint revision; unverifiable credential version remains unverified.
- [x] 3.2 Preserve Connector env-secret references.
- [x] 3.3 Add manual pull through capability.
- [x] 3.4 Add Workflow Data Node execution through capability.
- [x] 3.5 Persist DataSnapshot/SourceDocument/Fact provenance.
- [x] 3.6 Bound pagination/timeouts/body sizes.
- [x] 3.7 Treat external payload as untrusted data.
- [x] 3.8 Add failure/retry/audit behavior; `ConnectorEndpoint.last_pull_error` and all returned diagnostics must use bounded safe reason codes, never raw exception or response text.
- [x] 3.9 Do not mark unrelated plugin keys connected.
- [x] 3.10 Add connector integration tests.

## 4. Material search provider
- [x] 4.1 Define search provider protocol/capability.
- [x] 4.2 Return bounded candidate metadata only.
- [x] 4.3 Add explicit import/save action.
- [x] 4.4 Download/verify bytes/MIME/hash.
- [x] 4.5 Persist only a positively validated stable public citation URL in `MaterialRevision.source_url`, or a bounded source identifier plus one-way URL/input hash when the URL is ambiguous; never persist a signed/credential-bearing/expiring fetch or preview URL in material metadata, audit, events or API results. Preserve license/provenance without raw provider payloads.
- [x] 4.6 Require rights fields before public-use readiness.
- [x] 4.7 Add project attachment flow.
- [x] 4.8 Add unavailable/provider failure tests.
- [x] 4.9 Prove search preview is non-public-ready, accepted result bytes/license/rights are exact, and Project attachment uses a revision reference visible across Units.

## 5. Image/video providers
- [x] 5.1 Define image generation/variation protocol.
- [x] 5.2 Define video generation protocol.
- [x] 5.3 Persist accepted output as MaterialRevision.
- [x] 5.4 Persist provider/version/prompt/input refs/hash metadata.
- [x] 5.5 Respect model/public/commercial rights.
- [x] 5.6 Require explicit accept before Master use.
- [x] 5.7 Add async/timeout/failure/unknown provider-result handling.
- [x] 5.8 Add mock + at least one configured real adapter path where repository settings support it.
- [x] 5.9 Do not mark adapter verified without real test.
- [x] 5.10 Redact nested provider request/response/errors across API, Material metadata, AuditLog, ProjectEvent and settings projections; specifically prevent raw prompts/requests, signed URLs and secret fragments in existing `MaterialRevision.prompt_text`, `source_url`, `source_metadata_json`, `metadata_json` and `ConnectorEndpoint.last_pull_error`; add successful-result and error-path negative secret-leakage checks.
- [x] 5.11 Reject success-without-bytes, unsupported MIME, missing/ambiguous license and wrong render-input hash without creating MaterialRevision or Master provenance.

## 6. TTS/ASR
- [x] 6.1 Define TTS provider protocol.
- [x] 6.2 Store TTS audio as exact MaterialRevision.
- [x] 6.3 Define ASR provider protocol.
- [x] 6.4 Return bounded transcript/cues.
- [x] 6.5 Explicit accept/save required to change Video Master.
- [x] 6.6 Record provider/runtime/source hashes.
- [x] 6.7 Add rights/failure/provenance tests.

## 7. Renderer capability
- [x] 7.1 Register renderer capability descriptors.
- [x] 7.2 Declare supported modality/schema/form/MIME.
- [x] 7.3 Record deterministic/verified/manual property.
- [x] 7.4 Persist renderer verification scope.
- [x] 7.5 Save media renderer output as MaterialRevision.
- [x] 7.6 Bind exact render-input hash.
- [x] 7.7 Add stale/version change tests.

## 8. Publisher capability
- [x] 8.1 Persist exact account/channel/form/action/version verification.
- [x] 8.2 Keep copy_package as safe local capability where packageable.
- [ ] 8.3 Preserve existing WeChat WeWrite behavior and verify only real supported scopes.
- [x] 8.4 Automatic actions require verified capability + account authorization.
- [ ] 8.5 Publisher receives immutable approved package only; v5 WeChat article reaches legacy WeWrite input solely through validated deterministic frozen title/body/digest/cover projection before attempt preparation, with no v3/v4 fallback.
- [x] 8.6 No publisher content rewrite/truncation/asset generation.
- [x] 8.7 Unknown outcome remains Unknown.
- [x] 8.8 Add reconciliation/read-back/human verification flow. Existing scoped human verification plus locked, evidence-hashed, exact-attempt reconciliation/receipt and explicit UI confirmation implemented; synthetic acceptance is not real-account verification (10.5/10.6 remain pending).
- [x] 8.9 Douyin/Xiaohongshu remote actions remain unavailable unless real adapter verified.
- [x] 8.10 Add idempotency/duplicate-side-effect tests.
- [x] 8.11 Remove the legacy `allow_unverified_auto_draft` execution bypass for new remote effects; preserve old targets/attempts as readable history and report the behavior change.
- [x] 8.12 Recheck verification at execution after target creation, including account/form/action/version/fingerprint/expiry; revoked scope creates no new remote attempt.
- [x] 8.13 Ensure WeWrite subprocess output and all PublisherResult fields are allowlisted/redacted before persistence or API return; add nested secret/error negative checks.

## 9. Settings and capability UI
- [x] 9.1 Add capability inventory section/projection.
- [x] 9.2 Distinguish configured/executable/verified/unavailable.
- [x] 9.3 Show last verification/scope safe metadata.
- [x] 9.4 Add explicit probe/verify actions.
- [x] 9.5 Read-only inventory triggers no network calls.
- [x] 9.6 Preserve role-based editability and secret masking.
- [x] 9.7 Add provider configuration guidance/status without fake Save actions.
- [x] 9.8 Prove read-only inventory performs no provider/Connector probe and viewer cannot invoke verification.

## 10. Real integration acceptance/final gates
- [x] 10.1 Run Connector integration against configured isolated endpoint.
- [ ] 10.2 Run material search/import with real bytes if configured.
- [ ] 10.3 Run image/video/TTS/ASR real adapter tests only where credentials are provided.
- [x] 10.4 Keep missing credentials explicitly unverified, not failed-complete.
- [ ] 10.5 Run real Publisher verification only with explicit account/side-effect authorization.
- [ ] 10.6 Verify read-back/human evidence before `verified`.
- [ ] 10.7 Full backend/frontend/migration/OpenSpec/Ruff/diff gates.
- [ ] 10.8 Browser Settings/Production/Delivery acceptance.
- [ ] 10.9 Independent security/provider/delivery reviews.
- [x] 10.10 Record capability matrix with verified/unverified reasons.
- [ ] 10.11 Record local implementation commit and ARCHIVE_READY.
- [ ] 10.12 Do not canonical-sync/archive without explicit authorization.
