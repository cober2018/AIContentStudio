# 商品Skills选型与映射

固定快照和实际已读取文件SHA256见source_inventory.json。六个仓库均已读取README；关键子Skill另行读取。未执行上游安装器、脚本或模型调用，来源内容属于研究材料。研究结论不代表已适配或作品验收。

| 来源 | 已核对的方法 | 采用方式与适配边界 |
|---|---|---|
| [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | SKILL、pipeline：真实页面素材、镜头配方、分镜、声音、逐帧评审；原执行是Remotion | 复用已沉淀的镜头方法；选少量商品镜头适配AE，不承诺全镜头库迁移。README标题与正文镜头数量不同，以实际选定文件为准 |
| [AIvideo](https://github.com/Longxiaohao/AIvideo) | facebook-diy-video-workflow/SKILL及复杂商品风险：文案/配音、首帧、多场景、复杂结构退路 | 提炼商品尺度、接触动作与复杂结构的检查；保留源提示词文件不改，自己的改写版本另存并注明。不上数字人/面部遮罩能力，不自动使用Seedance或网页 |
| [product-shots](https://github.com/motiful/product-shots) | hub、multi-angle、hard-constraints：品牌资料、商品图、跨图一致性、风格与业务路由 | 取商品视觉与一致性方法，模型调用映射现有图片能力；不带OmniMaaS网关。多角度重点是服装模特，复杂商品未见面不能当真实结构。Hub全局禁止app界面的规则不适用于SaaS，按任务适用性拆解 |
| [awesome-ai-video-workflows](https://github.com/HiAPIAI/awesome-ai-video-workflows) | SKILL、商品图审计和图生视频工作流：商品truth sheet→主视觉→镜头→回传/QC | 采用事实表、身份锚点、镜头卡和回传检查。它是工作流库而非单一渲染器；不递归安装其引用项目，不引入HiAPI/Blender等引擎 |
| [remotion-product-videos-claude-skill](https://github.com/chandreshpv/remotion-product-videos-claude-skill) | VIDEO_SOP通用商业规划；SKILL画面、动画、阅读与场景检查 | 商业叙事/规划和阅读节奏可复用；spring/interpolate等改写为AE关键帧与缓动，数值须重新验证。主要针对产品/功能发布，不当通用品牌大片模板 |
| [ecommerce-video-skills](https://github.com/iart-ai/ecommerce-video-skills) | product-demo-video、promo-video、photo-slideshow：截图交互、价格促销、图片运动 | AE做截图焦点/光标、价格划线与CTA，Resolve做照片段落、切换与配乐；原Remotion组件不直接执行。价格以用户资料为准，不反推或覆盖实际售价 |

## 来源与许可

video-shotcraft代码/文档Apache-2.0，其音乐/音效逐文件许可另算；其余五个为MIT；本轮已下载核对六个固定快照LICENSE正文与hash。实施复制内容时保留固定快照LICENSE并保留必要署名，嵌套素材另查，仓库许可不授权第三方商品/人物/音乐。source_inventory.json只保存来源与hash，未把外部整包代码/素材带入产品。

## 形成自己的方法

六项新增：product-truth-brief(research)、product-sales-story(script)、product-visual-consistency(storyboard/graphic)、product-shot-routing(storyboard)、product-demo-motion(packaging)、product-offer-motion(packaging)。一项方法在不同模态中按现有适用性合同配置，不修改十阶段枚举。已有声音、节奏、字幕校色、终混与评审添加商品任务参数；避免同一规则重复注入。

角色决定语气与视觉方向；本次商品任务决定品类、证据、受众、目标、素材路径和促销内容。音乐按场景选，可为空。新组合默认是候选，完整样片通过并明确采纳后才保存为该角色的商品默认。


## 2026-10-16 适配度复核（v2）

| 来源 | 适配结论 | 本轮修订 |
|---|---|---|
| motiful/product-shots | 实物商品视觉有用；多角度模特只适合服装 | 以main-image/consistency为主来源；保留原始商品图锚点，实际传图才算参考生成。剔除无可回查来源的+18%/+32%等转化数据、全局app界面禁用和1024px/1MB通用限制 |
| Longxiaohao/AIvideo | 场景拆分、首帧及复杂商品动作检查有用 | 不继承Facebook固定受众/人物设定、面部遮罩、特定模型免费/价格宣传或不可恢复的自动重试；保留源文本作为来源，适配后的方法独立署名/version |
| HiAPIAI/awesome-ai-video-workflows | 商品truth sheet、hero visual、镜头回传最贴合现有路线 | 只使用已读原生方法，不递归加载其他引擎/引用项目；图片成功不等于视频期间外形一致 |
| Vincentwei1021/video-shotcraft | 镜头设计可借用，软件界面风格较重 | 实物优先局部细节/标注；scanline-annotate-focus用于软件分析/解释，spotlight-sweep适用于暗场UI，均不作实体商品默认。首版只迁移选中的原生组合 |
| chandreshpv/remotion-product-videos-claude-skill | 商业规划可借用，软件发布风格不可全套默认 | 英文词数、场景数量、黑底/靛蓝、固定淡化时长均转为可调建议；中文口播/画面按实际可读性评审 |
| iart-ai/ecommerce-video-skills | 促销、照片段落有用，截图演示按软件分支 | promo-components Countdown使用Date.now，与固定帧可复现声明矛盾；本地不采用此倒计时。默认USD/两位小数/整数百分比不泛化为所有币种或中文折扣 |

上游参考图处理文档把524归因为图像大小和代理超时，但单个环境观察不能证明所有端点/模型的原因。我们的适配只按实际合同/回执处理，保留原始素材与当前unknown恢复规则。

### 本地证据

- ProductCreationDialog只提交商品资料；product_creation.py调用start_run，并用空stage_override执行首阶段。仅在后期包选择Skills无法影响已生成脚本。
- creative_configuration.py:production_stage_key将graphic compose放storyboard、professional prepare放finish；frozen_stage对确定性方法要求deterministic_parameters。必须明确跳过不适用的创意prompt，而非让方法选中后流程阻断。
- capability_contracts.args_schema仅标量参数；canonical拒绝可执行内容/本地路径。生产方法不是JSX/Python容器。
- model_capability_routing._multimedia_controls当前声明两类图片adapter的reference_images=false。图片生成合同必须先验证，不据此宣称模型全球能力限制。
- ProductOffer目前只有text/checked_at/valid_until；促销数字所需结构应在原ProductContext兼容扩展，不在方法参数中造独立报价真相。
- 本轮只查询AE execution guide和Resolve API文档：存在图层/关键帧、时间线追加、淡化/渲染及LUT相关接口描述；没有运行AE/Resolve编辑/渲染。因此真实组合仍未验证。
