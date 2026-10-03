# F7 Provider Adapter Contracts

## Purpose

This document records capability-adapter boundaries. The user-selected Gemini
and `grok-4.7` profiles use a third-party CPA OpenAI-compatible gateway, not
Google/xAI official APIs. The dormant official-native descriptors below are
historical implementation inventory, not a current F7 requirement or evidence
that the CPA gateway offers those operations.

Native descriptors are opt-in at process bootstrap through
`AICS_ENABLE_NATIVE_MODEL_ADAPTERS=1`. The default is disabled so an
unverified provider cannot change legacy capability state merely by being
installed in the source tree.

The local MiniMax CLI adapter is separately opt-in through
`AICS_ENABLE_MINIMAX_CLI=1`. It uses the installed `mmx` executable and its
own local authentication/configuration. With explicit local authorization,
the application reads only the official fixed configuration path through an
OS-user-directory, no-follow file-descriptor boundary to derive an opaque HMAC
credential epoch. It never exposes or persists raw credentials, accepts an
arbitrary executable/path, constructs a shell command, or persists CLI
stderr/stdout as provider history.

## Current adapter matrix

Current model-routing implementation is23/23 with scoped provider/safety and
consumer/UI independent review APPROVE. Final local gates are recorded in
[final acceptance](FE_F7_FINAL_LOCAL_GATES.md); no additional real supplier
call or credential/configuration mutation occurred during this closure.

2026-10-03 authoritative scope: CPA chat and MiniMax image/TTS/ASR contracts
have actual bounded operation evidence in [model validation](FE_F7_MODEL_VALIDATION.md).
Formal TTS acceptance produced MaterialRevision6 and Unit3 Master9; local MLX
ASR produced43 explicitly accepted cues in Video Master5. MiniMax real video/H3
download is excluded by the user, not PASS. No Google/xAI official-native
adapter is required. Earlier protocol reads below are historical references,
not an instruction to repeat external calls or reopen excluded operations.

| Adapter | Operation | Model IDs | Protocol boundary | Status |
|---|---|---|---|---|
| `google.native@1` | image | `gemini-3.1-flash-image`, `gemini-3-pro-image`, `gemini-2.5-flash-image` | Interactions REST `steps/model_output/content`; SDK convenience fields are not REST fields | descriptor only; no response decoder/dispatch; not verified |
| `xai.native@1` | image | `grok-imagine-image`, `grok-imagine-image-2.0` | `/v1/images/generations`, bytes/URL response must be validated | not verified |
| xAI video (planned, not registered) | video | public examples: `grok-imagine-video`, `grok-imagine-video-1.5` | `/v1/videos/generations`, request ID polling | current XAI_NATIVE contains image operation only; unavailable |
| `minimax.native@1` | all | none enabled | partial official contracts below; no native dispatcher | unavailable |
| CPA configurable OpenAI-compatible | chat | `gemini-3.8-flash-high`, `claude-opus-4-6-thinking`, `grok-4.7` | configured base `/v1` + `/models` discovery and `/chat/completions`, Bearer auth; JSON messages/exact model, choices message text, deterministic structured parser | all three real product chat tests200; discovery30 IDs and seven consumer routes verified; no media inferred |
| `minimax.cli@1` | image | `image-01` actual CLI dry-run identity; `image-01-live` only if exact runtime proves it | fixed `image generate`, one base64 image, controlled temp file and existing durable task | actual image JPEG33997 bytes result_ready; not accepted into formal library, no public/commercial grant |
| `minimax.cli@1` | TTS | actual `speech-2.8-hd`; other exact allowlisted suffix IDs remain account-unverified | fixed `speech synthesize --model … --format wav`, real decoded bounded WAV | real supplier and formal task→explicitaccept→MaterialRevision6→Master9 verified; rights false |
| `minimax.cli@1` | ASR | `asr-1.0` | fixed `speech transcribe`, real SRT timestamp/cues; exact WAV or validated MP4 first-audio input | real WAV and video-audio transcription verified; explicit ASR/save contract separate, no visual understanding |
| `minimax.cli@1` | video | implemented fixed H3/V2 or Hailuo/V1 model/protocol, not brand inference | bounded original-job query/download retained | real generation/H3 download excluded_by_user_scope; generic mechanism offline-verified only |
| `minimax.cli@1` | text | none enabled | help advertises chat, but no text dispatcher exists | unavailable |

The previously recorded CPA401 is historical. Credentials remain in existing
protected configuration and never in this document. CPA chat does not prove
CPA image/video/TTS/ASR: missing exact media protocol stays unavailable, with
only an authorized configured plugin selected before sending. Text output or
a model name never substitutes for media bytes.

### Current per-operation limits and acceptance contract

| Operation | Input / call boundary | Output / recovery boundary | Rights / provenance |
|---|---|---|---|
| CPA chat | exact configured provider/model, registered endpoint guard, Bearer credential kept in runtime, bounded messages/tokens/timeout | JSON response parsed through existing chat provider; no invented media decoder/job | safe route projection; actual chat success does not set media verified |
| MiniMax image | fixed argv, no source-image edit, one image; actual model must match dry-run; side512–2048, 8-aligned, square within frozen pixel limit | base64→controlled file; stdout+stderr≤512KiB, content≤30MiB; real MIME/decode/hash, no URL-only result | generated provenance; user explicit license/hash/rights decision before MaterialRevision; unproved rights remain false |
| MiniMax TTS | exact full model ID; text<10000 characters; fixed WAV argv, one output, caller seconds and≤25s CLI request deadline | bounded local file, real WAV frame/duration≤frozen seconds, result hash/HMAC; timeout/nonzero/empty uncertain output→Unknown/no resubmit | formal accepted audio still public/model/commercial=false; no license grant inferred from successful API |
| MiniMax ASR | exact asr-1.0; validated WAV or fixed file-only MP4 first-audio→16k mono PCM; actual duration≤500s and caller limit,≤30MiB | fixed SRT/sentence timestamps, bounded cues/text/time range, shared deadline/4KiB media diagnostics; invalid output rejected, no fabricated times | source MaterialRevision/hash/model-use checked live; safe transcript receipt, explicit local accept and Master CAS, no Fact Boundary/Identity mutation |
| Generic video mechanism (not real account acceptance) | exact original model/protocol/job, bounded query interval/count; no replacement send | HTTPS443/public DNS pinned/TLS, same-origin≤4 hops, no env proxy/auth headers,≤30MiB, isolated process absolute deadline; V1 unsafe download unavailable | known-job unavailability remains Unknown; original identity retained; no real video or license PASS |

All durable operations pin owner/request/configuration/runtime/model/protocol,
original receipt-key ID and irreversible credential epoch. Inventory does not
read credentials or call suppliers. Explicit execution uses the fixed official
CLI authentication file only in memory; queries/acceptance validate original
runtime and retained key. Raw credential/error/signed URL never enters DB/UI.
Provider calls use the existing two-slot one-shot pool; timeout retains the slot
until the running call ends and never triggers provider switching. Exact bytes
are private until explicit atomic MaterialRevision/project-reference acceptance.

## Safety rules

- `binding_state` never performs a network request.
- Credential values are read only through the configured environment reference;
  runtime identity stores a one-way digest, never the secret.
- Unsupported model/operation pairs remain unavailable.
- Native adapters only describe/build bounded requests in this slice. Actual
  provider dispatch must continue through `provider_calls` and `provider_media`,
  then pass byte/MIME/decode/hash/rights and explicit acceptance gates.
- A provider URL or asynchronous job ID is not a generated asset. The original
  job remains the only pollable job, and an uncertain result remains Unknown.
- MiniMax CLI image/audio outputs are read from bounded temporary files and
  video uses only the original command/task/file result. All outputs still pass
  the existing preview → explicit acceptance → MaterialRevision path; generated
  media is never evidence or an authentic screenshot/news photo.

## MiniMax protocol verification — 2026-10-01

Public documentation reads only: no account authentication probe, generation,
quota consumption or credential-file read. Installed CLI help is `mmx 1.0.27`.
This section records the earlier public-document review, not current task status.
Google/xAI official-native coverage is outside current scope. MiniMax public or
commercial license remains unproven; local restricted acceptance never upgrades
those rights. Native descriptors remain unavailable; current execution uses the
fixed CLI implementation above.

| Operation | Verified public contract | Application boundary / missing evidence |
|---|---|---|
| Image | Bearer JSON POST `/v1/image_generation`; `image-01` example; URL response `data.image_urls` with `base_resp.status_code=0` | Existing CLI path requests one image. Base64 response field not independently confirmed here; do not invent one. CLI dry-run is model evidence, not real output verification. |
| TTS | Bearer JSON POST `/v1/t2a_v2`; nonstream `data.audio` hex, successful status example `2`, nullable data; optional URL expires after 24 hours | Official complete IDs: `speech-2.8-hd/turbo`, `speech-2.6-hd/turbo`, `speech-02-hd/turbo`, `speech-01-hd/turbo` (each suffix is a distinct full ID). Text must be fewer than 10000 characters. Family shorthand is rejected; CLI emits bounded WAV. |
| ASR | Bearer multipart POST `/v1/speech_to_text`, `asr-1.0`; audio at most 500 seconds and 50 MB; `srt` includes timestamps, incompatible with streaming | Current CLI accepts validated WAV only, with the stricter application 30 MiB limit. Both declared duration and actual WAV frames must stay within 500 seconds and the request limit; never infer cue timing from plain text. |
| Legacy video query | Bearer GET `/v1/query/video_generation?task_id=…`; exact original task; `Preparing/Queueing/Processing/Success/Fail`; Success yields `file_id` | This is the legacy endpoint, not proof that H3 uses the same protocol. Current CLI timeout still lacks complete original-job recovery; no replacement submission. |
| Legacy video file | Bearer GET `/v1/files/retrieve?file_id=…`; response `file.download_url` | File metadata/URL is not validated video bytes. Bind returned file ID to the original task, validate download and bytes before acceptance. No URL lifetime inferred from image/TTS docs. |

The earlier CN-document fetch failed. A subsequent read of the official global
H3 create/query pages succeeded; see the protocol separation below. Legacy video
creation and complete pricing/license verification are still incomplete. Do not
implement H3 by copying the legacy endpoint. The CLI descriptor remains partial,
not a substitute for native dispatch or durable original-task recovery.

API support is not a license or quota grant. Account entitlement, generated-media
commercial/public rights and any third-party reference rights still need explicit
evidence before accepting a MaterialRevision; neither CLI help nor successful
generation establishes these rights. Supplier pricing and aggregate monetary
budgets remain separate from local structural limits.

MiniMax protocol sources:

- [Image creation](https://platform.minimax.cn/docs/api-reference/image-generation-t2i)
- [Synchronous TTS](https://platform.minimax.cn/docs/api-reference/speech-t2a-http)
- [Speech recognition](https://platform.minimax.cn/docs/api-reference/speech-to-text)
- [Legacy video task query](https://platform.minimax.cn/docs/api-reference/video-generation-query)
- [Legacy video file retrieval](https://platform.minimax.cn/docs/api-reference/video-generation-download)

## Native protocol separation — 2026-10-01 follow-up

These are public request/output contracts, not live account verification. No
operations are enabled by this documentation update. Reading a current supplier
page does not prove that the installed CLI or a CPA gateway implements it.

| Protocol | Submission and output shape | Required implementation distinction |
|---|---|---|
| MiniMax H3/V2 | Bearer JSON POST `https://api.minimax.io/v2/video_generation`: model, typed `content`, resolution, integer duration; returns `task_id`. GET `/v2/query/video_generation/{task_id}` returns `task.id/model/status`, successful `task.content.url`; query window is last 7 days. | Success does not return the legacy `file_id` contract. Bind original ID/model, fetch validated URL bytes, never invent a file ID or use V1 query. Account-region endpoint is not inferred from global docs. |
| Google Interactions image | POST `/v1beta/interactions`, `x-goog-api-key`, model/input and image `response_format`; REST image is typed `steps[].content[]` under `model_output`, base64 `data` plus `mime_type`. | `output_image` is SDK convenience, not required REST JSON. Old `outputs` is a different response schema; do not permissively merge schemas. Current adapter has no Google response decoder. |
| Google Omni video | Official example model `gemini-omni-1.1-flash`, Interactions endpoint; completed REST response has typed video content in `steps`, MP4 MIME and base64 bytes. | `output_video` is SDK-only. A CPA chat model called Gemini does not thereby obtain this endpoint/model/account capability. Not registered in current adapter. |
| Google Veo | Official REST example POST `/v1beta/models/veo-3.1-generate-preview:predictLongRunning`, `instances` input, `x-goog-api-key`; returns operation `name`, GET same operation until `done`; `response.generateVideoResponse.generatedSamples[].video.uri` is downloadable output. | A different protocol from Interactions video. Validate returned operation path and download destination; never forward API keys to arbitrary redirect hosts or copy the documentation's unbounded poll loop. Not registered. |
| xAI image | Bearer JSON POST `/v1/images/generations`; `grok-imagine-image-2.0` official example; URL default, or `response_format=b64_json` with `data[].b64_json`; `n` supports 1–10. | Application restricts one bounded decoded image. Moderation and actual model metadata must be handled explicitly, not silently ignored. CLI/gateway and native bindings stay distinct. |
| xAI video | Bearer POST `/v1/videos/generations` returns `request_id`; GET `/v1/videos/{request_id}` yields `pending/done/expired/failed`, successful `video.url`, duration, `respect_moderation`, model. | Persist/poll original request only; expired is not permission to submit anew. Temporary URL is not bytes, and current image request builder must never be reused with `n/b64_json` fields for video. |

H3 constraints: `MiniMax-H3` has 4–15-second output at `768P/2K`;
`MiniMax-H3-Max` has 5–15 seconds at `480P/768P`, not 2K. Pure text needs a
concrete ratio, not `adaptive`. First/last-frame and reference modes are mutually
exclusive. Body maximum is 64 MB; reference image/video/audio caps differ.
Create documentation requires Pay-as-you-go API; do not infer authorization
from a CLI TokenPlan display. The installed adapter does not support H3-Max or
reference modes merely because public docs list them.

```text
MiniMax V1: task_id → status Success → file_id → retrieve URL → validated bytes
MiniMax V2: task_id → task.status succeeded → task.content.url → validated bytes
xAI video: request_id → status done → video.url → validated bytes
Google Veo: operation name → done → generatedSamples video.uri → validated bytes
Google Interactions: completed → model_output typed content → decoded bytes
All: exact runtime/input/owner → preview → explicit acceptance → MaterialRevision
```

Source contracts:

- [MiniMax H3 create](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)
- [MiniMax H3 query](https://platform.minimax.io/docs/api-reference/video-generation-v2-query)
- [Google Interactions migration](https://ai.google.dev/gemini-api/docs/interactions-breaking-changes-may-2026)
- [Google image generation](https://ai.google.dev/gemini-api/docs/image-generation)
- [Google Omni REST response](https://ai.google.dev/gemini-api/docs/omni)
- [Google Veo generation](https://ai.google.dev/gemini-api/docs/veo)
- [xAI image generation](https://docs.x.ai/developers/model-capabilities/images/generation)
- [xAI video generation](https://docs.x.ai/developers/model-capabilities/video/generation)

Task2.1 is evaluated against the current table and recorded actual CPA/image/
speech evidence, not this historical missing-evidence list. Real video/H3 is
user-excluded; generic original-job recovery, retained-key continuity and browser
proofs are separately documented in FINAL_LOCAL_GATES and MODEL_VALIDATION.
Unknown license stays unknown/rights=false, not an invented entitlement.

## Other provider sources

- [Google Gemini image generation](https://ai.google.dev/gemini-api/docs/image-generation?hl=en)
- [Google Gemini video generation](https://ai.google.dev/gemini-api/docs/video)
- [xAI image API](https://docs.x.ai/developers/rest-api-reference/inference/images)
- [xAI video API](https://docs.x.ai/developers/rest-api-reference/inference/videos)
- [MiniMax Video-01 API announcement](https://www.minimax.io/news/video-generation-api)
- Local MiniMax CLI capability evidence: `mmx --help` / version `1.0.27` on the
  configured development machine (help proves command shape only, not account
  access, quota or generation success).
