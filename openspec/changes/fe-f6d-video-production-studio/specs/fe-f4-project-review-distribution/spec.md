## ADDED Requirements

### Requirement: Project Review presents frozen Video v2 structure and final bytes
For a Video v2 Candidate, project Review SHALL derive script, shots, timeline, voice, subtitles, overlays, cover, current checks and final-render provenance from the frozen Candidate v4 manifest. It SHALL compare revisions structurally and SHALL NOT invent whole-video text similarity. Approval and Delivery Authorization SHALL retain their exact Candidate hash, live-rights and current-Master gates.

#### Scenario: Review a changed Video cut
- **WHEN** a reviewer compares two Video v2 Candidates with different shot order and subtitle text
- **THEN** Review shows those exact structured changes and the approved final-video identity without treating the preview as a new source of truth

### Requirement: Video v2 local handoff is byte-exact
The local copy/manual package for a Video v2 Candidate SHALL contain the exact approved final video bytes and hash plus only declared companion media and manifest content. It MUST NOT fall back to Draft/video v1 packaging or perform remote publication.

#### Scenario: Live media revocation before download
- **WHEN** the approved final-video MaterialRevision is revoked or its bytes/hash no longer match
- **THEN** package download is blocked and no older package is silently substituted
