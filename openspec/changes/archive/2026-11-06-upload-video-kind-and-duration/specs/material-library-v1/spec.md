## ADDED Requirements

### Requirement: Uploaded videos are recorded as videos with their length

The upload dialog SHALL set the material type from the chosen file's format (video, audio or image), still editable by the user. When a video is uploaded, the platform SHALL read its duration, width and height and record them on the revision; when they cannot be read the upload SHALL still succeed with them left empty, except for raw footage uploads, which keep requiring a readable duration.

#### Scenario: Uploading an MP4
- **WHEN** the user picks a 4.2-second 1080×1080 MP4 in the upload dialog and uploads it without touching 类型
- **THEN** the material is a video and its revision records 4200 ms, 1080 wide and 1080 high

#### Scenario: Length cannot be read
- **WHEN** a normal video upload cannot be probed
- **THEN** the upload succeeds and the duration stays empty
