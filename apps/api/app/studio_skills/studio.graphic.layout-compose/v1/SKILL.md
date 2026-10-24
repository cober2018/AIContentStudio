---
key: studio.graphic.layout-compose
version: 1
source_kind: studio_builtin
---

这是注册的确定性工具，不调用大模型，不执行本包脚本。仅接受人工接受的graphic.card-plan.v1、固定版本的视觉预设以及项目可见的精确素材和事实引用。template选择已支持的有限排版，density实际改变字体与间距。服务端计算稳定canvas/layer id、字形大小、边距和语义图形；字号在密度基准与上限之间取能放下的最大值（封面标题≤120、内页标题≤84、正文≤56、图解标签≤40，为中密度上限，低/高密度按比例放大/缩小），内容块整体放在安全区略高于中线处；任何引用、尺寸、溢出或缺失摄影需求都必须阻断，不偷偷换素材。产物只是graphic.master.v2候选提案，人工接受才创建MasterRevision，PNG必须再由真实Renderer产生。
