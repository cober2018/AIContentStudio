# Findings

## 2026-10-23
- Material search already marks rows to be made in post (`footage: motion`, suggestion 用 AE 动效或图解制作), scores candidates by looking at them, and flags `eligible_main` (seen, score ≥ 0.6, no conflicts).
- All licences the open search admits allow commercial use with attribution, so automatic acceptance can take its rights from the licence.
- map-route needs a real map image, so it is left out of automatic use for now.
- U80 on the live DB already has an accepted 7-shot master (revision 132, from attempt 332 generated at 11:10 before the shot-plan fix took effect). Its slots now follow that master. To get the 15-row table, the 导演稿 must be generated again and accepted.
- Accepting stock during auto-fill writes downloaded bytes to the shared content-addressed material storage even on a DB copy.
