## ADDED Requirements

### Requirement: The user reviews materials instead of the 导演稿
A saved 导演稿 SHALL count as adopted without a user decision. Before the first 小样 of a work the chain SHALL stop once at 素材待你看: the model maps every shot's material, prepares first frames and prompts for shots to be generated, and submits the materials for review. The user SHALL be able to replace materials, switch shots to manual and upload clips, approve, or send notes. Approval SHALL be refused while a manual shot has no clip. Only after approval SHALL auto clips be generated and the 小样 task be opened. Later revisions after 小样 notes SHALL NOT stop at materials again. The user stops SHALL be 素材, 小样 and 成片, and the user SHALL still be able to send the 导演稿 back with notes until the 成片 is final.

#### Scenario: Fully automatic materials
- **WHEN** the model submits materials and the user approves without changes
- **THEN** the model generates the auto clips, voices and cuts the 小样

#### Scenario: One shot made by hand
- **WHEN** the user switches shot 3 to manual, makes the clip on a website from the given prompt and uploads it, then approves
- **THEN** shot 3 uses the uploaded clip and only the other auto shots are generated

#### Scenario: Manual shot not uploaded
- **WHEN** a shot is manual and has no clip
- **THEN** 确认素材 is refused naming that shot

#### Scenario: Revision after 小样 notes
- **WHEN** the model saves a new 导演稿 after 小样 notes
- **THEN** it goes on to the next 小样 without stopping at materials
