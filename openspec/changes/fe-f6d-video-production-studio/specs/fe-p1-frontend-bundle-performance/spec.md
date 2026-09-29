## ADDED Requirements

### Requirement: Professional Video editor is isolated to the Video lazy route
The Video Studio and any timeline/player/editor-only runtime SHALL load behind the Video-specific lazy boundary. Common Production, Text, Graphic and other primary-route initial static graphs MUST NOT import it. The existing FE-P1 budgets and TipTap/XYFlow isolation SHALL continue to be checked automatically.

#### Scenario: Open a non-Video Production unit
- **WHEN** a user loads common Production, Text or Graphic without opening Video Studio
- **THEN** the Video-only editor/runtime is absent from that route's initial static dependency closure

#### Scenario: Build detects a Video import leak
- **WHEN** a shared Production module statically imports a Video-only editor dependency
- **THEN** the bundle gate fails rather than accepting the initial-size regression
