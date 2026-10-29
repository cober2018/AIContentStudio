# 进展

- 2026-10-28 提案建立，待用户确认。
- 2026-10-29 用户确认提案。平台部分完成：manifest 加 category（九类）、variants、previews；craft_skills 按 aspect 选工程（缺画幅报 ae_template_aspect_unavailable，不拉伸）、读取预览；MCP render_ae_template 加 aspect，两个模板工具说明写入选模板规则；设置页新增只读「AE 模板库」（GET /api/v1/settings/ae-templates、/preview/{9x16|16x9}，按类别分组、竖横切换、带身份取视频播放），本地浏览器验证可用；craft-ae 新增 make_previews.py（示例图在本机 _samples/），check_safe_area.py 支持 --aspect 16:9；SKILL.md 写入「默认模型自选、用户点名必用、画幅跟片子走」。竖屏 52 个模板出了库内预览（compare-pair v1 已停用未出）。后端相关测试 102 通过，前端 tsc / 37 测试 / build 通过。
- 2026-10-29 横屏：make_templates.py 支持 --aspect 16:9，横屏布局放 landscape_layouts.py（每个模板一张「竖屏数值→横屏数值」替换表，动画与数据逻辑共用，构建时生成 <fn>L）。46 个横屏工程全部构建成功，16:9 安全区检查零越界（检查工具边缘容差放宽到 2 像素，避免把滑过画面边缘的元素误判）。
- 2026-10-29 横屏 46 个对比视频完成（左：横屏两套内容叠 16:9 安全区图；右：竖屏对照），审片页 output/template-preview-landscape/index.html。地图落钉横屏预览改用 16:9 示例地图（make_previews 同步），否则竖屏地图坐标在横屏里跑出画面。等用户分批验收。
- 2026-10-29 用户反馈 #14 要「先收回再放开、顺序跟口播」：beats 改为每张「展开秒-收回秒」，前一张完整收回后下一张再展开（只给展开秒时下一张前 0.7 秒自动收回）；竖横两版重建、安全区零越界，审片视频与库内预览更新；SKILL.md 加 beats 按配音字幕逐句时间填写的规则。
- 2026-10-29 用户验收横屏全部通过（「这个应该都可以入库了」）。46 个 manifest 写入 variants["16:9"]（template-16x9.aepx、SHA256、1920×1080）、aspect_ratios 加 16:9、每个追加两条横屏检查记录；地图落钉 use 补充横屏要给横屏地图、点位留在安全区。平台真实渲染验证：name-plate 16:9 出 1920×1080 带透明 .mov（项目 41 素材 183 / 版本 188，测试产物）；number-card 请求 16:9 返回 ae_template_aspect_unavailable。横屏库内预览批量生成中。
- 2026-10-29 横屏库内预览 46 个生成，46 个 variants 哈希核对一致，53 个模板全部 ready；后端相关测试 175 通过，横屏预览接口返回视频；归档。
