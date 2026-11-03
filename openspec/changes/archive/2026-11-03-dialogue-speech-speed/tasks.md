## 1. 导演稿
- [x] 1.1 `video_documents.py`：声音段 speed_percent（50–200）、长度校验允许 ±34 毫秒、规范化保留
- [x] 1.2 `creative_mcp.py`：save_director_draft 说明加 speed_percent?

## 2. 整片变速
- [x] 2.1 `voiceover.py`：按倍速换算时间轴并存新主稿；status 返回 speech
- [x] 2.2 `edit_agent.py`：PUT voiceover/speed
- [x] 2.3 `video_chain.py`：_keeps_draft 加 speech_speed；「口播声音」规则文字
- [x] 2.4 craft-resolve `techniques/sound.md`「声音轨口播衔接」第一条

## 3. 页面
- [x] 3.1 `VoiceoverPanel.tsx`：语速滑块（只在有声音轨时显示）、实时新时长
- [x] 3.2 `StoryboardTable.tsx`：声音段标倍速；`VideoStudioModel.ts` 类型加 speed_percent

## 4. 验证
- [x] 4.1 数据库副本上作品 94：1.15 / 回 1.0 / 校验三项；页面看滑块和分镜标注
- [x] 4.2 全量测试、前端类型检查；写 progress.md
