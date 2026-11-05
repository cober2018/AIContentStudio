# task_plan：redub-locate-by-subtitles

目标：只重配几句时，没有逐句时间就先按导演稿字幕定位每句。

///
1. 只读核对作品 95 字幕与有声段边界，写方案，`openspec validate`，等「确认」
2. 改 `_line_spans`、`_redub`
3. 库副本 + 假 TTS 验证；挪字幕 2 秒验证；已有测试
4. 「重启吧」；真实重配要用户另外同意；「提交吧」归档提交
///
