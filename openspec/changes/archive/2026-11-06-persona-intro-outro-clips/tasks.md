## 1. 后端
- [x] 1.1 IdentityProfile 加 intro_clip/outro_clip，_persona_clip 检查；BrandProfile 删字段，读旧版本丢弃
- [x] 1.2 GET /content-personas/{id}/clips，删 /content-brands/{id}/clips
- [x] 1.3 video_chain 从角色取片段；全链路改名 persona_*，文字改「角色」
## 2. 前端
- [x] 2.1 BrandClips.tsx → PersonaClips.tsx；角色编辑页加两块；只读页显示、KNOWN 加字段
- [x] 2.2 品牌设置页删片段
- [x] 2.3 VideoChainPanel 改名和文字
## 3. 验证
- [x] 3.1 库副本：角色 6 存 618/619，开成片任务看结果、执行包、清单检查；不合规视频被拒；品牌 6 打开保存正常
- [x] 3.2 测试、tsc、规范校验
## 4. 上线（等「上线」，先备份）
- [x] 4.1 品牌 6 新版本去掉片段；角色 6 新版本设 outro 618/619
