## Why

AIContentStudio now has a full decision-to-learning lifecycle, but two first-class product areas still expose legacy structure instead of the current architecture:

1. `/assets` is still a placeholder while users must navigate separate legacy Source, Material and FactPack pages to understand reusable content assets and knowledge.
2. `/settings` contains many real capabilities, but its information architecture is still infrastructure-oriented and does not present Data Source Plugins, Channels, Rules and Team in the product concepts used by the rest of Studio.

F5C productizes these areas without creating parallel truth stores. Existing `SourceDocument`, `Material/MaterialRevision`, `FactPack/FactPackItem`, Connector, Data Source Plugin descriptors, Channel Registry, Rule Registry and system settings remain authoritative.

## What Changes

- Replace `/assets` placeholder with a real **System Assets & Knowledge** workspace.
- Add a unified system-library read model over existing Materials, Sources, FactPacks and Knowledge Collections; do not create a generic replacement Asset table.
- Add `KnowledgeCollection` and `KnowledgeCollectionItem` as organizational references to existing SourceDocument and FactPack resources. Collections do not duplicate source text, FactPack items or media bytes.
- Expose bounded provenance, rights/readiness and usage summaries for Materials, Sources and FactPacks.
- Preserve project reuse-by-reference semantics: MaterialRevision → ProjectMaterialReference, SourceDocument → ProjectSourceBinding, frozen FactPack → explicit Project Fact Boundary.
- Keep Source rights semantics truthful: SourceDocument itself is not a publication-right decision; public/model-use authorization comes from MaterialRevision and FactPackItem evidence rights.
- Productize `/settings` into Models, Data Sources, Channels, Rules & Templates, Team, and Advanced Runtime/Security sections.
- Reuse existing settings/connector/channel/registry/user APIs and persistence. Data Source Plugin descriptors and Channel/Rule registries remain their own sources of truth.
- Show disconnected/unavailable capabilities with their real reason instead of fake “connected” state.
- Keep current V1 system/shared library semantics explicit; F5C does not retrofit organization/multi-tenant ownership into legacy Source/Material/FactPack rows.
- Preserve FE-P1 route-level lazy loading and bundle budgets.

## Capabilities

### New Capabilities

- `system-assets-knowledge`: Unified system library projection, resource provenance/rights/usage, and reusable Knowledge Collections.
- `product-settings`: Product-oriented Settings information architecture over existing model, data-source, channel, rule, team and advanced runtime configuration truth.

### Modified Capabilities

- `fe-f0-f1-project-experience`: `/assets` becomes a real persistent workspace; `/settings` remains a primary workspace but gains the productized section contract.
- `fe-f2-persistent-production-workflow`: Data Source Plugin management/status is exposed in Settings while the typed plugin registry remains authoritative.
- `fe-f3a-content-project-core`: system library resources are reused by project reference rather than copied; Fact Boundary remains an explicit evidence action.

## Impact

Backend:
- additive KnowledgeCollection persistence;
- unified library/usage read services;
- product Settings read projections;
- no replacement of Source/Material/FactPack/Registry/SystemSetting truth.

Frontend:
- real lazy `/assets`;
- restructured `/settings`;
- legacy `/sources`, `/materials`, `/fact-packs`, `/connectors`, `/templates` remain compatibility/admin routes until separately retired.

No new external connector/provider, no organization auth redesign, no production migration/deploy, and no automatic rights inference is included.
