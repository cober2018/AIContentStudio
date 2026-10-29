# 卡片梳理（100 张）

来源：`output/editing-techniques/cards/`（影视飓风《剪辑全能必修课》第 1–14 集，剪映演示）。

判定：**保留** = 单独写成一节；**合并** = 并进另一节或现有条目；**舍弃** = 不进技能。

去向条目：

| 简称 | 文件 | 内容 |
|---|---|---|
| 结构 | `resolve-edit/techniques/structure.md` | 开场、全片节奏、段落衔接、收尾 |
| 卡点变速 | `resolve-edit/techniques/beat-and-speed.md` | 音乐卡点、变速、慢放 |
| 组接 | `resolve-edit/techniques/cutting.md` | 镜头组接、口播精剪、多机位、转场、推镜 |
| 声音 | `resolve-edit/techniques/sound.md` | 气口、声道、环境音、音效、混响 |
| 调色 | `resolve-edit/techniques/color.md` | 示波器、还原、一级、局部、统一色调 |
| 交付 | `resolve-edit/techniques/delivery.md` | 分辨率、帧率、编码、码率、音频、封面帧 |
| 效率 | `resolve-edit/techniques/workflow.md` | 代理、挑素材、拆参考片、中间件 |
| 关键帧 | `ae-motion/techniques/keyframes.md` | 关键帧、缓动、多参数同步 |
| 合成 | `ae-motion/techniques/compositing.md` | 抠像、遮罩、三明治层、混合模式、叠加光效 |
| 跟踪 | `ae-motion/techniques/tracking.md` | 点跟踪贴字、平面跟踪 |
| 文字 | `ae-motion/techniques/titles.md` | 数字跳动、滚动数字、信息卡、人名条、文字可读性 |

## 节奏（17）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| opening-hook-question-theme-teaser | 保留 | 结构 | 开场三步（提问、揭题、预告混剪）思路通用；和 edit-combos 的 Hook reveal 互补，写互引 |
| clock-theory-node-distribution | 保留 | 结构 | 按片长四等分安排刺激点，可直接用来检查分镜表 |
| wave-peak-rhythm | 保留 | 结构 | 与时钟理论同属全片节奏，单列一节说明起伏 |
| shot-length-by-information-density | 保留 | 结构 | 镜头时长按信息量定；与 components「镜头 2–5 秒」不冲突，写成补充 |
| ladder-progression-no-transitions | 保留 | 结构 | 递进式硬切，适合产品对比、价格递进 |
| fast-ending-no-long-goodbye | 保留 | 结构 | 收尾规则；与 Closing question 互补 |
| narration-out-beat-in | 保留 | 结构 | 段落衔接手法之一 |
| auto-beat-cut | 保留 | 卡点变速 | 剪映「踩节拍」→ Resolve 时间线标记 + 平台对音乐做节拍检测；思路是先有节拍坐标再定切点 |
| syncopated-beat-cut | 保留 | 卡点变速 | 局部打破节拍规律，写清使用次数上限 |
| music-trim-on-downbeat | 保留 | 卡点变速 | 音乐在重拍收尾，而不是只淡出 |
| curve-speed-custom | 保留 | 卡点变速 | 剪映曲线变速 → Resolve Retime Curve |
| action-speed-ramp | 保留 | 卡点变速 | 围绕动作顶点快转慢 |
| constant-speed-handles | 合并 | 卡点变速 | 并入「变速」基础说明（Resolve Change Clip Speed） |
| smart-frame-interpolation | 保留 | 卡点变速 | 剪映帧融合 / 光流 → Resolve Retime Process（Frame Blend / Optical Flow） |
| high-frame-rate-slowmo | 合并 | 卡点变速 | 并入补帧一节：优先用高帧率素材 |
| speed-beat-sync | 舍弃 | — | 剪映一键预设，没有可迁移的做法；思路已被 action-speed-ramp 覆盖 |
| manual-gap-cut-by-waveform | 合并 | 组接 | 并入「口播精剪」 |

## 转场（2）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| transition-preset | 保留 | 组接 | 转场只放关键点、风格克制，Resolve 转场时长写法 |
| broll-beat-montage | 合并 | 结构 | 并入「段落衔接」 |

## 镜头组接（10）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| shot-size-progression | 保留 | 组接 | 景别递进开场 |
| match-cut | 保留 | 组接 | 形状 / 运动匹配，适合产品展示 |
| kuleshov-action-to-closeup | 保留 | 组接 | 并置产生含义 |
| j-cut-ambience-preload | 保留 | 组接 | 声音先入；Resolve 中把音频片段起点提前 |
| zoom-to-hide-jump-cut | 保留 | 组接 | 口播跳切用放大伪装第二机位，可脚本（Zoom 属性） |
| keyframe-push-in | 保留 | 组接 | 后期推镜；缩放与位置同时打关键帧（Resolve Transform / Dynamic Zoom）；与 components 素材卡片缓推 100→104% 区分用途 |
| interview-cut-to-speaker | 保留 | 组接 | 采访切点规则，并入「多机位」节 |
| multicam-live-switch | 合并 | 组接 | 并入「多机位」：Resolve Multicam Viewer 实时切 |
| frame-accurate-trim | 舍弃 | — | 基础操作；平台装配已按帧数裁剪 |
| overlay-track-pip | 舍弃 | — | 基础叠轨；平台用 AE 素材卡片组件实现 |

## 调色（9）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| waveform-exposure-check | 保留 | 调色 | 「先看示波器」：波形看曝光 |
| rgb-parade-white-balance | 合并 | 调色 | 并入「先看示波器」：分量图看白平衡 |
| vectorscope-tint-correction | 合并 | 调色 | 并入「先看示波器」：矢量图看偏色 |
| log-lut-restore | 保留 | 调色 | Log 还原 → Resolve Color Space Transform 或对应 LUT |
| highlight-shadow-control | 保留 | 调色 | Resolve Primaries 的 Highlights / Shadows |
| color-wheels-four-zones | 保留 | 调色 | Lift / Gamma / Gain / Offset |
| rgb-curve-s-contrast | 保留 | 调色 | Custom Curves S 型 |
| hsl-single-color-hue | 保留 | 调色 | Hue vs Hue / Hue vs Sat 曲线，或 HSL 限定器 |
| color-clone-match | 保留 | 调色 | Resolve Shot Match 或抓静帧复制调色 |
| adjustment-track-color（工作流类） | 合并 | 调色 | Resolve 节点本身可逆；写成「调色放在节点 / 调整片段上，不直接改素材」 |

## 声音与音乐（10）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| overlap-tight-gaps-with-room-tone | 保留 | 声音 | 气口太紧时微叠 + 房间底噪 |
| fill-missing-audio-channel | 保留 | 声音 | 单声道补双声道；Resolve Clip Attributes 声道映射，可脚本检查 |
| rise-sound-opening | 保留 | 声音 | 上升音效在入点前蓄力 |
| audio-compound-reverb-space | 保留 | 声音 | 剪映要用静音副本；Fairlight 把混响放在轨道上，尾音自然延续，做法更简单 |
| custom-foley-pitch-shift | 保留 | 声音 | 自录音效降调变速；Fairlight Pitch |
| music-first-segment-mapping | 保留 | 结构 | 粗剪先用音乐定段落情绪 |
| narration-segment-bridge | 合并 | 结构 | 并入「段落衔接」 |
| bgm-tail-fade | 合并 | 声音 | finishing.md 已规定淡出 1.5 s；并进来说明「重拍收尾优先，淡出兜底」 |
| audio-export-quality | 合并 | 交付 | 并入交付的音频参数 |
| ai-sound-effect | 舍弃 | — | 剪映独有功能，DaVinci / AE 无对应 |

## 字幕与标题（3）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| text-shadow-outline-readability | 保留 | 文字 | 阴影、描边保证可读，AE Drop Shadow / Stroke |
| interview-name-lower-third | 保留 | 文字 | 人名条；标为 AE 模板候选 |
| auto-subtitle-and-style | 合并 | 文字 | 字幕生成已由 finishing.md 规定（ASR 对齐、按标点断句）；只补「平台界面安全区」和「先识别再加音乐」 |

## 包装与特效（21）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| keyframe-easing（keyframe-curve-easing） | 保留 | 关键帧 | AE Easy Ease / 图表编辑器；所有参数同一缓动 |
| keyframe-two-point-basic | 合并 | 关键帧 | 并入关键帧基础 |
| material-parameter-panel | 舍弃 | — | 剪映面板入门 |
| smart-keying | 保留 | 合成 | 人物分离：Resolve Magic Mask / AE Roto Brush |
| custom-keying-brush | 合并 | 合成 | 并入人物分离（物体用画笔补选） |
| chroma-key-green | 保留 | 合成 | 绿幕：AE Keylight / Resolve 3D Keyer |
| chroma-key-edge | 合并 | 合成 | 并入绿幕：边缘收缩羽化、去溢色 |
| mask-frame-green | 保留 | 合成 | 垃圾遮罩挡穿帮 |
| keying-sandwich | 保留 | 合成 | 人物在前、文字在中、背景在后 |
| blend-mode-blackwhite | 保留 | 合成 | 黑底用 Screen / Add，白底用 Multiply |
| light-leak-overlay | 保留 | 合成 | 光效叠加只作调味；写使用上限 |
| text-tracking-three-steps | 保留 | 跟踪 | 点跟踪贴标签：AE Track Motion / Resolve Fusion Tracker |
| planar-track-text-on-surface | 保留 | 跟踪 | 平面跟踪：AE Mocha AE + Corner Pin |
| planar-track-quad | 合并 | 跟踪 | 并入平面跟踪：选最大平面帧画范围、借参照物 |
| planar-track-perspective-adjust | 合并 | 跟踪 | 并入平面跟踪：手调 Corner Pin |
| planar-track-plane-vanish-trim | 保留 | 跟踪 | 平面离开画面前收掉素材 |
| text-compound-for-planar-track | 舍弃 | — | 剪映限制（文字要打包才能跟踪），AE 无此问题 |
| text-stretch-fix-nonuniform-scale | 舍弃 | — | 剪映复合片段导致的问题，AE 无此问题 |
| number-flicker-frame-split | 保留 | 文字 | 数字快速跳动；AE 用 Source Text 关键帧或表达式 |
| rolling-number-window | 保留 | 文字 | 滚动数字窗；标为 AE 模板候选（number-card 的变体） |
| translucent-timer-panel | 保留 | 文字 | 半透明信息卡；标为 AE 模板候选 |

## 导出与规格（8）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| resolution-match-source | 保留 | 交付 | 不超过素材原生分辨率 |
| fps-follow-draft | 保留 | 交付 | 交付帧率等于时间线帧率；与 finishing「先定分辨率帧率再建时间线」合并说明 |
| container-and-codec | 保留 | 交付 | H.264 默认，HEVC 的取舍 |
| bitrate-choose-recommended | 保留 | 交付 | 码率不盲目拉满，平台会再压 |
| ai-upscale-interpolation-caveat | 保留 | 交付 | Resolve Super Scale / 补帧只救单段 |
| cover-frame-selection | 保留 | 交付 | 封面不用首帧；只写挑帧标准，封面制作走平台封面步骤 |
| export-basic-settings | 合并 | 交付 | 并入各参数小节 |
| demo-then-final-export | 舍弃 | — | 平台已有小样 → 成片流程与目录 |

## 工作流效率（20）

| 卡片 | 判定 | 去向 | 理由 |
|---|---|---|---|
| smart-cut-by-transcript | 保留 | 组接 | 口播精剪：Resolve 文字剪辑（转录后删字）；保留好气口 |
| multicam-sync | 合并 | 组接 | 并入「多机位」：按音频 / 时码同步 |
| multicam-change-angle-fix | 合并 | 组接 | 并入「多机位」 |
| speed-to-fill-gap | 保留 | 卡点变速 | 轻微慢放补空隙，可脚本 |
| segmented-editing-assemble | 保留 | 结构 | 长片分段剪再总装 |
| proxy-mode | 保留 | 效率 | Resolve 代理 / 优化媒体 |
| preview-quality | 合并 | 效率 | 并入代理：降低回放分辨率 |
| broll-audition-timeline | 保留 | 效率 | 候选素材铺一条时间线对节拍挑选 |
| smart-shot-split | 保留 | 效率 | Resolve 场景剪切检测，用来拆参考片读节奏 |
| intermediate-export-before-packaging | 保留 | 效率 | 重效果先渲染成中间件再包装；与 native-execution 的 AE 中间件规则一致，写互引 |
| keyframe-multi-param-align | 合并 | 关键帧 | 并入多参数同起同止 |
| clip-params-multi-select | 舍弃 | — | 基础操作 |
| main-track-magnet-off | 舍弃 | — | 剪映独有设置 |
| free-layer-default | 舍弃 | — | 剪映独有设置 |
| timeline-zoom | 舍弃 | — | 基础操作 |
| timeline-shift-right-all | 舍弃 | — | 基础操作（Resolve 波纹插入即可） |
| planar-track-rename-planes | 舍弃 | — | 剪映界面操作 |
| export-filename-convention | 舍弃 | — | 与平台规则冲突：成片命名和存放由平台管理 |
| numbered-asset-folders | 舍弃 | — | 与平台规则冲突：项目素材目录由平台统一建立 |

## 统计

| 判定 | 数量 |
|---|---|
| 保留 | 62 |
| 合并 | 22 |
| 舍弃 | 16 |

## 和现有条目的关系

| 现有条目 | 关系 |
|---|---|
| `edit-combos.md` Hook reveal / Closing question | 开场三步、快速收尾是补充，不冲突；互相引用 |
| `components.md` 镜头 2–5 秒、素材卡片缓推 | 信息密度定时长是补充；后期推镜是另一种用途 |
| `finishing.md` 音乐淡出 1.5 s、字幕 ASR 对齐 | 平台规则为准；课程补充重拍收尾和安全区 |
| `native-execution.md` AE 中间件回 Resolve | 中间件思路一致，互引 |
| 平台标准项目目录、成片命名 | 课程做法冲突，舍弃 |
