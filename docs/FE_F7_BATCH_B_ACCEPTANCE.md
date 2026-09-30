# FE-F7 Batch B — shared media acceptance slice

## Scope and limitations

Local main based on `1687963`; F7 **67/105**, still implementing. This slice implements typed Image/Video/TTS/ASR interfaces and shared media staging/explicit acceptance, not real-provider readiness or complete ASR/render/search delivery. No additional table or migration. No push/deploy/production migration/canonical archive/remote generation or publishing.

The installed WeWrite image CLI is **unavailable for new typed requests**: launcher/credential labels do not prove effective configuration, and CLI retries uncertain generation internally. Neither manually confirming rights nor the synthetic browser fixture enables that runtime. A configuration-bound, single-attempt actual adapter remains required.

## Implemented boundary

- Actor-scoped, 15-minute, bounded in-memory preview with opaque ID; restart/expiry invalidates it. Cross-worker durable staging remains an explicit F8 concern, not a completed production guarantee.
- Nonempty bytes, exact MIME/hash, actual Pillow image decode, WAV frame validation and bounded full MP4 decoding. Stream dimensions alone cannot qualify video.
- Explicit accepted license/evidence hash, required CC BY attribution and independent public/model/commercial rights. Accept writes one exact MaterialRevision and optional ProjectMaterialReference atomically; identical decision replay is idempotent during preview lifetime.
- Sorted source Revision/Material locks and fresh rights/bytes revalidation held through acceptance commit. No Master/identity/publishing mutation.
- Safe hash/provider-version lineage only; raw prompts, provider metadata/errors/signed URLs are not copied into MaterialRevision/AuditLog/events.
- New `/assets` lazy panel and legacy `/materials` generation entry use the same two-step flow; old automatic material generation is removed from that endpoint.

## Actual gates

- `.venv/bin/pytest -q`: **1250 passed, 2 skipped, 8 existing warnings, 51.10s** after review corrections.
- Dedicated `tests/test_f7_media_acceptance.py`: **20 passed**; includes real PNG/WAV/MP4 bytes, corrupt output, missing license/attribution, foreign actor, archive, runtime drift, expiry, unknown/redaction and two SQLite connections racing source revocation.
- `npm run build`: TypeScript/Vite and FE-P1 budget gate pass. `/projects` 224.80/72.92 kB raw/gzip; `/assets` 258.37/82.70; ProviderMediaPanel 4.77/2.65 lazy. No TipTap/XYFlow enters library initial graph.
- `openspec validate --all --strict`: **30/30**; scoped Ruff and `git diff --check` pass.
- Fresh isolated SQLite migrations to `f7a000000001` passed; this slice has no new migration. PostgreSQL up/down/up evidence is Batch A, not rerun or claimed here.
- Independent read-only review initially found four blockers (CLI identity, retries, MP4 decode, revocation race); re-review **APPROVE**, confined to safety closure/shared acceptance.

## Isolated browser

Guarded fixture `apps/api/tests/fe_f7_media_acceptance_server.py` and script `apps/web/scripts/fe-f7-media-browser-acceptance.mjs`. Fresh DB/media: `/tmp/aicontent-f7-media.UL5AFR/`. UI/API loopback ports 15671/18271. Actual four gates and zero page errors:

1. Decoded PNG preview appears, no material exists, rights acceptance initially disabled.
2. Explicit acceptance saves exact content hash and selected rights; no raw prompt persisted.
3. Reload reads the durable material but does not revive the temporary preview.
4. Legacy generation opens the same acceptance panel.

Report/screenshots: `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-media-browser-kl1CJE`.

**This is a synthetic Provider emitting real decoded bytes, not real external generation or verified Provider/account evidence.**

## Next

Continue bounded search/import, real single-attempt adapters, ASR acceptance, renderer scopes and account-bound immutable publisher/readback; finish F7 before F8. Keep unavailable capabilities honest. Canonical sync/archive and real account side effects still require separate authority.
