## ADDED Requirements

### Requirement: Marked shots of portrait-less persona works may show other people without faces

A 导演稿 shot board SHALL accept an optional other_people text (1–60 characters, not blank) naming people in the picture who are not the persona, such as 宝宝 or 医护人员的手; it SHALL be stored only when written so existing drafts keep their hashes, and an invalid value SHALL be refused with the reason. For a persona work without a portrait, every generated prompt of a marked shot (first-frame still, image-to-video and text-to-video in Chinese and English, single stills, storyboard sheets and cell redraws) SHALL say that the persona never appears, that the named people may appear only as hands, feet, part of the body or from behind with no face, front or side view, and that no other people appear; the "no person, no body" rule SHALL not appear for that shot. Unmarked shots keep the no-person rule unchanged, and persona works with a portrait and product works ignore the field. The page and person_notices SHALL state for a marked shot that the named people may appear without a face.

#### Scenario: Shot marked 宝宝
- **WHEN** a shot of work 94 is marked other_people 宝宝
- **THEN** its prompts allow the baby's hands, feet and body without a face, exclude the persona and anyone else, contain no "不出现身体", and the page says this shot may show 宝宝 without a face

#### Scenario: Unmarked shot
- **WHEN** a shot of the same work is not marked
- **THEN** its prompts are identical to before

#### Scenario: Invalid value
- **WHEN** a draft is saved with other_people longer than 60 characters, blank or not text
- **THEN** the save is refused with the reason

#### Scenario: Product work
- **WHEN** work 93's prompts are read
- **THEN** they are identical to before
