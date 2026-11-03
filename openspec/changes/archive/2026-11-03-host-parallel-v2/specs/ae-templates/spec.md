## ADDED Requirements

### Requirement: Parallel picture reveal v2 for four pictures and long narration

The template library SHALL offer `host-parallel` v2 beside an unchanged v1, with image slots img1–img4 (img1 and img2 required), label fields item1–item4 of at most 8 characters, a duration of 4–60 seconds defaulting to 7, and a `beats` field long enough for four "open-close" pairs with times up to 60 seconds. Beats SHALL work as in v1: an image opens at its open second and closes at its close second, closes 0.7 s before the next opens when no close is given, and opens every 2.2 s when beats are empty. The thumbnails SHALL sit in one row above the speaker from their entrance to the end of the clip, laid out for 2, 3 or 4 supplied images without empty slots, with all thumbnails and labels inside the playback safe area. Opening, closing, border and label styling SHALL match v1. Both 9:16 and 16:9 projects SHALL exist with the same fields and a separate landscape layout. The v2 manifest SHALL have no checks, and so stay draft, until the user approves the comparison renders.

#### Scenario: Four points over 41 seconds
- **WHEN** v2 renders four pictures over 41 seconds with four beats pairs
- **THEN** four thumbnails stay in a row at the top, each opens and closes on its own beats pair in order, and nothing leaves the safe area

#### Scenario: Three pictures without beats
- **WHEN** v2 renders three pictures over 7 seconds with empty beats
- **THEN** it lays out three thumbnails like v1 and opens one every 2.2 seconds

#### Scenario: Draft until approved
- **WHEN** v2 is installed but the user has not approved the comparison renders
- **THEN** the library lists v2 as draft and v1 stays as it was
