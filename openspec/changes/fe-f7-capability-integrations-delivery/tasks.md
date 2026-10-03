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
- [x] 8.3 Preserve historical WeWrite reads and its fail-closed remote runtime; implement the approved account-bound publisher.wechat.official@1 supplement and verify only exact real supported account/form/action scopes. Do not inherit WeWrite verification. 2026-10-03 current product Attempt7 succeeded with stored media_id; genuine same-account user confirmation then atomically persisted Receipt1/CapabilityVerification1. Exact bounded account1/wechat/article/auto_draft only, no public publication or unresolved general long-form readiness. New-process repeat receipt is idempotent; six different scope/runtime cases cannot reuse evidence. See docs/FE_F7_SHORT_DRAFT_ACCEPTANCE.md; earlier follow-ups below are historical stages.
  - 2026-10-03 read-only preflight: both earlier succeeded drafts still match the approved account, but their registrations/Attempt runtime fingerprints predate the current implementation and no Receipt/Verification exists. The existing receipt endpoint returns 409 `official_draft_capability_runtime_changed` on an in-memory copy, with zero writes/calls. Close the missing explicit Attempt-to-current-runtime comparison, then obtain separate authorization for one current-version draft and record exact same-account confirmation; do not rewrite old fingerprints or retry Unknown.
  - Historical pre-confirmation stage: explicit successful Attempt runtime comparison was fixed (RED/GREEN, 120 existing targeted/1660 full backend, strict/Ruff/diff, narrow independent APPROVE). Newly authorized original short body/yellow cover was frozen/approved as Candidate7 and sent once through the product official adapter: Target7/Attempt7 succeeded with stored media_id and current matching runtime. Prior six Attempts unchanged; no public publish/readback/formal DB write. The pending confirmation at that stage was subsequently supplied by the user and Receipt1/Verification1 persisted as recorded above.
- [x] 8.4 Automatic actions require verified capability + account authorization. Legacy workflow publish now rejects every new execution before file/CLI work; scoped Delivery gates remain authoritative. Narrow independent safety review APPROVE; general real-account validation remains 8.3/10.5.
- [x] 8.5 Publisher receives immutable approved package only; new official WeChat execution requires the supplement's deterministic official HTML/asset-slot render frozen before Candidate approval, with no post-approval Markdown conversion, enrichment or v3/v4 fallback. Old candidates remain readable/local-packageable but cannot gain a remote render implicitly. 2026-10-02 task-level independent review PASS plus fresh129 targeted/1660 backend proves the implementation boundary; actual short-draft Attempt6 consumes frozen render/resources. This does not close 8.3/10.5 general-contract verification; original-filename parity was addressed separately in the archived supplement.
- [x] 8.6 No publisher content rewrite/truncation/asset generation. Removed legacy direct execution/truncation/placeholder path; schema1–5 and both opt-in flags reject without export/CLI. Account-bound immutable publisher implementation remains8.3/8.5.
- [x] 8.7 Unknown outcome remains Unknown.
- [x] 8.8 Add reconciliation/optional read-back/human verification flow. Existing scoped human verification plus locked, evidence-hashed, exact-attempt reconciliation/receipt and explicit UI confirmation implemented; synthetic acceptance is not real-account verification (8.3/10.5 remain pending). Successful draft acceptance does not require `draft/get`.
- [x] 8.9 Douyin/Xiaohongshu remote actions remain unavailable unless real adapter verified.
- [x] 8.10 Add idempotency/duplicate-side-effect tests.
- [x] 8.11 Remove the legacy `allow_unverified_auto_draft` execution bypass for new remote effects; preserve old targets/attempts as readable history and report the behavior change. Target route flag and direct workflow legacy_remote_publish cannot authorize new effects; historical key/read contracts retained.
- [x] 8.12 Recheck verification at execution after target creation, including account/form/action/version/fingerprint/expiry; revoked scope creates no new remote attempt.
- [x] 8.13 Ensure WeWrite subprocess output and all PublisherResult fields are allowlisted/redacted before persistence or API return; add nested secret/error negative checks. Legacy workflow no longer invokes subprocess or returns raw diagnostics; fixed safe refusal and existing delivery redaction preserved. Narrow safety review APPROVE.

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
- [x] 10.2 Record the user's explicit deferral of Commons live search/import and close this acceptance item administratively; do not claim real import PASS or promote that provider to verified.
  - 2026-10-03 lifecycle authorization preserves the earlier user decision to defer Commons. No live Commons calls or byte import were executed for this closure. Future real acceptance requires a separately authorized resumption.
- [x] 10.3 Run image/video/TTS/ASR real adapter tests only where credentials are provided.
  - 2026-10-03 scoped acceptance closed after evidence review: real MiniMax image-01 task remains result_ready/rev3 with exact JPEG33997 bytes/hash; image formal acceptance/rights are not inferred. Formal speech-2.8-hd TTS task is accepted/rev4→MaterialRevision6→Project1/Text Master9; actual MiniMax WAV/test-MP4 audio ASR and local user-video→43 cues→Video Master5 acceptance are recorded separately. Read-only records/bytes rechecked, 119 existing delivery/capability/ASR regressions passed and limited independent evidence review approved. No new vendor request. MiniMax video/H3 is user-excluded, not PASS; generic video protocols/history/offline regressions remain. CPA media remains unverified and no native Google/xAI adapter is required by the approved scope.
- [x] 10.4 Keep missing credentials explicitly unverified, not failed-complete.
- [x] 10.5 Run real Publisher verification only with explicit account/side-effect authorization. 2026-10-03 explicit new one-shot authority consumed once by current product Attempt7; user saw the same account's latest draft and confirmed acceptance. Receipt1/Verification1 real persistence/current runtime and scope checks passed without another WeChat request. Only the exact bounded draft-create scope is verified, not public publication, draft readback or every long-form contract.
  - Reuses 8.3's exact current-version account/article/auto_draft gate; prior one-shot authorities are consumed. No new draft or successful-draft readback was requested by this local preflight.
  - Fresh one-shot authorization was explicitly granted and consumed by the successful current Attempt7 at 16:42 Asia/Taipei; no repeat is needed or allowed. Genuine same-account human confirmation has now been supplied and atomically recorded; it was not inferred from API success.
- [x] 10.6 Close the successful-draft read-back requirement by explicit user decision: a valid `media_id` persisted on the exact successful Attempt plus documented human confirmation in the same account's draft box completes the bounded creation acceptance. The previously approved draft has these two pieces of evidence. No `draft/get` was executed or claimed; general scoped CapabilityVerification remains 8.3/10.5 and Unknown reconciliation is unchanged.
- [x] 10.7 Full backend/frontend/migration/OpenSpec/Ruff/diff gates. 2026-10-01 fresh isolated backend1629 passed/28 skipped/9 warnings; TypeScript/Vite/FE-P1 PASS (projects224.89kB/72.96gzip), full app Ruff PASS after semantics-preserving cleanup of12 baseline findings; native PostgreSQL16 selected passed and full upgrade→f7c000000001→F7 down/up PASS, SQLite migration/history guards included in full suite; OpenSpec strict31/31/diff PASS. Independent lint review APPROVE; temporary container/volume confirmed removed. This local gate does not close real-platform 10.2/10.3/10.5 or archive readiness.
- [x] 10.8 Browser Settings/Production/Delivery acceptance. Existing local UI flows revalidated in 52 gates; actual Text/Graphic rendering and five-form v5 local ZIP are distinguished from image/search/ASR Provider fixtures and reconciliation UI transport fixture in docs/FE_F7_BROWSER_REVALIDATION.md. Real supplier/account acceptance remains pending under 10.2/10.3/10.5; this does not close final F7 gates.
- [x] 10.9 Independent security/provider/delivery reviews. Whole-stage Scope B APPROVE; Scope A review found Connector code identity and Commons fingerprint instability, both reproduced RED and fixed, then independently re-reviewed APPROVE. Composite local review only; real platform evidence remains 10.2/10.3/10.5, full gates10.7 and commit/archive remain separate.
- [x] 10.10 Record capability matrix with verified/unverified reasons.
- [ ] 10.11 Record local implementation commit and ARCHIVE_READY.
- [ ] 10.12 Do not canonical-sync/archive without explicit authorization.
## 11. Approved original-HTML product draft closure

- [x] 11.1 Validate bounded original HTML against canonical visible blocks and exact image slots; preserve inline styling without unsafe active content.
- [x] 11.2 Freeze official renderer v3 before approval; preserve old hashes and original multipart filenames.
- [x] 11.3 Separate exact HTML one-shot authority from short-draft authority; keep general verification and Unknown safety gates.
- [x] 11.4 Run existing regressions and isolated original-HTML product-chain preflight without fabricated verification/check records.
- [x] 11.5 Execute the explicitly approved article/cover/account once to drafts, persist media_id and safe evidence; no public publish or automatic readback/retry. 2026-10-02 fresh isolated AIContentStudio Candidate/Approval/Target/Attempt: nine exact uploads, one draft/add, valid media_id persisted; prior Unknown remains unchanged. This closes only the bounded original-HTML experiment, not general Publisher verification.
