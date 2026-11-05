# media-tools Specification

## Purpose
TBD - created by archiving change media-transcription-tool. Update Purpose after archive.
## Requirements
### Requirement: Media transcription through MCP

The creative MCP SHALL offer `start_media_transcription` (a local audio or video file path, optional output folder) and `get_media_transcription` (a job id), without a project. A job SHALL run in the background, one at a time, with the platform's local transcription (MLX Whisper, else the local whisper CLI), splitting media longer than 10 minutes into pieces whose times are joined. It SHALL never call a network or paid model.

#### Scenario: Start and read
- **WHEN** the model starts a transcription of a 25-minute mp4 and later reads it
- **THEN** it first gets a job id with status running, and when done gets the output folder, the files, the duration and the opening text, with subtitle times covering the whole 25 minutes

#### Scenario: Not a media file
- **WHEN** the path is missing or has no audio stream
- **THEN** the start is refused with a reason and no job is queued

### Requirement: Text, subtitles and illustrated notes

Each finished job SHALL write one folder holding `<name>.txt`, `<name>.srt` and `<name>.md`. For video, the md SHALL be split at scene changes with one screenshot per part, at least 1 second apart and at most 200, kept in `images/` and referenced by relative path; for audio the md SHALL have no images. The default folder SHALL be `自媒体素材/AIContentStudio/转写/<name>/` on the material drive; an existing folder SHALL never be overwritten. With the default folder and the drive missing, the start SHALL be refused with `material_library_unavailable` and 「素材库盘没连接」.

#### Scenario: Video notes
- **WHEN** a video with 12 scene changes is transcribed
- **THEN** the md has 13 parts, each with its screenshot from images/ followed by the speech in that part

#### Scenario: Same file twice
- **WHEN** the same file is transcribed again
- **THEN** a new numbered folder is written and the first one is untouched

### Requirement: Tools page

The navigation SHALL have a 「工具」 group with 「小工具」. The page SHALL list the small tools (now 媒体转文字, what it does, how to ask the third-party model and its MCP tool names) and the latest transcription jobs with source file, status or failure reason, duration, output folder and files, each able to reveal its folder in Finder. The page SHALL NOT start transcriptions.

#### Scenario: Watch a job
- **WHEN** the model has started a transcription and the user opens 小工具
- **THEN** the job shows as running, then done with its files, and 「在访达中显示」 opens its folder

