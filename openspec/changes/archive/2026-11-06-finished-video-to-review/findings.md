# 发现
- content_unit.status 只在「编辑内容单元」手改（content_projects.py:817），平台不自动改；实际只有 draft / archived。
- v4 候选（candidates_v4.py:63）需要渠道 + 内容形态、render_attestation、导演稿全部素材权利字节；审批（production_validation.validate_live_v4_candidate）、授权（delivery.py:116）、ZIP（delivery.py:624 → production_packages.build_v4_package）、审阅预览（project_review_projection.py:287）都会对照导演稿重查；回填（routers/delivery.py:230）和效果复盘同步（published_history.sync_receipt）只看哈希一致。
- v4 ZIP 会把清单里所有素材都打包（含镜头原始素材）。
- 作品 95、96 冻结 v4 都被拦：asset_unready（镜头素材）、channel_form_missing、render_attestation_missing。
- 视频链已定稿的作品：80、85、90、92、93、94、95、96（93、94 不动）。
- 商品视频工作台作品页（ProductWorkbench.tsx）显示原始 status 英文。
