# AE 模板：做法与入库规则

## 结构

- 工程放在本机模板库（默认 `~/AIContentStudio/ae-templates/<id>/<version>/`），用 XML 格式 `template.aepx`，图片素材放在同一目录。
- 说明书放在平台 `craft_skills/ae-motion/templates/<id>/<version>/manifest.json`：用途、字段（text 带字数上限，number 带范围）、图片槽、时长范围、比例、字体、工程文件名和 SHA256、主合成名 `MAIN`、`checks`。

## 数据怎么进模板

- 可替换的图层命名为 `@字段名`。
- 表达式读取同一段数据：`var d=/*AICS_DATA*/{...}/*AICS_END*/;`。渲染时平台复制工程，只改这一段，再用 aerender 后台出片。aerender 不能读取 JSON 素材，所以数据写在表达式里。
- 文字：Source Text 表达式 `String(d["字段"]||"")`；锚点居中、超宽自动缩小；空字段用不透明度表达式隐藏。
- 图片：模板里放一个占位 PNG；渲染时用同名文件替换。

## 入库检查

1. 用 `make_templates.py` 或手工在 AE 里搭好，另存为 `template.aepx`。
2. 写 manifest，填工程 SHA256。
3. 换两组差别明显的内容（长短、空字段、不同数字）各渲染一次，看入场、中段和定格三帧。
4. 两次都正确，把检查写进 `checks`（日期、内容摘要、结论）。少于两次的模板是 draft，平台不自动选用。

## 版本

模板一改就出新版本目录（v2…），旧版本保留，已渲染的素材仍能追溯到当时的版本。
