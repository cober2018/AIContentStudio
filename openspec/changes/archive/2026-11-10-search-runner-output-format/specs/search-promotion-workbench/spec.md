## MODIFIED Requirements

### Requirement: Platform model runs the same steps in the background

选平台模型时，平台 SHALL 在后台按顺序执行与第三方模型路径相同的平台功能，MUST NOT 走逐阶段等人挑选、采用的创作流程；人工关卡 MUST 仍只有确认资料和审成稿。用途对应：资料起草用选题与资料（topic_discovery）及已接入网页搜索；问题库用检索（discoverability）；核心稿用写作（generate），事实复核用事实核查（fact_review）；平台版本与按意见重写用平台适配（platform_adaptation）。每一步调模型时 MUST 把要求的输出结构和字段名写进提示词。核心稿检查不过关时 SHALL 带着问题重写，最多 2 轮，仍不过关 MUST 停下并写明原因。每一步 SHALL 记录所用模型、结果与失败原因，失败步骤 SHALL 可单独重试。本期平台模型只做文章；图文、视频作品 SHALL 标为「等第三方模型」，其写作方 MUST 为第三方模型，第三方模型可以直接接手。

#### Scenario: 送审用保存时的检查结果
- **WHEN** 版本保存时检查已通过、内容没再改
- **THEN** 整批送审直接送出，不重新调事实核查模型

#### Scenario: 图文出图失败可重存
- **WHEN** 图文稿用了出图不支持的字重或对齐
- **THEN** 存稿时就被拒并写明哪张哪层；万一采用后出图失败，写稿方可以改好再存一版

#### Scenario: 检查不占写锁
- **WHEN** 平台在跑一篇稿子的检查、正在等事实核查模型
- **THEN** 其他作品照常能存稿、交付，不报「项目上下文正在更新」

#### Scenario: 图文交第三方模型
- **WHEN** 平台模型开的项目选了图文
- **THEN** 图文作品的写作方是第三方模型，第三方模型用 get_article_brief、save_article_draft 直接接手

#### Scenario: 点开始后全自动
- **WHEN** 资料已确认，人在推广对象页点「开始」，选 3 个项目、形式文章、发布平台公众号和知乎
- **THEN** 平台生成或沿用问题库，开 3 个项目，写核心稿、自查、出公众号和知乎版本，整批送到「待审成稿」，中间不等人

#### Scenario: 模型按要求的字段输出
- **WHEN** 平台模型生成问题库
- **THEN** 提示词里写明 questions 每条的 text、intent、priority、source_url 和 keywords 的 primary、long_tail、brand，模型按这些字段输出，平台能读到问题

#### Scenario: 重写两轮仍不过关
- **WHEN** 某个核心稿两轮重写后事实复核仍有阻断问题
- **THEN** 这个项目停在核心稿，项目页写明原因并提供「重试」，其他项目照常继续

#### Scenario: 按意见重写
- **WHEN** 人对平台模型写的知乎版写了意见
- **THEN** 平台按意见重写知乎版、复核后再送审
