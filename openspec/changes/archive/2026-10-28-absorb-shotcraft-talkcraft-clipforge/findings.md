# 发现与决定

- 许可证：shotcraft Apache-2.0；talkcraft PolyForm Noncommercial（商用需作者授权，2026-10-16 方案也因此未采用）；clipforge AGPL-3.0。
- shotcraft、talkcraft 都用 Remotion 渲染；用户决定只吸收配方换成 AE / 达芬奇做法，不引入 Remotion。
- clipforge 按平台 skill 边界内化为商品 skill，挂在商品体系。
- 用户原则：角色、商品两套独立 skill 体系，只有剪辑特效工具共用。
- 2026-10-28 用户补充：通用 skill 两边都要放。体系改为三类：商品 / 角色 / 通用（两边可用），剪辑特效另外共用。
- 2026-10-28 用户要求：免费素材抓取、数字人也要。映射表加 #10 免费素材找挑（通用 skill，用平台现有来源执行）、#11 数字人出镜（通用 skill，能力归纳，功能未上线前只用于规划）；新来源接入和数字人生成功能另提需求。
- 平台素材搜索（`open_media.py`）实际已接 6 个来源：Pexels、Pixabay、Openverse、Wikimedia Commons、NASA、Internet Archive。真正缺的只有 Coverr（视频）、Freesound（音效）、Jamendo（音乐），已更正映射表。
- 新建的 4 个 skill 没有平台阶段承接，只给第三方模型读，所以不声明可调字段（声明了会被「每个可调字段都要有阶段消费」的校验拦下）。
- 脚本评审 key 用 `studio.video.script-review`（不是映射表初稿的 `studio.text.*`）：text 类 skill 会自动挂到文章正文阶段，不合适。
- shotcraft 约一半卡是软件发布片的界面动效和品牌 logo 开场，和竖屏口播、带货不对口，舍弃；talkcraft 是知识口播包装，大部分可用。两边有 10 多张同名卡，合成一条。
- 「聊天与评论气泡」只能放真实评论、真实聊天；带货里编造好评属于编造用户评价。
- 平台写作 skill 实际是三类（商品 / 角色 / 通用），spec 已按用户要求从「两套」改为三类。
- 武器库新节来源只写仓库和卡名，提交号记在 craft-arsenal log（沿用课程条目只写来源名的规则）。
