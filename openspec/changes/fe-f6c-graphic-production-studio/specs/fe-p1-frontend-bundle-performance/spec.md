## ADDED Requirements

### Requirement: Professional Graphic editor loads only for Graphic production
The Graphic Studio and any canvas/editor dependency SHALL load behind its Graphic-only route/component boundary. Common Production, Text, Video and other primary workspaces MUST NOT statically import it; the existing FE-P1 initial-JS budgets SHALL remain automatically checked.

#### Scenario: Open common Production or Video
- **WHEN** a user opens common Production or a Video Unit without opening Graphic Studio
- **THEN** the initial module graph contains no Graphic-only editor dependency
