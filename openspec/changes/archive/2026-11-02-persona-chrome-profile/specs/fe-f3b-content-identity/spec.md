## ADDED Requirements

### Requirement: A persona can use its own Chrome profile

A persona SHALL optionally name one local Chrome profile, chosen from the profiles Chrome already has. No two personas SHALL share a profile. The choice SHALL be stored as a system setting, not in persona revisions or snapshots, and the studio SHALL read only profile names, never cookies, passwords or history.

#### Scenario: Choosing a profile
- **WHEN** the user picks Chrome profile 知数造物 for persona 量化研究专家 while no other persona uses it
- **THEN** it is saved and the persona overview shows 知数造物 as its browser

#### Scenario: Profile already taken
- **WHEN** the user picks a profile another persona already uses
- **THEN** the save is rejected with a message naming that persona

### Requirement: Account links open in the persona's Chrome profile

On the account page, 去发布, 去写作 and 账号主页 SHALL open in local Chrome under the owning persona's profile when one is set, and in a new tab of the current browser otherwise. The server SHALL only open the account's own creator links or homepage link.

#### Scenario: Opening with a profile
- **WHEN** the user clicks 去后台 on 知数Talk, whose persona uses Chrome profile 知数造物
- **THEN** Chrome opens https://mp.weixin.qq.com/ in the 知数造物 profile

#### Scenario: Arbitrary URL
- **WHEN** a request asks to open a URL that is not one of the account's links
- **THEN** it is rejected and nothing opens
