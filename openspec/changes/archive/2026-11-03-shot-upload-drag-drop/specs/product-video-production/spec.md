## ADDED Requirements

### Requirement: Shot videos can be dropped onto the upload area

The upload entry of a shot in the supplement panel and in the storyboard-grid dialog SHALL accept a video dragged from the computer as well as a click to choose a file. Dropping one MP4 / MOV SHALL upload it onto that shot through the existing upload. The area SHALL highlight while a file is dragged over it. Dropping a non-video SHALL show a message and upload nothing; dropping several files SHALL upload only the first and say that a shot takes one video.

#### Scenario: Drop a video
- **WHEN** the user drags an MP4 onto shot 6's upload area and lets go
- **THEN** the video is uploaded onto shot 6, as with a click upload

#### Scenario: Drop a picture
- **WHEN** the user drops a PNG onto the upload area
- **THEN** the page says to drop an MP4 / MOV video and nothing is uploaded
