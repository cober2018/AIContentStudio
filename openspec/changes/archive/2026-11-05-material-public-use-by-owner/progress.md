# progress

- 2026-11-05 核实：309 公开否 / 给模型用是（用户上传）；546 公开否 / 给模型用是（AE 渲染继承）；581 两项都否（采纳时越权就全关）；create_revision 和 AE 渲染都不复用旧版本。写好方案，待确认。
- 2026-11-05 用户确认后实现：
  - `materials.allow_public_use` + `POST /materials/{id}/revisions/{rid}/allow-public-use`：只限自己上传（source_kind upload、登记人本人）、cleared、未撤销 / 归档；写审计 `material.public_use_allowed`。
  - 素材详情抽屉「改成可公开使用」+ 确认框，只在自己能改的条件下显示；报错显示服务端原话。
  - `video_chain._accept_outputs`：越权时先退到「不公开、给模型用」，再退到两项都关。
  - `content_masters`：权限不够的 422 带 message（`_rights_reason` 顺着交付记录输入和 AE 渲染图片来源往上找）；种类 / 状态不对的仍是原样。MCP 透传 `video_asset_` 报错原文；视频规则加「权限只有用户能改」。
- 库副本验证：
  - 作品 95 开成片：「成片要接着用的小样素材 581…不能给模型用也不能公开：用了第 40 镜的素材 546「资料卡关注（简洁款）· 知数Talk」，它又用了素材 309「知数Talk Logo」，后者不能公开。请用户在素材详情里把素材 309 改成可公开使用…」。
  - 546（AE 渲染）、别人名下的 309 → `material_public_use_not_owner`；本人改 309 → 成功。
  - 309 改好后用 309 重渲 follow-card-x → 新版本 599，公开 / 给模型用都是，来源 [309]，没复用 546；渲染文件（真库无引用）已删。
  - 采纳任务 54 时模拟「公开越权」：成片先试（公开, 模型）=（是, 是），再（否, 是）成功；工程文件仍（否, 否）。
- 全量测试 2441 通过，5 个原有失败；前端 tsc、build 通过。
- 2026-11-05 重启 API 和 worker，健康检查正常。
