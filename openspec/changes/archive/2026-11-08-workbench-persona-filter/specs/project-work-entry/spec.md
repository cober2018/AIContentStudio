## ADDED Requirements

### Requirement: The persona workbench filters works by persona
角色内容工作台 SHALL offer a 角色 filter listing 全部 and every persona by name; choosing a persona SHALL list only the works of that persona, together with the other filters. The choice SHALL be kept in the page address. 商品视频工作台 SHALL NOT show this filter.

#### Scenario: Choosing a persona
- **WHEN** the user picks a persona in the 角色 filter
- **THEN** only works whose persona is that persona are listed, and the pick survives a refresh
