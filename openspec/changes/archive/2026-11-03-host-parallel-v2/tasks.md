## 1. 搭建脚本
- [x] 1.1 `make_templates.py`：VERSIONS 登记 v2、示例 4 张、`hostParallel` 支持 4 张和按框宽缩标签、合成长度按模板（host-parallel 60 秒）
- [x] 1.2 `landscape_layouts.py`：横屏替换表跟新写法
- [x] 1.3 `make_previews.py`：图片对应表加 img4
- [x] 1.4 `check_safe_area.py`：按 VERSIONS 找版本、`--until`

## 2. 入库
- [x] 2.1 AE 搭竖屏、横屏 v2 工程；写 `templates/host-parallel/v2/manifest.json`（两个 SHA256，checks 空）
- [x] 2.2 A、B 两组 × 竖横两种渲染，截三帧，和 v1 并排对比视频，放 `output/_平台/模板审片/host-parallel-v2/`
- [x] 2.3 A、B 两组 × 竖横跑安全区检查，零越界
- [x] 2.4 `make_previews.py` 出 v2 预览
- [x] 2.5 `SKILL.md` 模板表补 v2
- [x] 2.6 核对 v1 文件（说明书、工程、预览）没变；平台列表里 v2 是 draft

## 3. 用户验收后
- [x] 3.1 用户看对比视频确认后写 checks（状态变 ready）
