## ADDED Requirements

### Requirement: An approved 成片 goes to review by itself

When the user approves a work's 成片 in the video chain, the platform SHALL set the work's status to finalized (已成稿) and create a review candidate of kind finished video (manifest schema_version 6) holding the accepted 成片, the work's cover(s), the publish copy when there is one, and the director document's revision and hash. The candidate SHALL check only these files (public use allowed, bytes and hash intact), not the shot source materials, and SHALL record the work's channel or, when none is chosen, that it is still to be chosen. A later approval of a new 成片 SHALL create a new candidate and keep the old one in history.

#### Scenario: Work 95 approved
- **WHEN** the user approves the 成片 of work 95, which has no channel
- **THEN** the work list shows 已成稿 and the review center shows a candidate with the 成片, both covers and channel 待选

### Requirement: Finished-video candidates go through review, delivery and learning

For a finished-video candidate the review center SHALL preview the 成片, covers and publish copy; approval SHALL check only that its files are still valid and that it is the work's latest candidate; delivery authorization SHALL take the channel chosen there (fixing it on the candidate when it was still to be chosen) with content form short video; the delivery package SHALL contain the 成片, the covers, the publish copy and the manifest, and no shot source materials. A human-confirmed receipt SHALL set the work's status to published (已发布) and SHALL be picked up by the 效果复盘 sync as for other candidates. Existing candidates of other kinds SHALL keep their current checks.

#### Scenario: End to end
- **WHEN** the user approves the candidate, authorizes it for a channel and account, downloads the package and confirms the receipt
- **THEN** the package holds the 成片 and covers, the work shows 已发布, and the 效果复盘 sync records the publication

### Requirement: Work lists show where a work stands

The persona content workbench and the product video workbench SHALL show a work's status in Chinese, including 已成稿 and 已发布, keeping finished works in the list after the ones still in progress.

#### Scenario: Finished work stays listed
- **WHEN** a work is finalized
- **THEN** it stays in the list, labelled 已成稿, after works still being made
