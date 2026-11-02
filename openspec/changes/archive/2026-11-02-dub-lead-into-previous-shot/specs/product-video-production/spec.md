## ADDED Requirements

### Requirement: A dubbed line may start in the previous shot's silent tail

For a shot marked with `dub_persona`, the silent tail of the previous shot — from the end of the last subtitle cue inside the previous shot to the start of this shot — SHALL be usable. A line that fits its shot at the persona's normal speed SHALL start at the shot; one that does not but fits tail plus shot SHALL start early, as late as possible, ending 0.1 s before the shot ends and never before that last cue ends; only if it still does not fit SHALL it be sped up (at most 1.25× over tail plus shot), otherwise refused. The lead in milliseconds and the actual start SHALL be recorded with the voiceover, subtitles SHALL follow, and no shot duration SHALL change. There is no tail when the previous shot is itself dubbed or the shot is first.

#### Scenario: Work 92 mother line
- **WHEN** shot-9 of work 92 is dubbed by 懒羊羊小王, the previous shot's last cue ends at 27.867 s and shot-9 runs 28.467–32.267 s
- **THEN** the line keeps speed 1.1, starts around 27.9 s, ends before 32.27 s and does not overlap 「哇，我超爱的」
