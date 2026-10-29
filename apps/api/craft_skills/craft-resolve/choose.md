# 选用：先找问题，再挑办法

武器库（`techniques/` 与 craft-ae 的 `techniques/`）是储备，不是清单。一条片子只用解决它问题所需的那几招。写导演稿之前读这一页，再只读选中的那几节。

## 克制规则

1. 默认就是硬切 + 跟着配音的节奏。没有问题，就不加手法。
2. 每用一招，要能说出它解决的是哪个问题；说不出就不用。
3. 同一类手法（转场、光效、变速、夹心字、跟踪）一条片最多用一两次。
4. 先满足「用在」，再排除「不用在」；手头素材不满足条件就不用，不硬凑、不用生成图冒充。
5. 状态为「退役」的招不用；「试用」的招可以用，但在镜头备注里标「试用」。
6. 与平台现行规则冲突时，以 `finishing.md`、`edit-combos.md` 和 craft-ae `components.md` 为准。

## 在导演稿里怎么写

每个用了手法的镜头，在备注里写一行：`手法：<条目>/<节名>（试用）— 解决：<问题>`。没用手法的镜头不写。用户审导演稿时看这一行决定留不留。

## 问题 → 办法

先按镜头任务（edit-combos 的组合）挑，再看这里补什么。每行最多挑一个。

| 问题 | 候选办法 | 前提 |
|---|---|---|
| 开头留不住人 | `structure.md` 开场三步；edit-combos Hook reveal | 片长 ≥ 30 秒才用三步；预告要有足够强的画面 |
| 开场没交代环境 | `cutting.md` 景别递进 | 有远、中、近三种景别素材 |
| 中段平，容易划走 | `structure.md` 时钟检查、波峰节奏 | 片长 ≥ 60 秒 |
| 镜头时长拿不准 | `structure.md` 镜头时长按信息量 | — |
| 同一件事逐级升级 | `structure.md` 递进硬切 | 各段有同一个可比较的变量 |
| 两段之间接得生硬 | `structure.md` 段落衔接（旁白 / 旁白收音乐起 / 节拍小混剪） | 混剪需要与下一段相关的 B-roll |
| 进入新场景太突然 | `cutting.md` 声音先入画面 | 有和画面一致的环境声 |
| 结尾拖沓 | `structure.md` 快速收尾 | — |
| 无配音段落没有节奏 | `beat-and-speed.md` 先标节拍再定切点 | 有节拍清楚的音乐 |
| 卡点太规律、看腻 | `beat-and-speed.md` 切分节拍 | 规律已经立住 |
| 动作一闪而过、看不清 | `beat-and-speed.md` 动作顶点快转慢 + 慢放不卡 | 有明确爆发帧 |
| 长动作拖沓 | `beat-and-speed.md` 变速基础 / 曲线变速 | 不是需要看清细节的镜头 |
| 差一两秒接不上 | `beat-and-speed.md` 轻微慢放补空隙 | 补满所需速度 ≥ 70% |
| 两个镜头有相似形状或运动 | `cutting.md` 匹配剪辑 | 素材里真的有 |
| 想表达人物在看、在想 | `cutting.md` 并置产生含义 | 有平静的面部特写 |
| 主体太小，需要强调 | `cutting.md` 后期推镜 | 素材分辨率够 |
| 口播有停顿、口误 | `cutting.md` 口播精剪 | 真人录音 |
| 剪完口误人物跳一下 | 先盖 B-roll；没有再用 `cutting.md` 放大遮跳切 | — |
| 多机位素材 | `cutting.md` 多机位 | — |
| 段落大转折需要过渡 | `cutting.md` 转场只放关键点；具体做法见 `transitions.md` | 一条片 ≤ 2–3 处 |
| 换段时想把观众「带」进下一段 | `transitions.md` 镜头运动接力 | 前后镜头可加运动 |
| 想要一镜到底的感觉 | `transitions.md` 藏切点 | 素材里有遮挡帧 |
| 知识口播换章节、清单换条 | `transitions.md` 色块扫屏与纯色节拍卡 | — |
| 两段都是图形且有线条关系 | `transitions.md` 线条接力 | AE 图形画面 |
| 揭晓、反转那一下 | `transitions.md` 过曝闪白；`beat-and-speed.md` 动作顶点（定格） | 一条片一次 |
| 音乐副歌段需要密集节奏 | `beat-and-speed.md` 硬切连闪与分格并行 | 无口播、节拍清楚 |
| 两句接得急、有断裂声 | `sound.md` 微叠 + 底噪 | 真人录音 |
| 只有一边耳朵有声 | `sound.md` 声道映射 | — |
| 关键瞬间缺冲击力 | `sound.md` 上升音效 | 素材库有合适音效 |
| 音乐结尾生硬 | `beat-and-speed.md` 音乐收在重拍上；`sound.md` 混响尾音 | 音乐不垫在说话下 |
| 撞击、机械动作没声音 | `sound.md` 自录音效降调 | 没有现成音效 |
| 曝光、偏色拿不准 | `color.md` 先看示波器 | — |
| Log 素材发灰 | `color.md` Log 素材先还原 | 知道拍摄曲线 |
| 亮部过曝或暗部死黑 | `color.md` 亮部暗部分开救 | — |
| 画面发灰、没层次 | `color.md` S 曲线 | 已还原、已校正 |
| 某一种颜色太跳 | `color.md` 只改一种颜色 | — |
| 镜头之间色调不一致 | `color.md` 统一全片色调 | — |
| 播放卡 | `workflow.md` 代理与回放分辨率 | — |
| 候选 B-roll 太多 | `workflow.md` 候选素材铺成一条挑 | 平台候选不够用时 |
| 要学参考片的节奏 | `workflow.md` 拆参考片读节奏 | — |
| 动作或运动不够顺滑 | craft-ae `keyframes.md` 缓动 | — |
| 想让关键字出现在人后面 | craft-ae `compositing.md` 三层夹心 | 人物能干净分离 |
| 要换背景或分离主体 | craft-ae `compositing.md` 人物或物体分离 / 绿幕 | — |
| 画面边缘穿帮 | craft-ae `compositing.md` 遮罩挡穿帮 | — |
| 要叠烟雾、粒子、光效 | craft-ae `compositing.md` 混合模式 / 光效只当调味 | 黑底或白底素材 |
| 运动的物体需要标注 | craft-ae `tracking.md` 点跟踪 | 物体有清楚的特征点 |
| 要把内容贴在屏幕、墙面上 | craft-ae `tracking.md` 平面跟踪 | 表面露出够大 |
| 压在画面上的字看不清 | craft-ae `titles.md` 阴影优先、描边兜底 | — |
| 多人分不清谁是谁 | craft-ae `titles.md` 人名条 | — |
| 价格、计数要有紧张感 | craft-ae `titles.md` 数字快速跳动 / 滚动数字窗 | 单个静态数字用 `number-card` |
| 多项数据并列 | craft-ae `titles.md` 半透明信息卡 | 背景不太花 |
| 关键一句被淹没 | craft-ae `titles.md` 关键词重音 | 一句最多一个 |
| 「不是 A 而是 B」读不出对照 | craft-ae `titles.md` 对句与改口 | — |
| 一句核心观点要停下来 | craft-ae `titles.md` 金句卡 | 一条片一次 |
| 标题出现生硬 | craft-ae `titles.md` 标题入场四式 | — |
| 一句话要套多个用途、场景 | craft-ae `titles.md` 词槽轮换 | 3–5 个词 |
| 第一秒要用字压住画面 | craft-ae `titles.md` 冲击开场字 | 开头没有强画面 |
| 长口播分段不清 | craft-ae `titles.md` 章节卡与进度 | 片长 ≥ 60 秒 |
| 结尾引导关注 | craft-ae `titles.md` 关注引导卡 | 角色账号 |
| 截图、实物上要指出一处 | craft-ae `annotate.md` 手绘圈注 | — |
| 给部件、参数、按钮贴说明 | craft-ae `annotate.md` 标注线与取景框 | — |
| 一张图上要按顺序讲几处 | craft-ae `annotate.md` 聚焦压暗与扫描点名 | — |
| 细节太小看不清 | craft-ae `annotate.md` 局部放大镜；`cutting.md` 后期推镜（急推） | 素材分辨率够 |
| 横拍素材放进竖屏有黑边 | craft-ae `material.md` 同源模糊底 | — |
| 新闻、文档、评价要当证据 | craft-ae `material.md` 证据截图卡 | 真实且有来源 |
| 一句话里要同时给几张图 | craft-ae `material.md` 多图排版与焦点接力 | 2–6 张 |
| 两样东西对照、前后变化 | craft-ae `material.md` 分屏与前后对比（先用 `compare-pair`） | 有真实素材 |
| 回应评论、讲聊天经过 | craft-ae `material.md` 聊天与评论气泡 | 只用真实内容 |
| 讲软件、工具怎么用 | craft-ae `material.md` 屏幕操作演示 | — |
| 数据只念出来记不住 | craft-ae `data.md` 图表生长 | 数据有来源 |
| 比例、占比 | craft-ae `data.md` 比例点阵 | 比例 ≥ 3% |
| 讲步骤、讲先后 | craft-ae `data.md` 步骤与时间线（先看 `diagram-flow`） | — |
| 几选一、揭晓答案 | craft-ae `data.md` 选项揭晓 | — |
| 路线到达点、几个来源汇成结果 | craft-ae `data.md` 地图路线与流程汇聚 | 先看模板 |
| 截图、照片撑一整句口播 | craft-ae `keyframes.md` 静态画面运镜（先用 `photo-push`） | — |
| 口播人物和图表抢画面 | craft-ae `compositing.md` 讲者让位给图形 | 有人物出镜 |
| 交付参数怎么选 | `techniques/delivery.md` | — |

## 维护

这张表和各招的状态由本地技能 `craft-arsenal` 维护：新招加进来时补行；复盘时按用户审片结果调整候选顺序、补「不用在」、退役。
