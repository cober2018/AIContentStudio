# findings

- 采纳小样 / 成片时的权限回退在 `video_chain._accept_outputs`：越权（creative_execution_rights_escalation）就把公开和给模型用一起关，这是 581 给模型用变成否的原因。
- `creative_executions._rights` 对每一项单独判断越权，所以「不公开、给模型用」可以单独过。
- AE 渲染（craft_skills.render）每次新建素材，公开 / 给模型用按当时输入的权限 all() 计算，不查旧渲染。
- 现有界面只有「撤销公开」，没有「改成公开」。
