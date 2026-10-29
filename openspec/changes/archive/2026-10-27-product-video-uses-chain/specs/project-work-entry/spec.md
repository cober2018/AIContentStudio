## ADDED Requirements

### Requirement: Product videos use the third-party video chain page

A product video's production page SHALL show 商品与本条目标, 导演稿, 素材, 配音与音乐, 小样, 成片 and 交付, with the user reviewing the 导演稿, 小样 and 成片 on the page as for persona videos. The 导演稿 step SHALL show the platform writing skill switch. The old product steps SHALL no longer be shown.

#### Scenario: Review a product director's draft
- **WHEN** a third-party model saves a director's draft for project 42's 「儿童麸质饼干」 video
- **THEN** the 导演稿 step of that work shows the draft with 采用 and modification notes, and the platform writing skill switch

#### Scenario: Old link
- **WHEN** the user opens that work with an old step link such as workstep=edit
- **THEN** the page lands on the chain's current step
