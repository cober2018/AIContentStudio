# progress
- 2026-11-09 盘点旧代码、写好方案，等确认。
- 2026-11-09 后端：平台模型写的稿（创作流程采用后）停在「稿件待你看」，采用 / 写意见 / 出图 / 验收与第三方模型共用；成图待验收或出图中时任何新主稿（含平台阶段采用）都被拦下（article_chain.save_blocked）。删了 media-render-previews / outputs、media-renderer-verifications / revoke 四个接口，media_renderers 只留 resolve_renderer、scope_fingerprint，provider_media 去掉渲染预览分支，设置页去掉 media_renderer_previews；删 3 个只测手动出图的测试文件，改 2 个。后端全量 2329 通过，5 个旧失败不变。
- 页面：文字 / 图文作品步骤改为 选题与资料 → 稿子 →（图文）成图 → 交付；没到的步骤提示去当前步骤；旧 workstep 落到当前步骤；不再挂主稿编辑器和底部高级块；写作面板拆成稿子 / 成图 / 交付三段。主稿面板、图文编辑器里的旧代码清理进行中。
- 页面清理完成：主稿面板改为只服务视频；图文编辑器去掉手动出图、整组审阅、最终图绑定；删 GraphicRenderPanel.tsx、GraphicStudioModel.bindFinalRender、对应前端测试和两个旧验收脚本（fe-f7-graphic-render、fe-f6a），check-bundle 去掉图文模型单独分包检查。前端类型检查通过、node 测试 36/36、npm run build 通过。
