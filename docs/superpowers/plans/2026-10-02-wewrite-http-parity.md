# WeWrite HTTP Upload and Draft Creation Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task after explicit apply authorization.

**Goal:** Make AIContentStudio's account-bound WeChat draft adapter use the same proven HTTP wire behavior as the installed WeWrite implementation while retaining product safety boundaries.

**Architecture:** Keep `OfficialTransport` as the product-owned transport and port only WeWrite's request semantics: token GET, multipart upload construction, UTF-8 article JSON, and `media_id` confirmation. Keep account-scoped runtime resolution, frozen asset bytes, durable Attempt/CAS, redaction, draft-only action, and unknown/no-retry behavior in AIContentStudio.

**Tech Stack:** Python 3.12, stdlib HTTPS transport, SQLAlchemy delivery Attempt model, existing pytest transport/delivery suites, OpenSpec.

---

### Task 1: Align transport wire protocol

2026-10-02 correction: the previous implementation changed the method to GET but left `_PATHS["token"]` pointing to `/cgi-bin/stable_token`. The existing wire assertion also retained the old path, so its passing result did not prove the documented parity. The latest isolated real Attempt stopped at token with `official_api_rejected`; no upload or draft creation completed. Historical Unknown records stay unchanged.

/// Correct existing endpoint/dispatch assertions → reproduce locally with no network → change only token endpoint and truthful rejected-response dispatch evidence → rerun existing targeted/full backend gates → update acceptance/progress; no new test file, external call, retry, commit or archive.

- [x] Correct token endpoint to GET `/cgi-bin/token` and retain `dispatched=True` when a sent request receives an API rejection.
- [x] Verify existing protocol/diagnostic assertions: 110 targeted passed; full backend 1660 passed / 28 skipped / 8 existing warnings (81.27s). Ruff/change strict/diff passed; independent narrow review APPROVE. Real platform success remains unproven.

**Files:**
- Modify: `apps/api/app/services/wechat_official_transport.py`
- Modify: existing `apps/api/tests/test_f7_wechat_official_transport.py` only; do not add a new test file.

- [x] Change token request from stable-token POST JSON to WeWrite-compatible GET `/cgi-bin/token` query semantics without exposing secrets in logs or persisted metadata.
- [x] Make multipart upload preserve the frozen asset filename/MIME while retaining exact bytes and bounded request construction.
- [x] Change create payload headers/body encoding to UTF-8 `application/json; charset=utf-8`, include `show_cover_pic: 0`, and preserve existing approved article fields.
- [x] Keep strict response validation: cover requires `media_id`, inline requires `url`, draft creation requires a valid non-empty `media_id`.
- [x] Update existing focused tests and run the transport/delivery suites: 110 passed, one existing warning.

### Task 2: Verify product-path behavior

2026-10-02 user explicitly authorized one new draft-box-only experiment after the endpoint fix. Create a new ContentUnit and approved Candidate in a private copy, retain all three old Unknown attempts, run rollback-only preflight, then execute exactly once through the existing runner. Provision an explicit private process identity key for this isolated copy only; no production key/config changes. Do not retry a failed new Attempt or switch to the CLI. Record actual media_id evidence if successful; the general contract remains unresolved.

Outcome: preflight passed; new Candidate/Target/Attempt 4 in `/private/tmp/aics-wechat-token-fixed-vlhp68/acceptance.sqlite`. Real token succeeded, asset_0 response remained unconfirmed, no create/media_id. The one-shot authorization has been consumed; no retry. Old Attempts 1–3 match the source database exactly. Preserve preview/evidence and investigate safe response-stage diagnostics before any new external test.

**Files:**
- Modify: `apps/api/app/services/wechat_official_delivery.py` only if the transport contract requires an adapter-level field adjustment.
- Modify: `progress.md`, `findings.md`, `task_plan.md`, `README.md` with evidence only after verification.

- [x] Run targeted backend regression with `PYTHONPATH=.`: 110 passed, one existing warning.
- [x] Run full backend regression: 1660 passed, 28 skipped, 8 existing warnings; strict OpenSpec, Ruff and `git diff --check` passed.
- [x] The explicitly authorized one-shot product-path experiment was executed before the endpoint correction: Attempt 3 stopped at token with official_api_rejected, no upload/create/media_id. Execution is recorded, not counted as successful platform acceptance; no retry follows from this checkbox.
- [ ] Do not commit, push, deploy, run production migrations, or archive until separately authorized.

### Task 3: Safe local transport diagnostics (authorized)

/// Amend bounded diagnostic spec → reproduce missing detail without network → classify transport phases and refusal reasons → filter optional fields at Attempt persistence → existing regressions/full backend and narrow independent review → update evidence. No external requests or historical backfill.

- [x] Add optional fixed phase/reason, integer HTTP status and categorical response type without raw response/header/error retention.
- [x] Preserve strict response acceptance, Unknown/no-retry, and the existing two-field diagnostic contract when optional information is absent.
- [x] Verify locally using existing suites and transient no-network probes; no new persistent test code, migration, credentials or real API calls. Final: targeted129, backend1660/28 skipped/8 warnings (74.80s), strict33, Ruff/diff PASS; independent diagnostic-only review APPROVE. Real platform and whole-stage closure remain pending.

### Task 4: One newly authorized diagnostic draft test

2026-10-02 user explicitly authorized one new draft-box test after the diagnostic patch. This is a new Candidate in a private copy, not retry permission for any old Unknown; preserve all four historical Attempts and use the same previously approved exact cover/account. Title: “诊断联调测试，请勿发布”. Only product Delivery, no CLI fallback/publication/general verification/production writes.

/// Private read-only backup + exact cover/key → new Unit/Master/Variant/checks/Candidate/Approval via existing API → rollback-only preflight → exactly one execute → read only safe Attempt diagnostics/media_id → compare all historical rows and record outcome. No business-code change or second attempt.

- [x] Prepare isolated approved candidate and zero-network preflight: Candidate5 in `/private/tmp/aics-wechat-diagnostic-7OrCjk/acceptance.sqlite`, final HTML118 bytes, exact previous cover19723 bytes; all four old Attempts unchanged, preflight rollback adds no Target/Attempt.
- [x] Execute once; preserve ambiguous results and inspect safe diagnostics without retry. Attempt5 token completed, asset_0 HTTP200/text/plain refused by response_headers/content_type; no create/media_id. All four old Attempts unchanged.
- [x] Update acceptance/README/progress/findings with actual evidence; no commit/archive/push/deploy/production migration. WeWrite source directly parses resp.json(), unlike product MIME gate; local compatibility correction requires next scoped authorization, not automatic retry or CLI fallback. This checkbox records execution, not successful platform acceptance.

### Task 5: Authorized local text/plain JSON compatibility

/// Amend existing response contract → reproduce text/plain rejection with the existing in-memory wire fixture → minimally allow application/json or text/plain → verify strict parsing/required fields and existing regressions → independent narrow review and record actual gates. No new real requests, repository test code, historical mutations, commit/archive or deployment.

- [x] Record explicit user authorization and bounded response contract before code changes.
- [x] Accept text/plain only through the unchanged strict JSON parser and endpoint field validators. RED reproduced valid JSON rejected at content_type; GREEN verifies 15 endpoint successes (five operations × JSON/plain/charset) and 16 refusal cases with the existing in-memory fixture, zero network.
- [x] Run existing targeted/full suites, transient no-network compatibility probes, Ruff/OpenSpec/diff and narrow independent review; keep real acceptance tasks open.

Fresh local gates: 129 targeted passed/1 existing warning (14.09s); full backend1660 passed/28 skipped/8 existing warnings (77.68s); strict33/33, Ruff and tracked/untracked diff checks passed. No frontend/build rerun is claimed because frontend was unchanged. Independent replacement reviewer APPROVE for the single MIME condition; first reviewer failed to start due to capacity. No real account request or historical DB mutation. This is local patch completion, not real account acceptance or whole F7 completion.

### Task 6: One newly authorized test after response compatibility correction

User explicitly approved one new draft-box test. Use a private read-only backup preserving all five historical Unknown Attempts and the previously approved exact account/cover, title “响应兼容测试，请勿发布”. Create a new approved Candidate through product APIs, run rollback-only preflight, then execute exactly once. No retry/CLI fallback/publication/general contract enablement/production mutation.

/// Private backup + exact cover/key → API Unit/Master/Variant/checks/freeze/approve → preview + rollback-only preflight → one execute → safe media_id/evidence read → compare old Attempt rows and record actual outcome.

- [x] Prepare new isolated approved Candidate and zero-network preflight: Candidate6/Unit6/Master7/Variant7, HTML118 bytes, exact cover19723 bytes, four explicit semantic-warning dispositions; old Attempts1–5 unchanged, rollback leaves Target/Attempt counts at5.
- [x] Execute exactly once and verify persisted safe remote ID/step evidence without retry: Target6/Attempt6 succeeded, token/asset_0/create completed, valid returned media_id hash=`61bbf2b1b617cb31befa0cb656ac4e4ff5558f07479cee60d5fa8ea47f3c34f9`, target awaiting_manual_receipt. No optional remote readback or second create.
- [x] Record actual outcome in acceptance/progress/README; five old rows unchanged, source count5/new private count6, no Receipt/PublishedContentRecord. Only task2.8a closes (19/22); general contract and whole F7 remain incomplete.

Execution status: the escalated command was rejected by auto-review BEFORE process creation because it requires explicit authority naming the exact destination account, test content and cover. No network, Target6 or Attempt6 was created; one-shot API execution has not occurred. Preserve the private preview/database, do not bypass the rejection through another command/tool, and ask the user to confirm those exact external-write inputs before proceeding.

Authorization update: user expressly confirmed “授权将以上正文和封面发送到该公众号草稿箱一次” after being shown exact title/body/cover and destination (existing WeWrite/new_media account). Fresh read-only checks confirm those frozen inputs, original cover hash/19723 bytes, no new Target/Attempt and all five old Attempts unchanged; rollback-only preflight passed again. Proceed with the same runner once, no public publication or retry.

User acceptance: supplied backend draft-box screenshot matches “响应兼容测试，请勿发布” and the exact reused yellow test cover, updated14:31. User agreed this item passes. Record manual visible-draft acceptance only, no remote body-readback claim, database Receipt/Verification write, new API request or whole F7 closure.

### Task 7: Consolidate bounded acceptance, then reconcile MiniMax originals

/// Read-only persisted Attempt/history check → fresh existing gates → independent task-level review → current acceptance/matrix/TODO reconciliation → read original MiniMax tasks/bytes/key availability; no new supplier call or acceptance.

- [x] Persisted success and unchanged five old Attempts verified; receipt/publication/verification counts0. No WeChat calls.
- [x] Fresh129 targeted/1660 backend/28 skipped, Webbuild/budget, strict33/33, scopedRuff/diff PASS. Independent8.5 PASS; general verification and full2.9 remainPARTIAL.
- [x] Current record and pending TODO synchronized; original-filename parity discrepancy disclosed without relaxing specification.
- [x] Original MiniMax TTS bytes/hash/WAV remain valid and unaccepted; originalimage Unknown without job unchanged. Original receipt key unavailable in this process; no re-sign, resubmit or fabricated recovery.
- [ ] Complete broader WeChat limits/scope/final commit/archive only with their required evidence/authority. Continue MiniMax supplier/rights/restart closure with explicit limits, retaining all existing F7 obligations.
