## ADDED Requirements

### Requirement: Frame checks and covers use accurate colour conversion

craft-resolve SHALL extract the cover with an ffmpeg command using accurate conversion (accurate_rnd+full_chroma_int), so the cover matches the video as Chrome plays it within 1 level, and every instruction that converts video frames to RGB or gray for comparison SHALL use the same flags; color.md SHALL state that ffmpeg's default fast conversion reads bt709-tagged files about 2 levels dark across the whole range.

#### Scenario: Cover from a bt709 final
- **WHEN** the cover is extracted from a bt709-tagged final with the documented command
- **THEN** it differs from the frame Chrome shows by at most 1 level
