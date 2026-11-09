# findings
- 旧五步里「制作内容」挂主稿编辑器（ModalityWorkspace → GraphicStudioShell → GraphicRenderPanel），「审阅修改」挂主稿审阅；交付一步对文字/图文其实只有底部高级块。
- 只有 GraphicRenderPanel 及其两个接口会完全没人用；主稿面板、创作流程、执行包、方法面板商品作品和视频「高级」还在用，不能删。
- 平台模型的稿子经 creation-recipe/stages/{node}/accept-master 采用；写作链 _state 对平台写作一直返回 platform，从不进入采用。
