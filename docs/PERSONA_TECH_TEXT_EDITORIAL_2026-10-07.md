# 同一个模型，两种写法：角色配置该放在哪一层？

一套 AI 创作工具，可能既要写技术文章，也要写生活观察。模型连接可以共用，“默认怎么写”却不适合只放在一项全局设置里。本文讨论 AIContentStudio 在 2026 年 10 月 7 日已批准的项目设计，不是行业统计，也不保证生成结果一定更好。

## 共用模型，不共用角色默认

先看一个假设：同一位创作者上午写架构分析，晚上写日常随笔。如果把“多讲技术边界、少用感性表达”保存成所有内容的统一默认，生活稿也可能收到不适合它的要求。问题不在于一个模型能不能写两类文章，而在于这条配置究竟影响谁。

本项目把权限、模型接入和基础设施放在用户层；创作配置则以 Persona 为根，Account 和 Series 可以明确覆盖。[1] 这里的 Persona 是内容角色，不是另一个登录用户；Account 对应平台账号，Series 对应栏目。产品内置的科技研发博主和生活方式博主，各自有文字配置和默认流程。[3]

这种拆法允许两个角色引用同一套模型连接，又分别维护默认写法。它不意味着两条执行链完全隔离，也不证明事实错误会更少。是否写出了合适的文章，仍要看实际产物。

## 品牌约束与角色写法，是两件事

Brand 的身份和品牌约束可以进入创作上下文，但不能成为 Skill、Style、Quality、Recipe 或写作风格默认值的来源。[2] 这些英文在这里分别指方法、风格、质量配置和创作流程。

可以用一个假设理解这条边界：品牌要求内容遵守某项表达边界，两个角色都需要考虑；但技术稿用什么结构、生活稿用什么语气，不应该只因它们属于同一品牌就自动采用同一个默认。

这不是说品牌对表达没有影响，而是把“共同约束”和“角色默认”分开。工程上的收益是配置来源更容易解释；代价是增加了层级，排查稿件不合适时，需要先看配置来自角色、账号还是栏目。这里说的是设计取舍，不是已经测得的效率提升。

## 大纲接受了，不等于正文定稿了

研究、角度与大纲属于中间创作结果，接受它们不会创建 Content Master，也就是作为正式内容真源的主稿。[4] 这给探索留出空间：选定一个角度，仍可以调整大纲；认可大纲，也不等于认可后面生成的正文。

文字候选只有经过明确接受，才会追加保存为 ContentMasterRevision，即主稿的新版本；模型调用本身不会静默改正文。[5] 因而，“调用有响应”和“内容已定稿”是两个不同结果。

我倾向把这个确认点看成一道内容决策边界，而不是质量保证。它让创作者有机会挑选、修改或放弃候选，但也增加了审阅操作。接受后的文字是否准确、是否符合角色，不能由“已保存”三个字代替判断。

## 指定模型，就应该尊重指定

Custom 指定单个精确模型时，该模型不可用必须停止；Custom Composition 只允许在事先声明的有序精确模型链内回退。[7]

例如，明确只选模型 A，就不能把模型 B 的稿件当作 A 的结果交回来。如果提前配置的是 A → B，走 B 才属于执行既定选择。这能解释“本次为什么用了这个模型”，却不能保证请求一定成功，也不能替代对结果的检查。

事实来源也一样。生活方式角色讨论正在发生的事情时，需要新鲜来源，不能拿模型旧知识冒充实时事实。[6] 换成更自然的语气，不会让过时信息变新；没有来源的现实断言，也不能靠写得流畅来成立。

我的判断是，这套设计首先解决“配置属于谁、什么才算定稿”的问题。共用模型连接，可以减少重复配置；分开角色默认，可以避免把一种写法直接当作另一种内容的默认要求。代价是更多配置层级和明确确认。它是否值得，最终还要由两类真实稿件和实际使用体验来检验。

## 项目依据

以下编号只对应本次提供给模型的七条本机项目事实，不是外部新闻或行业研究。

1. Persona 是创作配置根，Account/Series 可明确覆盖；用户负责权限、模型和基础设施。见 [Persona 创作配置规格](../openspec/changes/add-persona-creative-studio/specs/persona-creative-configuration/spec.md)与[设计第 1 节的用户基础设施职责](../openspec/changes/add-persona-creative-studio/design.md#1-owner-is-infrastructure-scope-persona-is-creative-scope)。
2. Brand 可提供约束，但不是方法、风格、质量或流程默认的来源。见 [身份边界规格](../openspec/changes/add-persona-creative-studio/specs/fe-f3b-content-identity/spec.md)。
3. 科技与生活两个 Starter Persona 分别有文字配置和默认流程。见 [设计第 4、14 节](../openspec/changes/add-persona-creative-studio/design.md)。
4. 研究、角度、大纲接受不创建 Master。见 [中间创作 Stage 规格](../openspec/changes/add-persona-creative-studio/specs/creation-recipe-stage-control-loop/spec.md)。
5. 文字候选明确接受后才追加 Master revision，模型不静默定稿。见[主稿追加版本契约](../openspec/specs/production-content-master/spec.md#requirement-contentmasterrevision-is-the-project-production-revision-root)与[候选生成和明确接受契约](../openspec/changes/creation-recipe-stage-control-loop/specs/creation-recipe-stage-control-loop/spec.md#requirement-project-native-master-stages-produce-proposals-not-masters)。
6. 当前事件需要新鲜来源，不以旧模型知识冒充事实。见 [生活角色边界规格](../openspec/changes/add-persona-creative-studio/specs/persona-creative-configuration/spec.md)。
7. Custom 单模型精确钉死；组合回退仅限预声明链。见 [模型路由规格](../openspec/changes/add-persona-creative-studio/specs/model-capability-routing/spec.md)。

稿件来源：既有真实 Gemini 科技稿的 Agent 离线编辑候选，原稿未覆盖。本稿尚未保存成新的 Master、运行新的业务 checks 或生成新的 Candidate/交付包，不代表产品全链路及用户质量验收通过。
