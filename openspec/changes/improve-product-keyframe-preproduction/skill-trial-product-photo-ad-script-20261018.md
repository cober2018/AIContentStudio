# 商品商拍与广告脚本方法适配试验

## 需求与结论
用户要求核对并试用beatra-ai/ai-product-photography-skill与snailzsh/ad-script-master；同时要求查系统卖货资料。沿用SKU-000003儿童拖鞋棕灰两双装。用户否定原四镜外观巡览：需要购买理由驱动，每个场景约6–8秒，突出软、跟脚、耐磨、可爱。旧Master49与图65–68留档，本轮不继续旧网页生成包，不自动改正式方法开关或选图。

结论：两者可组成方法流程，但不宜原样接入。已做一次脚本方法演练和一张实际图片生成；未安装为全局Skill，未调用Beatra原生服务，未生成视频，未做商业转化验证。

## 实际读取的源资料
- https://github.com/beatra-ai/ai-product-photography-skill ：README（声明MIT-0）、skills/product-photo-studio/SKILL.md、references/scene-craft.md与product-routing.md。
- https://github.com/snailzsh/ad-script-master ：README（声明MIT）、SKILL.md、evals/evals.json。
- 读取日期2026-10-18；GitHub API获取提交SHA失败，不能声称锁定源码commit。此次不复制或安装代码，只做方法适配与自写输出。

Beatra的三条路线是背景替换、场景置景、已选图局部修整；原生工具为images.transform/edit，经其bundled MCP client执行，需账号与积分。保真依靠源图输入、提示词和输出审阅，没有查到保证Logo/标签逐像素不变的独立约束算法。具体平台主图规则仍需查平台，Skill不自动保证合规。

ad-script-master是Markdown指令，五步覆盖商业目标、人物场景、节奏、分镜矩阵、结尾卡。其“合规”是要求模型检查的文字指令，不是法规数据库/自动过滤程序；“防幻觉”是拆分复杂动作的方法，不是视频后处理引擎。evals只有5个输入和expected_output，无此次实测结果、销量或对照转化证据。

需要调整：原文长片时间区间与比例不一致，30秒至3分钟共用固定长片节点不可照搬；前文禁止温馨等感性词，后文又建议温暖治愈预设，不能当严密合同。Seedance中文/时长/延长等参数没有在本轮向官方核验，不传播成Grok/Gemini能力。摄影参数是表达意图而非物理相机控制；自然手机展示无需堆ARRI、f值、十六进制色值。超现实、电影情绪峰值、至少4–6场景、硬性结尾卡均不作为本次必选项。

## 两方法的正确串联
先广告策略：买家情境→一个购买理由→相应证据/演示→场景任务；再商拍方法：原图外观核对→为动作准备关键帧→看图确认；再广告分镜方法：据确认画面写短动作→人工网站生成→真实回片审阅→Resolve声音/节奏/调色，AE按需。不是先随意精修一批图，再硬编故事消耗图片。

## 本轮脚本演练（提案，非最终广告事实）
总长约24秒的起点，不强制固定；每段6–8秒可以包含多个剪辑切点，生成任务仍按模型可完成的单动作拆分。用户所述软/跟脚/耐磨记为卖方提出的卖点，尚无实物验证；不能从AI图升级为已验证事实。

| 段落 | 购买理由/顾虑 | 实际画面设计 | 文案状态与素材需求 |
| --- | --- | --- | --- |
| 0–8秒：触感 | 给孩子选家居鞋，先看触感 | 近景指尖划过鞋面；真实轻压回弹作第二切点（有素材才用） | 核验后可试“给孩子选家居鞋，我先看软不软。”；当前试图只表现触摸，不能证明柔软/舒服 |
| 8–16秒：活动 | 在家走动时跟不跟脚 | 低机位侧面真实走两步，接脚后跟近景 | 需实际穿着片和合适尺码；AI走路不能当跟脚性能证明。旁白候选“再看走起来，鞋跟不跟脚。” |
| 16–24秒：外观与选择 | 孩子愿不愿意穿；家长看组合 | 卡通装饰近景→两色两双同框；孩子选择只能作情境，真实反馈另需依据 | 现有外观支持“卡通装饰，棕灰两色，一套两双。”；最后商品页/尺码入口待真实入口落实 |
| 可替换单段：鞋底 | 耐磨顾虑 | 鞋底实拍/有条件说明的真实测试 | 原图看不到鞋底，缺参照与测试；不生成猜测鞋底，不以摩擦动画证明耐磨 |

这是一条销售逻辑候选而非四卖点全部塞入；可先测试触感版与外观版，其他条件尽量一致。客户评论/订单/退货才用于判断销售效果，本轮没有这些数据。

## 实际图片试验
- 输入：用户原始截图，MaterialRevision64对应文件；未使用旧AI图替代商品依据。
- 引擎：Codex内置imagegen；借鉴product-photo-studio的参照/布景/光线/审图方法，不是Beatra原生性能测试。
- 输出：[触摸场景v1](keyframes/children-slippers-skill-trial-touch-v1.png)；提示词同目录`children-slippers-skill-trial-touch-v1-prompt.txt`。
- SHA256：ef68bb0ac23f6b98514002e4d8c9a0650570e02319a6e7281cbed497e95546d8。
- 实际看图：棕灰两色、共四只鞋，一只成人手接触棕色鞋面；自然室内光、地毯与手部关系可读，没有文字或价格。近景有明确触摸任务，比旧版仅拿起展示更贴合当前意图。
- 问题：卡通贴片面部/轮廓及绒毛细节被重绘，不能判为商品精确保真；仅为创意候选，未选用、未上架、未加入Master。静态图不能证明动作不会穿模，也不能证明材质性能。
- 结论：叙事方向可继续讨论；保真终审未通过，暂不生成动态提示词/视频。下一版应使用更清晰商品近照进行局部修正，不批量扩图。

## 系统学习资料（已查官方/作者来源）
1. Value Proposition Design/价值主张画布：用客户任务、顾虑、期望收益整理购买理由；https://www.strategyzer.com/library/the-value-proposition-canvas 。先给家长和孩子分别建购买者/使用者视角，避免混成同一种需求。
2. Scientific Advertising，Claude Hopkins：《科学的广告》，关注销售目的、具体表达与测量；出版社 https://www.simonandschuster.com.au/books/Scientific-Advertising/Claude-Hopkins/9781640954250 。
3. Made to Stick，Chip与Dan Heath：单一核心、具体可信、情感与故事；作者一页框架 https://heathbrothers.com/wp-content/uploads/resources/mts-made-to-stick-model.pdf 。
4. The Choice Factory，Richard Shotton：购买决策心理作为测试假设；https://harriman.house/books/the-choice-factory/ 。不把偏差清单变成保证转化的套路。
5. TikTok官方Creative Codes与SMB Creative Playbook：原生表达、开头/主体/结尾、商品展示；https://ads.tiktok.com/business/library/Creative_Codes_ENG.pdf 与 https://ads.tiktok.com/business/library/Global_SMB_Creative_Playbook.pdf 。
6. 抖音电商官方学习中心/案例库：https://school.jinritemai.com/doudian/web/home 与 https://school.jinritemai.com/doudian/web/ecomcase 。用于中文平台及品类案例，不将成功案例当对照实验。

本轮只读公开资料与真实单图试验，不修改业务代码、默认Skill、SKU事实或正式主稿，不归档提交。依赖现有imagegen与正常联网，无新增软件依赖。
