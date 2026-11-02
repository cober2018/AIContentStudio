# findings

- 过曝原因：iPhone HLG 实拍在达芬奇默认色彩管理下平均亮度约 190，苹果显示约 147；拟合 LUT（MCP/iphone-hlg-apple-sdr.cube 与渲染补偿版 -render.cube）后 146.8。LUT 已在 /Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/MCP/。该做法只在开发助手笔记里，平台规则与 craft-resolve 没有，导致每条新视频重复过曝。
- craft-resolve color.md 有「统一全片色调」但为可选；finishing.md 只要求配音母带与整片响度；平台交付只测整片响度（creative_media_stream.loudness）。
- 返修意见：video_chain.decide 把 notes 存在该作品的 video_chain 记录里，只给当前模型看，无跨视频沉淀；learning_candidate、content_memory_entry 均 0 行。
- 用户纠正的假设「按第一镜调亮度套全片」与实际原因不符，方案按实际原因修。
- 交付检查默认阈值：平均亮度 >180 或贴顶像素 >5% 算过曝；相邻镜头差 >40 算跳变；说话镜头偏离中位数 >6 LU 算音量不齐。只提示不拦。
- .cube 文件不能经 get_craft_skill 取，规则写明从仓库路径拷到达芬奇 LUT/MCP。
- 已有的整片响度提示仍未在审阅页显示（不在本次范围）。
