# findings：ae-tech-templates

- MotionGit 开源模板是网页动画（Playwright 逐帧截图 + ffmpeg），MIT 许可；字体 Anton / Geist / Noto Sans SC 为 OFL。我们不搬它的代码，只在 AE 里做同类画面，不带 MotionGit 标志。
- 现有 AE 模板全部 30 帧（`make_templates.py` 里 `FPS=30`）；平台渲染按 manifest 的 fps 算帧数（`app/services/craft_skills.py:302`），60 帧模板后端可直接用。
- 成片后期固定 30 帧（`app/services/edit_handoff.py:56,59`），60 帧模板放进 30 帧成片看不出区别，所以成片改 60 帧要另开需求。
- 本机已装思源黑体 SC（Medium / Bold / Heavy），可做粗重的中文大字。
- 文字填充不能做渐变，金属字用「渐变实底 + 文字当 Alpha 遮罩」；遮罩层会被安全区检查跳过，所以金属字要靠排版参数（最大宽度）保证并人工核对。
- 竖屏要点卡左边距 110、滑入 70 像素时起点会越出安全区左边（59），滑入改 40。
