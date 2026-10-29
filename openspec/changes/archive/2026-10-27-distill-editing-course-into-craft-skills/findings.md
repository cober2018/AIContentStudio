# 发现与决策

- 课程全程用剪映演示；用户确认：课程提供思路，要换成 DaVinci / AE 的做法（2026-10-27）。
- 不新建技能，写进现有 `craft-resolve`、`craft-ae`；`craft_skills.skill_entry` 允许子目录条目，无需改代码。
- 卡片统计：可脚本 0、部分 39、手动 61；置信度高 79、中 21。
- 用户要求：武器库只是储备，实战只用几样 → 加选用表和克制规则；方法要能进化 → 每招带状态并按审片结果复盘；由单独的维护技能 craft-arsenal 管整套流程（2026-10-27）。
- 第三方模型通过 MCP 只能读技能、读单条片子的决定，不能写技能文件，所以维护技能放本地 `.codex/skills/`，由在仓库里工作的模型执行。
- DaVinci 接口核对（Resolve 21.1 脚本 API）：SetSpeed{Percentage}、RetimeProcess/MotionEstimation、AddMarker、TranscribeAudio、DetectSceneCuts、CreateMulticamClip、CreateMagicMask、SetFades、Get/SetSourceAudioChannelMapping、AudioPitchSemiTones、Graph.SetLUT、SetCDL、CopyGrades、GrabStill、ColorGroup 可用；Retime 曲线、S 曲线、Hue 曲线、Shot Match、示波器读取不能脚本。
- 本机 runtime.env 的 REQUIRED_SCHEMA_HEAD 仍为 matmatch0001，导致健康检查 503；与本需求无关，待用户决定是否修。
