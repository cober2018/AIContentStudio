## 2026-10-18 正式前端一致性修正完成（58/66）

已按用户授权统一实拍页面与四段任务书。代码仅修改ProductionWorkspace.tsx、VideoStudioShell.tsx、VideoShotMaterialPanel.tsx的路线/状态展示及上传框布局；无后端门禁修改。

- 六步引导区分实拍/AI/混合；实拍显示“脚本与任务书已确认·可拍摄”和“待拍摄4镜”，后期资料/事实检查独立说明，不冒充已具备成片或发布条件。
- 脚本结构与可后补旁白分开；确认区读取中/读取失败保留真实状态，确认按钮禁用，不伪称草稿。任务书标题去掉固定草稿字样，未保存修改仍显示待保存/确认。
- 当前作品追加Brief38，将旧颜色搭配思路统一到按压、走动、鞋底、两双同框的已批准方向。未知材质/性能/规格和购买入口仍未补造。追加Master56/57，只补入共同手机拍摄说明并保存任务确认；四镜动作、顺序、8/7/7/6秒剪入和12秒原片均不变。当前Master57 v10、脚本/任务已确认可拍，制作配置仍v4。
- 下载读取同一保存主稿；真实点击下载并核对#57 v10、四镜说明和1080p/30fps等要求。Markdown拍摄清单版本头同步，页面/下载/聊天的拍摄要求一致。
- 真页面验收发现原生文件上传控件宽349px导致1440页溢出25px，已对实拍及AI上传框增加容器宽度约束，上传合同不变。

验证：正式本机12页（六步×1440/390px）逐页只读核对，通过旧文案排除、当前内容/字段、无整页横向溢出、零页面错误、零API写检查；两个宽度均真实下载任务书。另7场景使用浏览器GET隔离夹具复核实拍/混合/AI/旧路线/读取失败/读取中/未保存修改，均通过，不写正式数据。最终Web TypeScript/Vite/bundle通过；独立规格/数据及TypeScript审查通过。证据见evidence/capture-workflow-20261018/alignment-*。

备份后通过CLI追加当前作品版本。与本轮备份比较，45条旧Master、31条Brief、137条制作配置、33条素材版本、2个SKU及其版本逐行保留；integrity OK、FK 0。这是相邻已授权测试项目清理后的实际基线，未使用更早全库计数冒称当前保全。无新真实原片/模型调用/成片，未提交、push或归档；原8项仍需对应真实证据。



## 2026-10-18 正式前端内容一致性追加核对

用独立只读浏览器访问Project34/Unit40的导演方案和逐镜素材，零API写、零页面异常。最新Master55脚本/任务均已确认，四段待拍镜头、机位和实拍流程已显示，和发送用户的任务书一致。

仍有展示未统一：逐镜素材页顶部固定旧AI图生视频引导；当前Brief的核心购买理由/使用场景仍为先前颜色搭配草案，未与新实拍主稿全面同步；统一资料提示与拍摄确认分属不同阶段，但未清楚区分“可拍”与后期准备缺口。上轮58/66只代表当时工程验收记录，不足以声称页面整体内容完全一致。已重新打开10.4和10.8的整页一致性验收，当前56/66；四段拍摄任务本身有效，不要求用户重确认。证据live-frontend-consistency.json。

## 2026-10-18 实拍流程与Skills工程收尾

第10节非素材工程收尾完成，当前58/66；原8项真实参考/素材/成片/用户验收及最终归档仍保留。实际Git为main@8539806加相邻未提交改动，没有提交、push或归档。

- 产品固化：购买理由→脚本结构确认→任务书确认→逐镜原片/审阅/选段→后期交接→成片反馈。无旁白可确认可拍；任务书有手机清单与下载、拍摄/成片排序，混合路线区分实拍与AI。
- 方法固化：平台自编studio.video.product-filming@1负责购买理由到动作、机位、重点、证据和补拍判断；Harness的product-video-material-director负责实际素材审阅，video-production-handoff承接平台CLI/MCP、冻结包及Resolve/AE。按阶段选择与冻结，不改变其他作品/角色/SKU默认。
- 已修复声音后置误要求重拍、通用/use绕过SKU限制、任务改版旧原片无法复核、旧网页回片误计入，以及恢复旧任务时新pending遮蔽有效历史审阅。旧原片/方法/确认记录保留。
- AI辅助：隔离真实模型完成任务书10字段补齐、指定动作反馈修改及选区润色。四次请求中一次润色失败，明确重试后成功，保留失败记录。回执为openai_compatible / gemini-3.8-flash-high / configuration_revision13，不推断网关上游。无正式验收样本写入。
- 反馈仍需明确范围、保存候选、验证和精确版本引用；SKU/品类/风格/项目/当前作品分开。SKU限制覆盖表单与通用/use/MCP共用服务。偏好不是自动升级的阶段Skill，历史作品和默认不随之改写。

验证：本轮最终163项视频/执行/能力既有检查通过（59条既有依赖弃用警告）；另69项能力检查、33项拍摄配置/后期隔离检查、14项同原片按新任务审阅API链通过，存在覆盖重叠不累加。UI 12组原回归、12组首次返修、15组当前hash返修通过，最终Web TypeScript/Vite/bundle通过。Python/TypeScript及代码独立复核、OpenSpec strict和diff检查完成。证据统一在evidence/capture-workflow-20261018/final-*。

后期包验收使用ffmpeg合成工程视频，经实际上传探测、合法隔离SKU/Brief/FactPack、采用/prepare/claim/媒体取回及manifest选段检查。Resolve/AE工程回执是显式夹具，未运行真实拖鞋剪辑，不能称成片质量通过。

本机API重新加载，ready=true；SQLite integrity OK、FK 0。仅为当前拖鞋作品追加制作配置v4（DB143）、Brief37及Master52–55；Master55 v8脚本和任务均confirmed、ready_to_shoot=true。脚本方向为用户明确批准，具体任务书是Agent按既有全权授权审核，不冒充用户逐字段审阅。旧51条Master、142条配置、36条Brief、68条素材和3个SKU/版本逐行不变。

当前只需用户拍摄[四段原片](slippers-filming-taskbook.md)：按压、走动、鞋底、棕灰两双同框，每段约12秒、动作前后留余量、无需现场旁白。尺码/价格/链接按用户决定暂缓；公开挂车前再核对。人物口型同步仍按授权延后，不挡本条旁白版。

# 复核

## 2026-10-18 实拍主链工程接入（未完成整体样片验收）

第10节已获用户确认。新增可选capture_plan/filming/capture_takes，精确脚本/任务书确认，逐镜多原片与毫秒选段，未审阅原片不自动采用；脚本/任务改变显示需复核。旁白可以为空。自编product-filming@1经既有阶段方法冻结和独立开关，不改变旧默认。

证据在 evidence/capture-workflow-20261018/：360项相关既有检查、18项既有反馈检查、Web TypeScript/Vite/bundle、strict及隔离API链通过。隔离工程视频经过真实上传探测和项目引用API，走到确认→待审→可用→采用→时间线；越界片段409，路线切换保留历史回片且不允许在AI路线改写回片。方法启用/关闭/阶段关与10拍摄字段探针通过。未为此调用模型，反馈只复跑既有检查，不宣称新增真实模型反馈质量已验。

独立审查修复：新增实拍镜头错误回退网页；混合任务书缺少来源/景别；审阅片段外素材被剪入；通用director包绕过确认；视频轨短于音轨时误用总时长；切换路线无法保留旧回片；上传中途切账号继续写；AI路线已有素材误被实拍筛选。共享导演包门禁探针仅模拟无关FactPack/readiness前置，实际capture门禁执行，不能代替商品完整后期验收。

本机API已加载，ready=true；390px页面脚本/确认/下载和40拍摄字段可见、无整页横向溢出。通过CLI追加儿童拖鞋Master50 v3实拍草稿，脚本/任务均draft、ready_to_shoot=false；旧49主稿、68素材版本、40单元、36 Brief和3 SKU保全。没有新增真实视频、配音、公开权利、发布或销量结论。服务启动前SQLite备份保留在backups/capture-enable-20261018/（私有、不入Git）。

尚待：本条脚本/任务书明确审阅，原片上传与实际可剪质量、完整Resolve/AE成片；第10节AI实际内容质量、反馈版本提升及六步完整用户链仍不以本轮工程检查替代。只勾选10.1/10.3/10.5，当前53/66，未归档、未提交、未push。


## 2026-10-18 第10节部分实现复核中
独立审查发现并已修：空稿选实拍后新增镜头默认网页、混合清单不区分来源及缺景别。确认校验和AI字段基础已复核，完整回传及实际API/页面尚未验收，不能宣布第10节完成。

## 2026-10-18 第10节方案自检（文档，不是实现验收）
已对照用户最新要求检查：产品承接状态/版本/记录，Skills承接输入/判断/输出/返工；脚本结构与完整旁白分开；实拍不要求AI关键帧；稳定镜头ID贯穿任务书/多条原片/选段/补拍/后期；原事实与生成情境分开；方法独立开关/作用域/新版本不回写旧作品。新范围在同一提案设计和两spec中，8项均未勾，旧8项未完保留。OpenSpec strict通过。业务schema、迁移必要性及实际接口在10.1待核验，不能把文档合同说成当前平台能力。本轮没有运行代码验收或新视频制作；等待用户确认具体新增方案后实施。

## 已完成检查
- 方案独立只读复核：无固定镜头数、无素材齐全率、可选方法关闭仍有效，历史冻结包不改。
- 方法行为场景A：仅合照且要求先选图；应先规划/补素材/候选审阅，不提前生成视频。
- 方法行为场景B：明确单图动态海报且关闭可选方法；按有限目标制作，不强制五镜或补拍。
- 四项候选方法已同步v3/嵌入正文/SHA256，其余14项方法保持原样；已有Skill快速校验通过。

## 实际图片检查及修订
独立复核查看原图和S01–S05。S01 v1与S02同方向整品构图，信息增量偏弱，已生成S01 v2扩大环境比例；再次实际看图确认分工改善。旧v1保留。

S02整品轮廓/蓝色和黑色底部可辨，精确比例未获商品方确认。S03放大生成褶皱/光泽，原图不能核实工艺，只作外观构图。S04未见明显肢体穿帮，但接触/承托和尺度为演绎，不证明舒适/承重。S05多色与原图有对应，精确色号和库存未知。

## 新增页面方案复核
七项检查、五类表达、可选少量版本及约30秒均保留合理适用范围。发现E01真实素材分支原方案未明确，已补“中栏拍摄/核验说明，右栏直接引用真实资料/上传实拍”，跳过AI选图/提示词要求。修正分镜尾部“未安排尺寸镜头”与E01占位的矛盾，统一为待真实资料。

## 前期结论（历史）
可展示候选和页面方案供用户确认；**不是图片已批准、商品性能已证实、页面已上线或完整广告通过**。真实尺寸资料、购买入口、商家依据和成本仍缺失。业务代码/正式资源未修改，change保持进行中。

## 页面实现复核（2026-10-16）
三项独立复核：代码/规格、TypeScript、Python。两项发现均已修复再验：换候选图或保存新Master时，禁止使用不匹配的旧冻结包；非法售价不能参加内部估算。权限、历史冻结、成本隔离、上传与接受分离、真实资料分支及Resolve/AE接续通过。280项既有检查和Web构建通过。

正式服务重载，Brief/costs/readiness回读200，实际桌面三列与390px逐行纵排截图已查看。仅只读渲染，不声明浏览器提交E2E；持久操作由隔离API探针验证。页面实现可用；图片未批准，方法v3仍仓库候选，尚非完整广告交付，因此不归档整个change。

## 本轮方案自检（非新增代码或成片验收）
事实发现：新创意与正式任务分离；三镜旧Master未更新；候选图未入项目；字段补齐不能创建镜头结构，但整稿Recipe候选路径已存在，应复用。入口易用性和保存恢复的完整交互尚待验证，不提前列为已复现代码缺陷。
覆盖映射：连贯操作→6.1/6.2；正式草稿与图片质量→6.3/3.3；动态图像条件和人工回传→6.4；声音/主剪/包装/回收→6.5；方法复用→6.6；规范归档→5.1。
范围复核：不要求固定镜头数、素材齐全率或强制配乐；缺商业资料不阻止局部场景样片，但不宣称完整广告。现有归档不重开，历史接受不覆盖，本版待用户确认后实施。

## 本轮实施复核与边界
独立只读代码复核覆盖ProductionWorkspace、VideoStudioShell和CreationRecipePanel三文件。修复最终details未展开、升级模式无目标锚点及多编辑器固定ID问题后通过；3项blocked说明只改展示。Web构建和132项原有检查通过。
真实模型Run18到Master43修改后采用通过；随后商品Brief更新，显式保存匹配新上下文的Master44。原图43/原样片50与旧Master41保留。导入候选54–58未选、权利未改、新视频0。
此结论不包含空白新项目真实模型E2E、候选完整生成provenance授权、逐镜用户选图、动态素材和成片质量。当前允许用户审阅静态候选，不宣称全部生产可用性已完成。

## 新增精确选图与人工生成包
用户已明确批准S01–S05。每张已选副本hash等于原manifest，经实际像素查看再写提示词；Master45/任务3–7/包6–10回读通过，公开/商业使用false。源AI文件的生成溯源保存在本目录manifest；平台素材来源诚实为upload，不声称平台图像provider生成。
隔离零脚本/零镜头真实模型起草通过，不再将此项列为缺验。人工网页原片仍0，没有新成片；维持动态/配音/最终质量待验。


## 2026-10-17 修订方案复核（文档自检，非代码／用户操作验收）
范围映射：双入口→7.1/7.2；单步骤层级→7.3；草稿和旧链接→7.4；角色多形态→7.5；商品逐镜/声音/剪辑→7.6/7.7；AI及反馈→7.8；Skills和连续动作→7.9/7.10；验证/正常使用→7.11/7.12。
核对并在方案中明确：音频沿用文字派生，不虚构audio类型；商品关联不能按所有视频判断；混合项目不复制；既有商品创建的Persona要求保留；实拍不用AI选图；换步骤保留编辑；跨接受/保存部分失败不伪装成功；旧S01–S05批准仅针对原字节；当前新风格不覆盖旧冻结包；方法关闭不跳过底层事实/权限合同。
验证：OpenSpec strict通过；proposal/design/specs/tasks均已形成（CLI isComplete仅指方案制品齐备）；任务16/32，新增12项全部未勾选；文档存在、内部链接、Requirement场景检查通过；限定路径git diff --check通过。本change未追踪文档另以直接读取检查，不把git未报错当全部文件内容验收。
限制：本轮未运行业务测试/构建，未审阅新的参考卖货视频，未改代码/方法正文或正式数据；未进行独立代码评审或用户点击验收。方案可交用户确认，不能称新版工作台已实现。按用户本轮要求等待方案确认后才实施。

Renoise参考审查：确认其为Skills/远程服务适配及局部批注UI，并非完整商品工作台。源码流程可借鉴不等于出片质量已验证；声明Apache-2.0不等于外部网站品牌/素材自动获同许可；保留人工网页、声音与工具边界。生成实测证据和强制UGC口播规则不直接采用。

## 多类型作品补充复核（2026-10-17，文档）
已移除人物口型同步的范围排除；类型/创作方式/声音可组合，同商品作品级隔离与共享事实明确。人物台词先规划、生成原声后保留审查，旁白为并列选择；能力不足不悄悄降级。情境演示形式允许，实际证明依据单独记录。参考二创可拆镜重建，不强制支持视频参考输入。原冻结包不变。
OpenSpec strict通过，任务16/36（20未完成，其中新增16）；文档内部链接检查通过。仅方案/文档变更，未新增代码、持久测试或业务操作；新同步路线仍需真实样本才能验收。

ViMax只读复核：已区分上游源码有实现与模型产出未运行；镜头首尾结构不代表所有网站支持双帧；候选相对最佳不等于商品合格；对白描述不代表口型同步已验收。Web界面来源为仓库静态截图与代码，无实际交互验收。无业务变更。


## 2026-10-17 整合方案复核（当前，文档自检）
覆盖检查：六步次序在proposal/design/页面/spec保持一致；角色五步和文字派生音频保留。商品类型、原创/二创、声音模式为可组合维度。页面保留三列、单步骤主视图及按需抽屉，不新增复杂白板或全自动调度引擎。

已校正：声音规划前置但不强制人物先TTS；原商品依据不能被AI参考取代；允许独立场景及候选全部不合格；不默认增加生成数量；目标尾帧不伪称模型输入；返片问题按参考、关键帧或运动/对白分别退回，剪辑问题不要求全部重生成。外部原则由本地独立编写为有输入/输出/检查/返工的阶段方法，旧来源不洗成原创。

范围映射：7.17方法合同、7.18视觉声音定样、7.19精确引用和依赖、7.20候选比较；连同7.1–7.16承接全部页面与路线要求。原16完成项不变，总计16/40，新增20待批准。OpenSpec strict通过；最终文档完整性核验见同日progress追加结果。

本轮未运行产品构建、业务测试或新素材生成；未进行独立代码评审或真实用户交互验收。结论仅为方案可交用户确认，不代表这些功能上线或视频质量通过。

2026-10-17交互原型自检：JavaScript语法通过；实际浏览器检查双工作台、步骤、镜头、方法面板及原型内草稿保留，390px不溢出，未捕获脚本错误；已查看桌面截图。此为设计原型，商品图/视频为明确占位，不是素材生成或业务验收。

2026-10-17 Canva候选首屏复核：双入口文字存在，但使用笔记本透视包装及黑橙色，并非要求的浅色平视可编辑界面。其余7页尚未完整核对、元素编辑性未验证；不报告全稿通过。保留原交互原型作为布局讨论依据。


## 2026-10-17 Canva与原始架构蓝图对照
依据：根目录NorthStar_V2（2026-09-26）§0/75/78、Frontend_Product_Contract_V1（2026-09-27）§1/2、当前design及guided规范；Canva DAHYOfjkHs8的1–8页可访问文字逐页读取。此次不是代码运行验收，也未修改Canva。
结论：生产主题大体对应，不能认为完整功能/流程/架构一致，不能直接按Canva实施。
- 页面2–7导航混用“定位与目标/商品与本条目标/创意与脚本/素材与资源/审核与发布”，与本版六步不一致。页5镜头摘要变为建立/触摸/反应/展示，与页3动作链不一致。
- 页5三列、人工网页/精确选图/原片回传基本体现；页4定样、页6声音→节奏→调色和AE可选、页7范围反馈、页8文字派生音频/字段补齐基本体现。
- 页5新增“系统提示词”和英文提示词两个输入；公开网页执行未证实有独立system-role输入。应回到单个可用动态提示词及真实参数，不把画出来的字段当能力。
- 页8“音频内容将依据已接受的文字自动生成”缺少明确执行触发与接受步骤；不能理解为文字接受即付费生成。
- 原蓝图ContentProject为业务根，双台应为同一项目/单元的生产视图。当前设计写共用实体但将项目叫档案、主原型缺项目矩阵返回，易误解项目降级；需明确项目上下文和跨形态作品关系，不是必将矩阵铺回主画布。
- 原蓝图Skill非核心依赖，现阶段方法应是可选可版本的指令/策略，由Workflow调用可替换模型工具，不能把角色等同Skill集合。用户后续要求阶段开关可与此兼容，不以关方法关闭确定性规则。
- 原前端契约包含完整Workflow Run、节点输入/输出和局部重跑/调整。分步视图可简化默认页，但当前稿缺明确高级工作流入口；不把“创作方法”开关当完整Workflow替代。
- 原蓝图Candidate整包审批、发布授权和效果学习独立。商品六步只覆盖生产，应明确成片→渠道适配/Candidate→内容审批→目标账号发布授权→回执/效果学习的入口衔接，不新增另一发布系统，也不强制全部展示在生产页。
- 内容身份是一等上下文，不仅角色音色；应保留其定位/观点/事实边界/版本。图文视频平级，音频为现阶段派生路径。
上述为设计缺口与歧义，不推断底层已删除能力；新增/调整实现范围仍以用户确认后的同一规范为准。


## 2026-10-17 可操作原型静态复核
范围为对话内content-workbench-canvas.html及同一设计规范，不是产品代码或正式平台验收。原架构四项修订已落入规范与原任务：项目上下文、身份/方法分离、高级工作流、完整Candidate/账号授权/回执/学习衔接。
独立只读审阅两轮：首次发现草稿与确认状态不同步恢复、提示词失焦重绘可能吞掉切镜点击、方案/定样修改后仍显示确认；已分别改为schema3完整状态快照、局部刷新、相关阶段待重新确认。第二轮确认前两项修复，补充“所有镜头已采用时，修改定样后继续仍跳剪辑”的边界；已将镜头待办判断放在定样已确认分支，本轮自查修复。
验证：原型JS语法通过；36872字节，无fetch/XHR/WebSocket调用；OpenSpec strict通过；工程任务实际16/40。未新增测试文件，未运行业务测试或构建。原浏览器检查只适用于旧版；此前本地file URL预览被浏览器安全策略拒绝，本轮未绕过或再次进行浏览器检查，因此新版桌面/窄屏渲染和真实操作仍待用户在对话原型中评审。静态通过不等于完整交互验收。
结论：可交用户试用设计，不能宣称正式功能上线或素材质量通过。Canva未修改，停止作为实施依据。

## 2026-10-17 SKU原型静态复核
新增功能仅在同一交互原型：商品库、SKU四区、方案选择、独立模拟草稿、草稿参考和方案另存。规范明确跨项目复用的SKU资料/方案、独立角色配置和作品精确版本；追加3项未实施任务，当前16/43。
独立只读审阅发现另存声音忽略定样声音/配乐，以及持久化超限或失败只提示隐藏工作区。已修复为优先保存定样声音并映射新作品讲话方式、同步SKU可见状态提示。正常路径未发现商品/角色切换覆盖和作品草稿串联；修复后语法自查通过。
原型留存的是标注缺真实成片/工程的示意草稿参考；新方案仅保存所选创意设置，事实和授权不提升为默认。完整媒体持久存储与默认版本管理仍待正式实现。OpenSpec strict和JS语法通过，无新版浏览器运行或产品上线验收。


## 2026-10-17 商品选择优先的入口修订
本轮入口修订按用户明确说明执行；新建表单只要求名称与品类，编码可自动生成，未知规格不补造。当前原型不上传图片，不声称已获得未提供技术参数；新草稿进入视频制作目标页，后续真实生成仍不执行。

独立静态复核确认新建提交后直接进入新SKU视频制作目标页，重复编码/自动编号和资料隔离路径无阻断；发现面包屑残留沙发名称，已改为当前商品名称。JS语法与OpenSpec strict通过，未新增浏览器运行验收。

## 2026-10-17 SKU流水号与右侧图片静态复核
独立只读审阅未发现本轮阻断问题：编号避重、提交递增、schema6恢复上界、schema5兼容旧条目与示例别名；图片数据不进入widgetState；各SKU分别展示绑定图片，无图不借用其他款。窄屏左列可收缩并断行，右图100px、主按钮跨列，静态未见明显溢出。
原型JS语法、OpenSpec strict通过。正式服务端原子分配、上传/指定主图、加载失败重试属于7.21实施验收；原型不代表这些接口已落地。本轮未浏览器验收，未生成测试代码，未改正式业务代码。

## 2026-10-17 新作品六步原型静态复核
只读审阅覆盖新作品主路径、post/feedback作品隔离、方案声音/风格和旧状态恢复。发现并修复：待审且已勾选原片在上游修改后未取消勾选；当前画面风格未被另存；旧配乐显示与交接不一致；镜头抽屉跨步骤读写错误键。前三项经独立复核确认，抽屉问题以advance/sc-prev清drawer修复并自查。
本轮无浏览器操作验收，不将静态审阅视作渲染/交互通过。原型所有生成、素材、后期、接受均明确模拟；正式服务端与真实素材验收仍待实施，工程任务16/43。

最终修复后node --check exit0；OpenSpec strict valid。全部四镜均可作为反馈目标，前进/后退均关闭镜头抽屉。原型158KB量级，未嵌入任何新媒体或调用网络。

## 正式首版复核（2026-10-17）
独立Python与TypeScript审阅覆盖SKU权限/版本/幂等、工作级配置进请求、阶段manifest以及草稿常驻/折叠层级。发现的保存方案回退旧身份、profile内stage被旧manifest覆盖、重复AI浮窗、无法收起高级区、错误商品受众均修复复核通过。275+53既有检查通过，最终Web构建/bundle、Ruff F与strict通过。既有migration测试3失败在原main基线同样复现，实际新迁移及复制库fresh upgrade通过，不能写为全量绿。
正式使用CLI/API创建测试SKU/新草稿并查搜索图片；浏览器仅只读核对入口、目标、方案、定样、旧逐镜面板、后期、成片反馈；未点击平台或人工网站生成。服务重载窗口曾出现一次页面500提示，相关API随后200/刷新正常，未以此改写业务记录。未完成完整键盘/异常交互与新片质量，7.11仍开放。旧14units/45masters/10packages/63materials/14identity/95LLM/9provider行逐行保全。
结论：六步产品首版接入通过；全change仍25/43，继续实施剩余工程与创作验收，不归档。

## 2026-10-17 连续性/方法/参考入口复核
本轮继续完成7.9/7.15/7.17/7.19/7.23，当前30/43。可选镜头构图依赖记录前置镜头和精确图/hash，拒绝缺镜/自引/循环；只提示受影响镜头、不改历史。实际尾帧路线未验证，明确不支持伪尾帧选项。三个独立自写方法v4经压力场景审阅、正文/hash校验与真实stage preview确认；完整卡在能力上下文重复时触及原体积限制，改为精简运行指令（保留来源卡hash），未放宽门禁。正式artifact15/16/17最新修订42/43/44，仅新草稿工作级选择，旧修订/默认/冻结包保留。新参考作品href携带master，历史精确选版只读、非法不fallback。连续性相关150既有检查复跑通过，实际链/陈旧hash/原包结构/参考hash拒绝验证通过，前端构建与独立复核通过。代码/方法共33路径，无新测试代码、模型调用或push。完整交互、AI助手扩面及新样片等未勾项继续，不归档。

## 2026-10-17 最终工程更新：34/43
37路径已选择性接入。7.7/7.8/7.16/7.18按工程证据完成；最终Web构建通过，既有328项通过，最新177项复跑通过（重叠）。实际Run19保留初稿拒绝、镜头输出失败及明确重跑，保存Master46，策划四镜/30秒；6次模型调用含旁白建议，不代表新媒体或最终质量通过。Session1生成/采用不自动保存，单独保存revision4回读一致；同SKU同方案作品对照独立。
部分阶段manifest不含finish时曾造成整稿提交后响应失败，已修复并原幂等键恢复200，无重复Master。新项目事实边界缺失继续正确阻断准备；未用旧项目证据清门禁。旧行保全/integrity/FK/ready通过，原3项迁移测试失败与基线一致。
余9项真实媒体/成片/同步、参考片分析和完整交互/用户反馈仍待；不归档、不提交。

## 2026-10-17 不依赖新素材的剩余验收：35/43
24页/两宽度只读检查无横向溢出、无脚本异常；432次Tab观察和键盘步骤切换通过，浏览器零写请求。商品库与镜头任务读取失败可区分空态并恢复，旧/非法精确版本不混用。既有相关138项检查通过（与前轮重叠）；隔离候选全部拒绝/单项返工保留历史且零自动采用通过，真实新素材质量仍待。
修复新商品默认选xiaohongshu图文造成后续视频门禁：新作品允许无渠道、前端只列实际视频渠道，服务拒绝新建不支持视频的目标；历史明确/省略渠道幂等恢复与明确null冲突验收通过。独立代码复核与Web构建通过；四文件选择性接入，数据库/文件已备份。Unit15通过API清空渠道，相同策划保存Master47/v2，Master46/Run19历史保留；缺事实边界仍阻断，未新增模型或媒体。
使用步骤及一次性材料清单已补齐。7.11完成；7.12使用说明已完成但新工作台的用户使用反馈仍待，不替用户签收。7.20机制已验，真实新候选效果仍待；余8项保持开放，不归档/提交/push。

## 2026-10-17 商品独立性审计：当前未通过，修订方案待确认
范围为当前main@8539806加工作区实现；仅只读代码/正式库，不复跑模型或写业务数据。已有页面和工程检查不代表商品不依赖角色。

| 位置/证据 | 已确认问题与影响 | 修订方向 |
|---|---|---|
| ProductWorkbench.tsx:30–75；product_skus.py WorkIn/create_work | 获取Persona/角色默认video工作流，创建要求persona_id | 以SKU启动，不取角色列表，不用隐藏占位角色 |
| models.py ContentUnit；product_creation.py服务:68–190 | persona_id必需、创建identity快照、要求persona_default及persona.N.video | 单元业务域与条件身份约束，独立商品上下文/默认流程 |
| creation_recipes.py；creative_configuration.py frozen_stage；stage_resolver.py:29–56 | 默认与profile从身份取，过滤creative_profile后仍带身份定位等 | 商品解析器与请求上下文独立，执行器共用 |
| form_assistance.py:282–308；creative_packages.py:284–410/461–467 | AI助手/包仍读取identity视频profile与非创作身份属性 | 助手、媒体和后期包统一读取商品快照 |
| ProductionContextHeader.tsx；ProductionWorkspace.tsx；useProductionWorkflow.ts | 商品页显示角色身份链、声音链接到角色配置并加载身份 | 商品资料/方案页头与独立声音入口 |
| product_skus.py:395–420 save_plan | 缺配置组回退IdentitySnapshot，可把角色默认存为SKU方案 | 仅提取商品有效配置，保存所选组及来源版本 |
| content_masters.py:106–131及run适配 | identity_missing和run身份匹配阻断无角色作品 | 按域检查商品资料/配置/事实边界，角色门禁保留 |
| product_skus.py workspace_rows；capability_memory.py | 项目product_context推断归属；方法记忆仍有角色层级 | 单元级显式域；商品方法/反馈明确作品/SKU/品类/风格范围 |
| models.py ContentAccount；delivery.py:174–190 | 账号必须Persona，交付比较account.persona_id与unit.persona_id | 补账号独立所有权和商品授权；不直接删除安全检查 |

正式库只读证据：SKU1 → Unit15 → Persona2 / IdentitySnapshot15 / Workflow18；Workflow18 scope=persona_default、key=persona.2.video。快照含positioning、target_audience、expression_style、audio_creative_profile、video_creative_profile等键，确认角色上下文已进入商品任务。当前1个SKU、0个SKU方案、4条制作配置修订、15个内容单元、101条LLM运行。方案留存串入角色配置是已发现的代码路径风险，不声称已有被污染的SKU方案。

结论：不是仅前端名称问题。第8节8项新增修订均未实现；历史35项工程证据保留，不能据此归档。迁移不得改写旧Master46/47、Run19和身份快照；真实素材、成片质量待验边界仍保留。本轮仅方案文档变化，无代码修复完成声明。

方案校验：`openspec validate improve-product-keyframe-preproduction --strict`通过。仅文档调整，本轮未运行代码测试；旧测试结果不充当新架构验收。

## 2026-10-17 第8节最终复核
结论：商品独立业务域工程范围通过，真实新片质量未验收。独立Python、TypeScript及规范复核接受；已修复审核清单身份依赖、角色计数、当前音色保存后旧媒体表单缓存、事件注册、实际商品prompt超界，以及方法归档后历史读取。最终修复126既有检查+10临时断言；提示词342既有检查；正式集成后候选/交付/概览171既有检查通过，Web构建通过，数目重叠不相加。
零角色17断言mock链通过，真实复制库和正式API preview ready；正式106旧表指纹一致、关键历史逐行不变、integrity/FK通过。12页桌面/窄屏只读验收零Persona请求、零写请求、零页面异常。Unit15工作流切换明确记录，历史18/19/46/47保留。无新模型或媒体生成；原素材与新成片质量剩余8任务继续。证据evidence/product-domain-20261017，代码58文件清单同目录。

服务恢复后再次核对旧行：除Unit15工作流pin及updated_at外，仅既有后台发现任务正常推进heartbeat/catchup_clock和source54/55游标时间；未回退后台工作。关键主稿/运行/身份/模型/媒体历史仍逐行一致。见final-preservation.json。

## 2026-10-17 第9节方案待确认
方案自检覆盖两项分工、补齐/润色、独立开关及必要unit/空意图接线；复用路由/冻结/保存，无新增表或自动多Agent。源诊断与字段代写区分，来源受限材料不复制。新功能尚未实施/验收，原工程结果不充作本节通过。

## 2026-10-17 第9节实施自检（待独立复核）
范围：9.1–9.7。基线 main@8539806 + 相邻未提交改动；本批新增文件 6（studio_skills 两包）+ 修改 4（studio_creative_catalog.py、services/form_assistance.py、routers/form_assistance.py、前端三组件 + ProductionWorkspace 传参，共5处前端文件）；无路由外后端结构改动、无数据库/正式数据/模型配置改动（隔离 SKU-000002 与 Project11/12 为探针新建样本）。
- 后端：路由声明顺序正确（/product-methods 在 /{session_id} 前）；product_goal_methods 只读且经既有 access 归属校验；run_attempt 的 unlock 仅 product_brief+商品域+空值+白名单字段。
- 前端：方法开关状态与请求注入经既有 productionStages prop（methodIdentity 自动纳入漂移比较）；保存 GET 回读全量再 PUT，规避 ProductionSettings extra=forbid 默认覆盖；persona/项目级 ProjectBriefTab 路径未动。
- 检查：compileall、442 项既有检查（product_settings/creation_recipe_stages/persona_creative_studio/persona_creative_identity）、tsc+build、openspec strict 全过；27/27 隔离探针（真实冻结链+假 provider 捕获实际 user_prompt）；1440/390 页面只读零写请求。
- 真实模型：autofill 建议质量通过；polish 保留原意但存在**尾部重复缺陷，对照组证明为既有 field_polish 选区管线问题，与本批无关**——列为已知问题，不在本批修复范围。
- 边界：未归档、未提交、未push；正式沙发 Project8/Unit14、既有 Project9/Unit15 只读未写；原8项素材验收未完成，不因本批勾选。

## 2026-10-17 第9节严格审计与修复复核
用户指令对本批做完整严格审计。审计以 handoff-goal-methods-20261017.md、design 第9节、spec 行246–269、tasks 9.1–9.7 为基准逐条对照当前代码，并复跑全部门禁（442/27探针/compileall/build/strict 均绿）。
发现三处问题（详见 README"第9节严格审计与修复"）：B1 阻断——前端新建方法条目 id 含 @（校验模式不允许），首次启用后保存 422、AI 请求 500，主流程不可用；探针全用后端构造合法 id＋页面检查只读，故此前未暴露。B2 中等级——组开关本地关闭（不保存）时请求不带 stages，已存方法经 project_snapshot.production_methods 背景进入指令，与 spec"全关无隐藏回退"不符。S1 次要——焦点字段适用卡高亮未实现。
同轮修复并验证：id 回退去版本 ref；generate() 非法条目可读 422；组关但已配置时显式传两项 disabled（manifest 记录状态、user_prompt 无指令残留）；字段 onFocus 高亮适用卡。修复探针 10/10（含 @ 护栏与旧作品不变对照）、Playwright 全新作品端到端 10/10（保存 PUT200、真实补齐 POST200、高亮断言、零控制台错误）、门禁复跑全绿。证据 evidence/goal-methods-20261017/{fix-probes.txt,fix-e2e.txt}。
已知问题不变：polish 尾部重复为既有管线缺陷（对照归因，非本批引入）；非 UI 客户端省略 stages 时作品级方法仍走既有背景继承路径（记录为现状，超出第9节最小范围）。结论：阻断与规范差距已收口，待主Agent独立复验。


## 2026-10-17 主Agent独立验收：未通过，退回修复

本结论取代前述“严格审计已收口”的当前状态；保留开发自检历史。主Agent重新执行真实代码探针、442项既有检查、Web构建和OpenSpec strict。检查与构建通过，但以下五项阻止第9节验收。未修改业务代码或正式数据，未提交、push、归档。

### R1 关闭后仍残留完整指令（必须修复）
- 位置：apps/api/app/services/form_assistance.py:510–514、628–631；product_context.py:78–89。
- 复现：在内存库保存两项开启的作品配置，再明确传两项disabled发起请求。configured_methods虽为[]，实际user_prompt仍包含完整SKILL指令，路径为/project_snapshot/product_context/creative_profiles/product_production_methods/video/stages/0/methods/{0,1}/instruction。
- 原因：只pop顶层production_methods/selected_production_stages，未处理商品上下文内另一个冻结副本；并非仅非UI省略stages才出现。
- 修复要求：实际模型渲染以本次有效选择为准；清理所有重复执行指令，保留历史审计快照和事实。不能靠模型自行忽略或只检查configured_methods为空。
- 复验：先保存开启，再临时全关/单关/阶段总关，递归检查完整实际请求无被禁用方法正文；检查默认继承和历史可读。不要仅在“从未保存方法”的空作品上验收。

### R2 方法没有按目标字段过滤（必须修复）
- 位置：form_assistance.py:217–248、630。
- 复现：targets=['objective']且两方法开启，configured_methods同时包含audience-need和purchase-reason。applicable_fields仅随指令发送，未用于筛选；嵌套副本也须核对。
- 修复要求：在明确本批eligible targets后筛选本次适用方法，区别记录完整配置和实际执行投影；每次润色/反馈重写重新按本次目标匹配。不得全局删掉其他生产场景的方法。
- 复验：objective只带购买理由方法，primary_audience只带受众方法；混合目标按适用并集；单关/全关及反馈重写分别核对实际请求。

### R3 整组关闭不能保存（必须修复）
- 位置：GuidedProductionGoal.tsx:157。
- 复现：用实际组件转译后运行，已配置的方法组关闭时保存按钮disabled=true。虽然mergedStages含disabled条目，用户无法保存；重新载入仍读取旧开关。
- 修复要求：允许保存已配置方法的关闭选择，保存与重新载入显示一致；方法修改须进入适当的草稿/离开提醒，避免静默丢弃。
- 复验：首次启用保存→关闭整组→保存→重新读取；切换步骤/离开时草稿行为符合现有设计。

### R4 方法保存覆盖其他入口的新阶段配置（必须修复）
- 位置：GuidedProductionGoal.tsx:99–122。
- 复现：页面旧effective_stages的review.enabled=true；保存前模拟另一入口把review关闭并追加product-script方法。组件GET取得最新revision=9，但PUT把页面旧mergedStages整体写回：review变回true，新方法被删除；其他顶层voice_id保留不能证明阶段配置保全。
- 原因：仅顶层settings合并，production_stages来自旧页面；使用最新revision使已有版本保护无法识别这次覆盖。
- 修复要求：在最新有效配置上只合并这两项明确修改，或按页面原基线拒绝冲突并保留草稿。不得把所有阶段旧快照当成两项开关补丁写回。
- 复验：另一入口更新其他阶段/方法后，本页保存两开关，应保留那些更新或清晰409；验证同方法冲突及保存过程中再次变更。

### R5 选区润色尾句重复尚未通过质量验收（本批交付阻碍，旧缺陷）
- 位置：form_assistance.py:606–631、686–692；开发证据real-model-samples.md第2节。
- 开发方真实样本已证明开启和关闭方法均重复。主Agent用该输出形状在内存库重放：模型返回整字段建议后服务再次拼接suffix，得到“办公室下午随手鲜榨，不用洗复杂零件，不用洗复杂零件”。本轮没有重新调用真实模型，不据此宣称所有模型必然如此。
- 这是既有选区输出合同问题，并非指控本批新增；但第9节明确承诺定点/选区润色且需要真实质量验收，不能以旧问题为由勾选质量通过。
- 修复要求：明确选区模式返回替换片段的合同及边界，保留未选文字；不要通过全句通用去重破坏用户原文。复验整字段、开头/中间/结尾选区及Unicode偏移，补真实模型样本。

### 本轮验证与边界
- 既有四文件检查：442 passed，8 warnings，17.01秒；Web完整构建退出0；OpenSpec strict、git diff --check通过。
- 开发修复探针10/10本轮复跑仍通过，说明其覆盖不足；独立探针覆盖“先持久开启再临时关闭”后明确发现R1。
- independent-backend.txt：实际请求深层指令位置、目标字段错配、选区输出形状重放。
- independent-component.txt：实际TSX转译执行的按钮状态与保存payload，React hooks/API为隔离替身；这不是浏览器端到端验收。
- independent-tests.txt、independent-build.txt、independent-scope.json：命令、结果和源文件hash。
- 临时脚本保存在/tmp/goal-methods-independent-backend.py、/tmp/goal-methods-independent-ui.cjs；没有新增持久测试代码。
- 原8项素材/成片任务仍未完成；第9节9.2–9.6重新打开，当前45/58。保留9.1方法合同与9.7交接记录完成，不代表本批接受。由开发Agent按R1–R5修复并回写同一套文件，主Agent再复验。

## 2026-10-18 R1–R5 返修回应（开发Agent，待主Agent复验）

按上节五项逐条修复；未重置/清理相邻未提交改动，未触正式沙发数据（探针均用 goalprobe@studio.local 隔离用户新建作品），未提交/push/归档，未新增持久测试代码。修改面：apps/api/app/services/form_assistance.py（R1/R2/R5 后端）＋ apps/web/src/product/GuidedProductionGoal.tsx（R3/R4 前端）。

### R1 修复：嵌套指令副本彻底清理
- 新增 `apply_explicit_draft_stages(snapshot, frozen)`（form_assistance.py），generate/decide/feedback 三处同构调用（保持 decide 摘要对比一致）：请求带显式 stages 时，除顶层 production_methods/selected_production_stages 外，同时清理 product_context.creative_profiles.product_production_methods 与 production_profile(.settings).product_production_methods 两个嵌套冻结副本；本次冻结清单只经 explicit_draft_stages 进入审计。
- 新增 `render_snapshot_without_method_bodies`：发给模型的 project_snapshot 再去掉 explicit_draft_stages 内方法正文，启用方法正文只经 configured_methods 执行投影出现一次（无重复执行指令）；attempt.project_snapshot 审计快照保留完整清单与 manifest_hash，历史可读。
- 复验（r1-r5-probes.txt R1 组 7/7）：先经真实 save_profile PUT 持久化两项开启，再显式全关/单关/阶段总关各发请求，用真实包正文中段指纹对完整 user_prompt 递归扫描——被禁用方法正文零出现；启用方法仅出现一次；关闭以 disabled_method_ids 记入清单；不带 stages 的默认继承路径保存方法仍可读（既有行为）；显式关闭请求生成的建议 decide 采用不误报漂移（decision=adopt）。

### R2 修复：按本次 eligible 目标过滤
- run_attempt 在明确 eligible 后过滤执行投影：仅 applicable_fields 与本次目标相交（或无字段限定）的方法进入 configured_methods；完整启用选择（identity 无正文）单独记入 configured_methods_selection；feedback 重写按本次 keys 重新匹配。其他生产场景方法（如 product-script，无 applicable_fields）不受影响，未全局删除任何方法。
- 复验（R2 组 6/6）：objective 只带 purchase-reason（+product-script），primary_audience 只带 audience-need（+product-script），混合目标按并集，cta 同理；完整配置与执行投影分别记录；反馈重写 keys=[objective] 时请求只含 purchase-reason。

### R3 修复：整组关闭可保存
- 保存按钮条件改为 `!mergedStages || methodBusy || readOnly`（组关但已配置时 mergedStages 仍生成显式 disabled 条目）；组开关语义＝"任一方法实际生效"，全关持久化为 selected+enabled=false 条目，保存后回读同步页面状态（重载显示"已配置·全关"一致）；方法修改纳入 methodDirty 脏状态，进入既有 beforeunload/站内锚点点击守卫（文案含"商品方法选择"）与"有未保存的方法修改"提示。
- 复验（r3-r4-e2e.txt）：全新作品首次启用保存（B1 回归）→ 整组关闭后保存按钮可用 → 保存 PUT 200 → API 两项 selected+disabled → 重载摘要"已配置·全关"、组开关为关 → 未保存方法改动触发离开提醒且 dismiss 后页面停留。

### R4 修复：保存只合并两项，不覆盖其他入口
- saveMethodSwitches 保存时并发 GET 最新 production-profile 与 product-methods：以最新 effective_stages 为基线，只 upsert 两项方法条目（id 沿用最新既有条目），带最新 expected_revision（GET/PUT 之间再变则 409）；不再把页面旧快照的其他阶段/方法写回。
- 复验（r3-r4-e2e.txt R4 组 5/5）：页面停留旧状态期间，其他入口关闭 review 阶段并追加 product-script 方法（版本+1），本页仅切换购买理由开关保存——review 关闭与 product-script 条目保留，两项按本页选择（受众开/购买理由关），无 409/422。

### R5 修复：选区片段返回合同
- system prompt 明确合同：带选区润色时 suggestion 只返回选区范围内改写后的文字片段，不含选区外前后缀、不重复选区原文以外的句子，未选前后文由系统原样保留拼接；无选区返回整字段完整内容。拼接仍为 prefix+片段+suffix，未做任何全句通用去重（不破坏用户原文）。
- 复验：隔离探针（r1-r5-probes.txt R5 组 7/7）覆盖中间/开头/结尾/代理对（UTF-16 码元）/切半代理对 409/无选区整字段/系统提示词含合同；真实模型 6/6（real-model-samples.md 第4节、r1-r5-real-samples.txt，方法开×5＋方法关×1）：未选文字逐字保留且不重复，第2节"不用洗复杂零件"尾部重复在全部样本中不再出现。〔2026-10-18更正：本行原文标注"MiniMax-M3"不准确；六份样本（Session13–18）保存回执均为 openai_compatible / gemini-3.8-flash-high / configuration_revision=13，质量结论按回执归属，见 independent-recheck-model-receipts.json 与 real-model-samples.md 文档头。〕

### 返修后门禁与边界
- compileall、442 项既有检查（17.30s, 8 warnings）、27 项隔离探针、20 项返修探针、tsc+build（2.19s）、openspec strict 全绿（r1-r5-gates.txt）。
- 证据目录新增：r1-r5-probes.txt、r3-r4-e2e.txt、r1-r5-real-samples.txt、r1-r5-gates.txt；real-model-samples.md 增第4节。临时脚本在 /tmp（probe_r1_r2_r5.py、probe_r3_r4_e2e.py、probe_real_r5_samples.py），不入库。
- tasks 9.2–9.6 已带新证据重新勾选（50/58）；原8项素材/成片验收保持未完成；仍知现状：非 UI 客户端省略 stages 时作品级方法走既有背景继承路径（嵌套快照副本原样进入请求，review.md 171 行已记录，超出第9节最小范围未扩展）。
- 服务已重启加载后端改动（launchctl kickstart com.aicontent.api）；未提交、未push、未归档。


## 2026-10-18 主Agent二次独立验收（优先于上节开发完成声明）

**仍未通过整体验收。** R1显式关闭、R3整组关闭保存通过；R5选区返回合同及现有六份样本通过，但模型归属须按保存回执更正。R2默认继承与R4并发保存仍有可复现缺口。9.2、9.3、9.4、9.6重开，当前46/58；原8项素材/成片任务保持未完成。主Agent未改业务代码、未写正式数据、未新调用模型、未提交/push/归档。

### 已通过的返修
- R1：复跑开发20项隔离探针；真实save_profile函数先持久化开启，再显式全关/单关/阶段总关，完整请求正文指纹与采用检查通过。启用方法仅在显式执行投影出现一次。
- R2显式路径：按objective/primary_audience/混合目标过滤正确，不能据此推导省略stages的继承路径也通过。
- R3：实际GuidedProductionGoal.tsx转译执行确认整组关闭仍可保存；开发浏览器19/19证据保留，本轮没有重跑浏览器，不把组件隔离检查称为端到端验收。
- R5：只读API回读goalprobe隔离Project23/Unit29的Session13–18，五项带选区样本按UTF-16边界核验未选前后文逐字保持，另有整字段样本；六项均未重复旧尾句。修复前mock故意返回整字段的旧重放不作为本轮R5失败依据。

### R2仍需修复：保存的方法在默认继承时绕过字段筛选
位置：apps/api/app/services/form_assistance.py的draft_method_projection、render_snapshot_without_method_bodies、run_attempt。
- 内存SQLite经真实save_profile保存两项开启后，合法请求省略production_stages，仅targets=[objective]。
- 实际configured_methods=[]，但受众方法正文和购买理由正文各出现3次，分别在project_snapshot.production_methods、product_context.creative_profiles.product_production_methods和product_context.production_profile.settings.product_production_methods。
- 受众方法不适用于objective，却仍进入模型正文；执行清单为空也与实际指令不一致。这不是关闭方法泄漏，而是默认继承没有经过本次目标过滤。默认继承属于现有受支持入口，本轮新方法经此入口生效，不能以旧机制为由排除第9节适用字段合同。
- 修复边界：保留默认继承，先统一解析实际生效选择，再按本次目标渲染正文；审计保留完整冻结。无需要求所有客户端强制发送stages，也不改其他场景方法。
- 复验：真实保存后省略stages，分别objective、primary_audience、混合及feedback，扫描完整请求（非只检查configured_methods）；显式开关和采用漂移回归保持通过。
证据：independent-recheck-inheritance.txt。

### R4仍需修复：两个读取结果不保证同版本，未改开关仍会覆盖他人修改
位置：apps/web/src/product/GuidedProductionGoal.tsx:125–141。
- 两个GET读同一版本时，最新review关闭及追加product-script能保留，本轮已确认这部分改进。
- 读跨版本时：product-methods先读取旧配置；另一入口关闭review并追加product-script；production-profile随后返回revision=9。实际组件PUT携带expected_revision=9，却写入旧effective_stages：review变回true、追加方法消失。若此后没有新写入，revision保护无法识别这次旧配置覆盖。
- 另一独立场景：页面原A开/B开，远端将A关，本页仅改B关；两次GET均取得最新数据，实际组件仍写回A开/B关，覆盖用户没有修改的A。原R4已要求核验同方法冲突，本次仍未处理。
- 修复边界：保存须使用同一版本的配置与revision；仅提交用户实际修改项，或按页面基线检测冲突并保留草稿。总开关明确修改全部时另按其意图处理，不允许用最新revision静默覆盖旧选择。
- 复验：同版本合并、两GET之间写入、GET后PUT前写入、同方法远端变更而本地未改、同方法两边均改；允许明确冲突，不能丢设置。
证据：independent-recheck-component.txt；实际TSX转译执行，React/API为隔离替身，展示真实构造payload，不是线上竞态发生记录。

### 模型证据更正（不新增功能）
开发文档称六份R5真实样本使用MiniMax-M3，但Session13–18保存回执均为provider=openai_compatible、model=gemini-3.8-flash-high、configuration_revision=13、profile=registered.ddd9b006056eae2bfb76b2ee。质量检查可归属于这些保存样本，不能宣称已验证MiniMax-M3；回执只是平台注册路由标识，不进一步推断网关实际上游模型。按实际回执更正real-model-samples及交接描述；若另声称MiniMax覆盖，须另有匹配回执。
证据：independent-recheck-model-receipts.json；本轮只读回读，无新增计费调用。

### 本轮独立执行结果与交接
- 442既有检查通过（8 warnings，18.72秒）；Web完整构建及bundle门禁通过；OpenSpec strict通过。
- 开发返修探针20/20复跑通过；额外继承及组件竞态探针复现以上缺口，证明现有绿灯未覆盖这些边界。
- evidence/goal-methods-20261017/independent-recheck-{probes,inheritance,component,tests,build}.txt、independent-recheck-model-receipts.json和independent-recheck-scope.json记录本轮证据及实际源文件hash。
- 临时探针仅在/tmp，未新增持久测试代码。继续由开发Agent修复R2/R4并更正模型说明后交主Agent复验；不重开R1/R3，不扩大新功能。

## 2026-10-18 R2/R4 返修回应（开发Agent，待主Agent复验）

按二次验收两项缺口逐条修复；未重置相邻未提交改动，未触正式数据（探针均 goalprobe@studio.local 隔离用户新建作品 Project24–32/Unit30–38），未提交/push/归档，未新增持久测试代码，无新增模型调用。修改面：apps/api/app/services/form_assistance.py（R2）＋ apps/web/src/product/GuidedProductionGoal.tsx（R4）。

### R2 修复：默认继承统一按目标字段筛选
- 原因与位置：run_attempt 的目标过滤只作用于 explicit_draft_stages；省略 production_stages 的请求未建立执行源，三项嵌套冻结副本（project_snapshot.production_methods、product_context.creative_profiles.product_production_methods、product_context.production_profile.settings.product_production_methods）原样进入 user_prompt，不适用的受众方法随 objective 请求注入且 configured_methods 为空（form_assistance.py 原 generate/decide/feedback 只在显式 stages 分支调用 apply_explicit_draft_stages）。
- 实际修复：新增 product_brief_unit 与 apply_inherited_draft_stages（form_assistance.py，紧随 apply_explicit_draft_stages）：商品域 product_brief 会话在省略 stages 时，把 project_snapshot 已冻结的有效方法清单（顶层 production_methods，即 brief+作品级合并后的 freeze 产物）统一当作 explicit_draft_stages 执行源——generate/decide/feedback 三入口同构接入。继承选择自此与显式选择走同一条链：嵌套正文副本清理、eligible∩applicable_fields 过滤、configured_methods_selection 记录、渲染快照正文去重、decide 漂移对比（继承配置变化→409 重新生成）全部生效。默认继承能力保留；未强制客户端发送 stages，未删除任何其他场景方法（product-script 等无 applicable_fields 方法保持原合同）。
- 复验方法与结果（r2-r4-before/after.txt R2 组；先经真实 save_profile PUT 保存再省略 stages 发请求，扫描完整 user_prompt 的真实包正文中段指纹并递归定位路径）：修复前 10 项 FAIL（两条正文各出现 3 次、路径与 independent-recheck-inheritance.txt 一致）；修复后 18/18 PASS——objective 只渲染购买理由一次（含 configured_methods 唯一路径）、primary_audience 只渲染受众、混合并集各一次、表达字段同理；继承会话 feedback 按 keys 重匹配；保存全关/单开/阶段总关继承零正文或按保存状态；配置未变时可采用（decision=adopt）、生成后其他入口改配置采用被 409 阻止；显式全开/单关/全关/阶段总关回归不变。原 27 项、20 项 R1–R5 探针同步更新断言后全过（"默认继承可读"旧断言按新合同改为"继承按目标过滤渲染"）。
- 已知边界：统一解析覆盖商品域 product_brief surface（含镜头提示词润色等该 surface 全部目标）；production_profile surface 助手与 persona 域不走此链（第9节范围外，行为不变）。

### R4 修复：同版本基准＋仅提交实际修改项
- 原因与位置：GuidedProductionGoal.tsx saveMethodSwitches 用 Promise.all 并发读取 production-profile 与 product-methods——两响应可能跨版本（product-methods 旧配置＋profile 新 revision），PUT 以新 revision 提交旧阶段配置覆盖他人修改；且无条件 upsert 两项开关，用户未修改的开关把远端修改写回旧值。
- 实际修复：保存改为先读 production-profile；基准取该响应自带的 settings.production_stages（与 revision 同源同版本），作品级从未保存 stages 时才读 product-methods effective 继承（此情况下任何并发作品级写入都会提升 revision，PUT 必得 409 而非覆盖——两分支均保证配置与 revision 同版本）。合并仅写入用户实际修改的开关（与页面载入基线 diff；组开关切换视为对两项的明确整体修改：启用＝两项默认开、关闭＝两项全关），未修改项原样保留最新版本条目（含其他入口更改）；无修改时不发 PUT。409 沿用既有提示且保留草稿与脏状态，不自动重试。
- 复验方法与结果（Playwright 真实组件＋真实保存接口，路由拦截注入竞态；r2-r4-before/after.txt R4 组，PUT payload 逐项断言）：修复前 S2（两GET间写入）覆盖远端 review 关闭与新增 product-script、S4（远端关A本地仅关B）把 A 写回开——2 项 FAIL；修复后 7 场景 21/21 PASS——同版本合并保留远端其他阶段与新增方法；两GET间写入（product-methods 喂旧配置＋profile 新 revision）不覆盖；GET后PUT前真实写入→PUT 409、草稿保留（未保存提示与开关状态不变）、重存成功且保留远端；远端改A本地仅改B→A 保留远端关闭；同一方法双方均改→一致结果（二元开关下双方从基线改向必然一致，本地明确修改按用户意图写入）；整组关闭保存及重新载入一致（R3 回归）；另补 S2b 回退路径（作品级无 stages 的两GET分支，product-methods 读取前注入真实写入）→409 草稿保留、重存保留远端（4/4）。
- 已知边界：PUT 与服务器间的最后竞态由既有 revision CAS 兜底（409＋草稿保留）；页面基线 diff 无法区分"切换后改回原值"的净零变化（视为未修改，不写入）；基准取作品级 stages 意味着保存不再把 brief 级阶段物化进作品级（brief 级配置继续按 effective 合并生效）。
- 过程说明：复验期间一次外部并行编辑短暂向 saveMethodSwitches 注入"同方法冲突抛错"逻辑导致一次 S5 误报，用户已恢复为本次实现；最终证据均为恢复后运行（r2-r4-after.txt，Project31/Unit37 及以后）。

### 模型证据说明更正（无新增功能/调用）
- 六份 R5 样本（Session13–18）模型归属按 independent-recheck-model-receipts.json 更正：provider=openai_compatible、model=gemini-3.8-flash-high、configuration_revision=13、profile=registered.ddd9b006056eae2bfb76b2ee；不再标注 MiniMax-M3。已在 real-model-samples.md（文档头路由说明、第2节结论、第4节归属）与本文 R5 回应行以更正括注统一改写，2026-10-17 历史节原文保留；回执仅作平台注册路由标识，不推断网关实际上游模型。未为此调用模型。

### 返修后门禁
- compileall、442 项既有检查（17.91s, 8 warnings）、27 项原探针、20 项 R1–R5 探针、18 项 R2 继承探针、tsc+build（2.22s）、openspec strict、git diff --check 全绿（r2-r4-gates.txt）。API 服务已重启加载 R2 后端。
- tasks 9.2/9.3/9.4/9.6 带新证据重新勾选（50/58）；原8项素材/成片验收保持未完成；仍未提交、未push、未归档。


## 2026-10-18 主Agent接续修复与最终复验：第9节通过（50/58）

用户已授权主Agent直接修复。接收开发R2/R4交付后完成代码、探针及证据复核，并补齐三个同范围继承缺口；本节为第9节当前结论，前述退回与开发回应保留作历史。

### 最终实现与补齐
- R2的显式/继承统一执行源、按目标过滤、去嵌套正文、generate/feedback/decide同构处理通过。额外实测发现project_snapshot先读有效配置，再套任务书会反转作品优先级：任务书受众开、作品受众关时，修复前正文A=1，修复后A=0且购买理由P=1。商品域现在沿用effective_profile已经合并的阶段，不再次用任务书覆盖作品。
- 冻结版本补齐：有任务书stages时原代码无条件弃用保存清单，可能重载目录方法正文。商品product_brief改用context_snapshot已核对有效选择的冻结清单；保存后替换目录正文的隔离探针，在无任务书及同配置任务书两种情况下均保留原正文。
- R4保留仅写本地净变化的开关、组切换明确写两项、无变化不PUT、409保留草稿。作品只有review覆盖、script从任务书继承时，单取作品stages会在保存时丢掉继承的product-script和未修改开关，已复现并修复。最终保存固定为：先GET profile版本及settings，再GET有效方法配置，以有效配置合并局部选择，PUT携带第一次读到的revision。两读间或PUT前发生作品写入会返回409，不能用新revision覆盖旧配置。
- 同一二元开关从同一基线均改向同一值时允许保存；保留最新条目其他参数，不再加无必要的同值冲突限制。本轮独立组件链验证该语义。修改后改回原值视作净零变化，不写入。
- 六份R5样本按保存回执标记为openai_compatible / gemini-3.8-flash-high / configuration_revision13，原MiniMax归属已更正；没有为更正文案调用模型。

### 本轮实际验证
- 442项既有检查通过（8 warnings，17.52秒）；Web TypeScript/完整构建及bundle门禁通过，Python compileall通过。
- R2继承探针18/18；R1–R5回归探针20/20；补充作品覆盖任务书1/1、冻结正文兼容2/2。全部在隔离内存SQLite，通过实际save_profile路径冻结再捕获完整模型请求；模型provider为替身，不冒充真实生成质量检查。
- 实际GuidedProductionGoal.tsx转译执行，React hooks为隔离替身，API调用连接真实read_profile/save_profile/product_goal_methods函数及内存SQLite，9个场景全部通过：保留其他阶段/方法、两GET之间写入409、PUT之前写入409及明确重存、远端A本地B、同开关同值修改、整组关闭、首次启用、部分作品覆盖时保留继承script、无修改只刷新。该证据是组件与真实服务函数集成，不是浏览器端到端；开发之前的浏览器证据保留，不冒称本轮重跑。
- 综合代码复核、Python复核和TypeScript复核均未再发现本次范围内阻断问题；两处继承错误与冻结错误修复后已由只读评审方复核。
- 重启com.aicontent.api加载最终代码；GET health/ready返回200且ready=true，隔离作品方法读取接口200。没有写正式沙发数据、没有新增模型调用或持久测试代码。
- 本轮证据：evidence/goal-methods-20261017/main-final-{r2,regression,override,frozen,component,tests,build,runtime}.txt、main-final-scope.json（最终业务文件hash及基线）。临时脚本仅/tmp。

### 验收边界与下一步
R2/R4关闭，第9节9.1–9.7接受，tasks为50/58。CAS覆盖作品production-profile修订；本次未新增任务书与作品跨对象事务，不声称验证了继承来源跨对象同时修改的原子性。R1/R3/R5已通过结论继续保留，真实模型质量只归属已有回执样本。
同一change原8项真实素材/新片及收尾任务仍未完成；不归档、不提交、不push。main@8539806加未提交修改，保留相邻工作。下一步按原材料清单继续商品资料/参考片、确认图和人工回传视频，再验收旁白成片；不重开第9节开发。


## 2026-10-18 剩余八项与一次性材料核对
本轮仅剩余任务/材料交接核对：服务ready、SKU/主稿/声音只读回执在evidence/guided-workspace-20261017/remaining-intake-readback-20261018.json。原工程检查已完成，不重复充作素材质量验收；7.12操作交接补齐，但真实使用反馈未签收，原八项保持开放、50/58。无代码改动及业务写入。

2026-10-18 收尾：相邻生命周期任务将数据库升级unitlife000001，造成原运行配置productdomain0001短暂schema_head_mismatch；核对其加法迁移后仅将API运行环境REQUIRED_SCHEMA_HEAD对齐，最终ready=true。本实拍任务未执行该迁移，未更改相邻实现。

### 2026-10-18 最后返修独立复核
Python复核通过：同原片新任务复核14项API检查、SKU /use隔离及配置投影均通过。TypeScript最终复核通过：当前任务hash优先、同hash可用记录优先、历史不进入可采用选项，独立tsc通过并核对15项探针和源码哈希。通用代码review限定范围通过。没有剩余已发现的非素材阻断问题；当前真实原片仍0条，不作实片质量结论。
