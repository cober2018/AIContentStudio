# AI补空白与当前字段润色实施计划

已获用户确认并完成；本文件是此需求唯一计划。用户最新修正优先：允许任意已填部分作为起点，不要求完整意图。

**目标**：共享浮窗支持补未填项、定点润色、逐项确认和明确反馈迭代。
**架构**：字段适配+结构化建议服务，复用LLM路由、Brief/Master保存和Capability候选；单个有归属的会话实体记录尝试与反馈。
**技术**：现有FastAPI/SQLAlchemy/Pydantic及React/TypeScript，不新增供应商SDK。

执行时使用executing-plans，代码复核按现有要求；不新增测试代码，不生成示例代码。

/// 1. 核对隔离基线与已批准规范，保持旧change和相邻改动。
/// 2. 字段清单覆盖ProductCreationDialog.tsx、project/ProjectBriefTab.tsx、CreativeIntentEditor.tsx、VideoStudioShell.tsx、VideoShotMaterialPanel.tsx及现有脚本/音频子组件；逐项标注保护、空白、事实、类型和依赖。先校验数据流再接控件。
/// 3. 更新services/model_registration.py、services/generation/providers.py、services/system_settings.py及ModelRegistrationSettings.tsx：两个用途、同一版本保存、回执与错误显示。复用既有模型登记检查。
/// 4. 在models.py及现有Alembic versions目录增加会话实体和单一加法迁移。隔离数据库验证owner/project/unit与LLMRun关联、旧记录保留；不提前运行正式迁移。
/// 5. 新增services/form_assistance.py和routers/form_assistance.py，通过main.py现有路由方式挂载；字段白名单共用于输入和响应校验，不接受任意JSON路径写入。先临时探针验证补空白/保护意图/类型/事实缺失/失效，再接页面。
/// 6. 共享FormAssistancePanel.tsx及字段适配负责固定浮窗、捕捉目标、逐项差异与采用，不改DOM、不独立保存Master。创建弹窗在真正发起项目之前也可请求建议。
/// 7. 将商品页和视频台按现有onChange接入；保留手动表单、已填值和每页原保存行为，验证新图/新字段/新意图变化能使旧建议正确失效。
/// 8. 反馈按单次尝试保存；重新生成新尝试不覆盖旧输出。“以后也这样”通过capability_memory的创建/版本/生命周期/明确使用接口产生候选，不伪造capture-preference所需的Master编辑证据。
/// 9. 复用既有product_settings、model_registration、recipe、video_documents、creative_executions等检查，临时探针覆盖空白0/false、手改并发、跨用户、冻结历史、重试、成本隔离和偏好范围；npm run build通过。实际具体检查文件在实施时按现存路径核对，不全量扫描。
/// 10. 选择有效已配置模型做有来源的最小真实请求验收，比较“原结果→具体反馈→新结果”是否落实修改；区分网络成功/结构校验/内容质量，人工选图仍独立。
/// 11. 独立代码与规格复核，通过后按批准范围备份接入，核验正常页、旧资料和模型配置；保存实证，不用Mock当真实模型质量证据。
/// 12. 回写README/progress/findings/review，全部满足后再归档与选择性提交；不改变相邻12/14的图片确认状态。

/// 13. 范围补充：product_context增加品类标识与所选风格精确版本；沿既有Capability结构化内容保存适用条件和阶段方法组合。UI在商品创建/任务书显示选择与阶段开关差异，明确应用才生效，不新增Persona或库存系统。
/// 14. 反馈区分“商品资料/品类方法/表现风格/阶段技巧”与“本次/当前商品/指定品类/指定风格/通用方法”；权限范围和适用标签分别校验，默认只作用本次。临时探针验证同品类不同风格、跨品类显式复用、事实不传播、关闭方法不自动恢复；本批反馈不覆盖已填项。

执行顺序：上述13/14分别并入步骤2字段合同、步骤8反馈接续及步骤9验收，不在归档后追加实施。任务清单该阶段为16项，最终为17项。

/// 15. 用户补充素材核心：先读取现有video-production-handoff及四项商品方法，明确一个“商品视频素材导演”编排入口，在既有能力包装中引用选定子方法版本；不把图片提示词直接充当动态提示词。前端在三列台串接图像审查→精确选图→看图设计动作/运镜→提示词审查→人工回传→实际片段检查。单元不自动发布/选图/接受。
/// 16. 验收增加实际图像输入能力、换图失效、复杂动作分拆、图片准确性与美观分开、返回视频变形/动作失败定位、已验证与待验证修订区分。当前外部视频需用户回传才可做实际质量结论，不以模型自评代替成片检查。上述并入步骤6至10，现共17项任务；未执行。

/// 17. 完成：恢复startup-cleanup快照、独立复核与修复、纯候选286检查和Web构建、本机备份/加法迁移/服务重载/API和页面回读。归档同步只包含本新增能力，旧商品审图仍独立。
