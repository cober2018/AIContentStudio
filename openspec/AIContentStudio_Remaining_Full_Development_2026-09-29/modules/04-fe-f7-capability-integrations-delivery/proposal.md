## Why

The North Star places Model/Tool/Data/Search/Image/Video/TTS/ASR/Renderer/Channel Adapter/Publisher behind a replaceable Capability layer. The repository already has useful pieces (Connector tables, PluginRegistry, Channel Registry, copy-package Publisher, WeChat WeWrite Publisher, provider settings) but they are not yet a durable, verified capability system.

F7 turns these pieces into real integration boundaries without moving Studio business truth into external runtimes.

## What Changes

- Extend Capability Registry kinds to the North Star capability categories.
- Persist safe capability metadata and verification status separately from secrets.
- Map configured Connector endpoints into executable Data Source capabilities only when an explicit mapping exists.
- Add replaceable material-search, image-generation, video-generation, TTS and ASR provider contracts.
- Save accepted external media into MaterialRevision with exact provider/source/prompt/hash/rights metadata.
- Add Renderer and ChannelAdapter registration/verification metadata.
- Add account-specific Publisher capability verification:
  Platform × Account × ContentForm × Action × VerificationTime.
- Keep all unverified capabilities unavailable.
- Add capability inventory and verification status to Settings.
- Preserve copy/manual delivery as universal safe fallback where the content form is packageable.
- Support existing WeChat WeWrite only according to its real verified behavior.
- Do not claim Douyin/Xiaohongshu remote API publishing unless an actually verified provider is implemented and tested.

## Migration

Likely additive persistence:
- `capability_registration`
- `capability_verification`

Secrets are not stored in these records.
Existing code/static registry descriptors remain valid sources; persistence records runtime verification/config identity.

## Non-goals

- Importing an external agent framework as the Studio business core.
- Storing provider secrets in capability metadata.
- Marking capability active because a plugin class exists.
- Auto-publishing without Delivery Authorization.
