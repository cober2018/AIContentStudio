---
key: studio.video.director-package
version: 1
source_kind: studio_builtin
---

把接受的Video Master、镜头计划和精确素材整理为director.video.v1，使用现有stage.professional.prepare桥接外部执行。描述目标、约束、人工验收项与所需输出，不自动dispatch执行器。请求比例必须和现有Video Master/目标profile一致，不重新创建内部剪辑引擎或video.master.v3。原v1/v2/render/Candidate历史保持兼容。外部结果先staging，人工接受才成为MaterialRevision，然后仍需显式绑定保存Master；本包的说明不授权发布、审批或任意文件系统操作。
