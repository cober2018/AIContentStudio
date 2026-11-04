# progress：ae-tech-templates

- 2026-11-04 方案写好，等确认。
- 2026-11-04 用户确认，已实施：
  - `make_templates.py`：加 `FPSS`（只给 tech-points / tech-summary 设 60 帧）、`LENS` 加两款（30 秒 / 15 秒）、新增 `flyIn`（表达式选择器按字错开的模糊飞入）、`metal`（渐变实底以文字为 Alpha 遮罩）、`techBg`（深色径向渐变、颗粒、四角框、左上小标题、右上 60 帧时间码、底部进度刻度）、`techPoints`、`techSummary` 和样例（作品 94 文字）。
  - `landscape_layouts.py`：两款横屏各换一组排版参数。
  - 两份 manifest（draft、fps 60，字段见 design.md）。
  - 工程搭在 `~/AIContentStudio/ae-templates/tech-points|tech-summary/v1/`，竖屏、横屏各 1 个（tech-points 32 层，tech-summary 19 层）。搭之前 AE 开着作品 94 的 rough-cut.aep（已保存），搭完和检查完已重新打开（dirty=false）。
- 安全区检查（`--until 10`）：样例、最长字数 5 条、最长字数 3 条，竖屏和横屏。第一次竖屏要点卡滑入起点越界 3–11 像素，滑入距离 70→40 后重搭，全部零越界。金属大字是遮罩层、检查工具不看，另外渲染最长字数竖屏 / 横屏用眼睛核对，没出画面。
- 渲染：10 秒 60 帧 aerender 约 16 秒。平台列表里两款为 draft、fps 60；现有模板（如 check-list）工程未动、仍 30 帧。
- 对比视频在 `output/_平台/模板审片/tech-templates-v1/`：`对比-上MotionGit-下AE-横屏.mp4`（声音是 MotionGit 的音效，AE 版本身无声）、`AE科技风-横屏-…mp4`、`AE科技风-竖屏-…mp4`、最长字数截图两张。
- 2026-11-04 用户看过对比视频说「可以，写进 checks」：两款各写 4 条 checks（样例 + 最长字数 × 竖横），出预览 preview-9x16.mp4 / preview-16x9.mp4（60 帧），SKILL.md 加两行（tech-summary 在「金句与对句」，tech-points 在「步骤、流程与对比」）。平台列表两款为 ready、fps 60。未提交。
