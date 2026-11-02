# progress

- 2026-11-02 方案已写，等用户确认。
- 2026-11-02 用户确认，开始开发：第一部分（剪辑规则、LUT、交付检查）与第二部分（返修记录、经验库、propose_lesson、经验随任务书下发）并行实施。
- 2026-11-02 第二部分已本地实施，未提交、未上线：迁移 lesson0001（video_lesson、video_rework_record）；services/video_lessons.py；decide() 退回小样/成片时逐条记返修记录；brief() 加 lessons（生效经验 + 本作品未归类返修记录）与 lessons_rule；MCP propose_lesson（同因合并计数、无新来源不重复计数）；设置「经验库」；接口 GET/PATCH /settings/video-lessons、GET /settings/video-lessons/records。
  - 副本验证：同因第二次提议计数到 2；同意后进入任务书；作品 84 走真实退回流程生成 2 条返修记录（空意见跳过）。全量只剩 5 个已知失败，tsc 通过。
  - 待办：正式库迁移后用 video_lessons.ensure_active 录入首条经验（HLG 过曝，计数 3）。
- 2026-11-02 第一部分已本地实施，未提交：video_chain.RULES 加 HLG 还原（必做）、素材统一（必做）、回执要求；LUT 两份入 craft_skills/craft-resolve/luts/（与已装版本 SHA256 一致）；craft-resolve color.md/sound.md/finishing.md/SKILL.md/choose.md 补做法；新 services/delivery_checks.py 逐镜头亮度/高光、相邻跳变、对白分段响度，接在 creative_executions 小样/成片交付检查后，结果存 shot_checks；审阅页（VideoChainPanel）显示提示；设置「交付检查」与 GET/PUT /settings/delivery-checks。
  - P46 实测（默认阈值）：被指出过曝的小样（任务26、27）10/10 镜头报过曝，亮度 187–205、首镜 30.8% 像素贴顶；修正后的成片（任务31）各镜头 132–154，无提示；对白 −13.6～−17.3 LUFS，未超 6 LU。
- 2026-11-02 两部分合并后：全量 2441 通过、只剩 5 个已知失败；tsc 通过；alembic 单一 head lesson0001。等用户确认后迁移正式库、录首条经验、重启。
- 2026-11-02 已上线：正式库迁移到 lesson0001；首条经验「iPhone HLG 实拍出片过曝」录入（id 1，生效，计数 3）；API/worker 已重启；经验库与交付检查接口返回 200。未提交，等用户看界面验收。
