# 商品视频Skills与原生后期适配 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task after explicit proposal confirmation. Steps use checkbox syntax in tasks.md for tracking. 按用户约定不新增持久测试/示例代码。

**Goal:** 将六组来源映射为商品专用方法，复用平台十阶段开关与AE/Resolve后期，完成一支真实商品样片。

**Architecture:** 保持Persona风格与商品任务参数分离；新增六项CapabilityMemory方法，复用原生产包、输出与接受合同。执行由Codex通过平台CLI/MCP及本机专业软件MCP完成。

**Tech Stack:** 现有Python API、TypeScript Web、版本化JSON/CapabilityMemory、AE/Resolve MCP、OpenSpec。

## 当前阶段

2026-10-16：v2 CONFIRMED_APPLYING。实施20/20；真实样片、正式回收、纯候选与独立复核通过；规范归档和本地选择性提交均完成。本计划持续维护，不另建计划目录。

## 文件职责与最短实施顺序

1. **任务1.1–1.4：方法资产。** 修改现有 `.codex/skills/video-production-handoff/references/production-methods.json`、`THIRD_PARTY_NOTICES.md`；扩展已有 `SKILL.md` 的商品分支及引用。每项方法写适用阶段及节点、参数、输入输出、固定来源和校验状态，提供按需加载的完整方法卡。主图/一致性优先，服装/软件分支不误套实物。非执行指令留平台，执行脚本留工具库。研究清单在本目录source_inventory.json/research.md。验证JSON可解析、引用与hash对应、方法名无重复。
2. **任务2.1–2.3：最小平台接入。** 先读相关目录README，再读 `apps/web/src/product/ProductCreationDialog.tsx`、`PersistentProjectsPage.tsx` 及已有阶段覆盖组件；后端定点核对 `apps/api/app/services/project_brief.py`、`content_identity.py`、`creative_executions.py` 与现有web_video_handoff.py中实际商品字段/方法冻结路径，本轮已核实补充 `product_creation.py:save_launch/resume_launch`调用链、`creative_configuration.py:frozen_stage/freeze_production_stages`、`creative_packages.py`、`capability_contracts.py` 和 `model_capability_routing.py:_multimedia_controls`。必须补齐首轮启动前保存/冻结任务方法、恢复同一launch时版本一致、AI规划与确定性节点适用性。ProductOffer按促销需要最小可选扩展；不能向scalar-only args塞嵌套数据。图片仅走已验证参考图通道或原图/保真合成退路，不新增网关。只有实际缺口才编辑；不引入新数据表或第二套Recipe。通过CLI调用现有REST或使用MCP准备任务，验证覆盖、off与历史不变。
3. **任务3.1–3.4：原生组合。** 更新 `references/native-execution.md`，先搜索既有AE工具库，再用本机MCP做两个AE与一个Resolve小样；小样与观察回执保存本需求evidence及受保护本机媒体目录。每个AE合成分别核对时长/分辨率/fps/alpha、色彩解释和回Resolve后的商品颜色。促销只用已核实金额与静态截止时间。保存、重开、渲染分开，失败/unknown先核对原操作。只回传真实产物。
4. **任务4.1–4.5：实际商品。** 用户商品资料到位后保存任务书、方法与素材引用。用正常入口对应的CLI/REST或MCP完整跑通；网页部分人工，等待期间不冒充完成。先声音后节奏/字幕校色，再按需AE，回Resolve终混。质量审查覆盖证据、SKU外观、售价条件、镜头效果、字幕、声音和工程。保存已检查/未检查的明确边界。
5. **任务5.1–5.4：正式采用与关闭。** 相关既有API suites、Web build/bundle、规范strict和独立代码复核；具体测试文件在实施时按实际改动定点选择。备份正式数据/媒体/相邻差异；仅导入本需求方法，不默认覆盖经营角色。正常回读执行与旧记录。通过后更新本文、progress/findings/review/README，归档和选择性本地提交，不push。

## 验证与完成条件

每项真实回执落progress；tasks.md只在实际完成后勾选。完整样片、原生工程、方法开关生效与正式回读必须分别通过；用户未提供商品资料或未回传所需视频则对应步骤保持未完成。声音技术/ASR不能替代直接试听结论。许可与上游网关不直接继承为执行权限。

## 本轮执行步骤（用户已确认v2）

/// 先隔离现有工作树并记录相邻文件hash。
/// 完成方法卡与来源，再补齐商品任务冻结/适用性/页面。
/// 运行既有检查和独立代码审查，完成AE与Resolve真实组合小样。
/// 首件商品资料到位后跑真实样片、回收及质量评审；缺资料时保留未完成项。
/// 正式接入回读和保全通过后才归档并选择性本地提交。

/// 完成：10条主规范同步，47/47 strict，20/20归档，本机main选择性提交；未push。
