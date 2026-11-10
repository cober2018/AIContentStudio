## MODIFIED Requirements

### Requirement: The user reviews materials instead of the 导演稿
A saved 导演稿 SHALL count as adopted without a user decision. Each work SHALL have a materials switch, manual by default, which the user can change until the 成片 is final. With the switch on manual, before the first 小样 of a work the chain SHALL stop once at 素材待你看: the model maps every shot's material, prepares first frames and prompts for shots to be generated, and submits the materials for review. The user SHALL be able to replace materials, switch shots to manual and upload clips, approve, or send notes. On approval, manual shots without a clip SHALL be switched back to auto so the model makes them. With the switch on auto, the chain SHALL NOT stop at materials, every shot without a user material SHALL count as auto, and submitting materials SHALL be refused. Only after approval, or with the switch on auto, SHALL auto clips be generated and the 小样 task be opened. Later revisions after 小样 notes SHALL NOT stop at materials again. The user SHALL still be able to send the 导演稿 back with notes until the 成片 is final.

#### Scenario: Fully automatic materials
- **WHEN** the switch is auto and the model has mapped the materials
- **THEN** it generates the auto clips, voices and cuts the 小样 without waiting for the user

#### Scenario: Switch to auto while materials wait
- **WHEN** the materials wait at 素材待你看 and the user switches to auto
- **THEN** the chain goes on as if the materials were approved

#### Scenario: One shot made by hand
- **WHEN** the switch is manual, the user switches shot 3 to manual, makes the clip on a website from the given prompt and uploads it, then approves
- **THEN** shot 3 uses the uploaded clip and the model makes the other shots

#### Scenario: Manual shot not uploaded
- **WHEN** the switch is manual and the user approves while shot 5 is manual without a clip
- **THEN** approval goes through and shot 5 is switched back to auto for the model to make

#### Scenario: Revision after 小样 notes
- **WHEN** the model saves a new 导演稿 after 小样 notes
- **THEN** it goes on to the next 小样 without stopping at materials
