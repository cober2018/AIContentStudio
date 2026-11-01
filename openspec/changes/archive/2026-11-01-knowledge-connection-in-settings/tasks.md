## 1. 后端
- [x] 1.1 `obsidian_knowledge.check_speech_folder` 去掉子目录名单检查，只校验在库内且存在
- [x] 1.2 `obsidian_knowledge.speech_samples` 去掉名单检查；`read_note` 加参数让角色样本读取跳过名单（路径安全检查保留）

## 2. 前端
- [x] 2.1 新建 `KnowledgeSettings.tsx`，把 `ObsidianKnowledgePanel` 里的连接设置表单搬过去；设置目录加「知识库」分区
- [x] 2.2 项目「来源与证据」去掉连接表单，未连接或要改时提示「设置 → 知识库」
- [x] 2.3 角色逐字稿文件夹的提示改为「知识库里的任意文件夹」

## 3. 验证
- [x] 3.1 更新受影响的现有测试；跑全量后端测试和 tsc
- [x] 3.2 用数据库副本验证：名单外的角色文件夹能保存、能读到样本；库外路径被拒
- [x] 3.3 `openspec validate knowledge-connection-in-settings`
