# findings

- 需求里被截断的两句按审计原文补全：补算时成片和原片必须用同一种读法（旧记录的成片读数不能和新读法读的原片直接比）；60 镜存不下时亮度对比和颜色标记提示一起最先保留。
- craft-resolve 里用 ffmpeg 抽帧的地方：delivery.md 截封面命令；color.md 第 14 行 signalstats（直接读 Y 码值，不经过 RGB 换算，不受影响）、AE 叠层一节和 HLG 一节的「抽帧比」。video_chain 规则第 46 行讲封面抽帧。
- 审计方 Chrome 测试页：page.html 读 bands_srgb.mp4（bt709 / sRGB 标记）0.2 秒处三个色带的 canvas 像素。
- 2026-11-03 快速换算只在整尺寸画面上出现（160 宽测不出来）。灰度那条路只在 bt709 标记时偏暗；转 RGB 那条路在整尺寸下三种标记都偏暗（标准纯色片上 Y=235 读成 253）。加 `flags=accurate_rnd+full_chroma_int` 后都和标准换算一致。
- `-sws_flags` 放在 `-i` 前面不起作用；写在 scale 滤镜里（`scale=flags=…`）或放在输出位置才行。
- 带 bt709 标记直接编码测试片时，ffmpeg 会自动插一次色彩换算，改动像素，造成假结果；测试片要先不带标记编码，再用 bitstream filter 只改标记。
- 和 Chrome 比：饱和色边缘因为颜色隔像素存储、补色算法不同会有个别大差值（蓝色通道最多 30），整体平均在 1 级内。
