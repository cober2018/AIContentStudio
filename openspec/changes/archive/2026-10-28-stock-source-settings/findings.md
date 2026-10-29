# 发现与决定

- 现状：Key 只在 `scripts/startup/runtime.env`（只配了 Pixabay）；`open_media.py` 已有 6 个来源，镜头匹配只搜视频和图片，没有音频搜索。
- 用户决定：先做设置入口和 Coverr；音频来源下一个需求；数字人生成排第三。
- Coverr Key 要发邮件给 team@coverr.co 申请；搜索 `GET https://api.coverr.co/videos?query=&urls=true`，用 `mp4_download` 直接保存不需要额外上报下载；要求在应用里注明来源（入库时署名「Video from Coverr」）。
- 「清除」会在页面存一个空 Key，之后不再回退到 runtime.env，这是有意的：清除就是不用。
- `open_media.py` 新加的 `about` 类属性触发 ruff RUF012，和文件里原有的 `download_hosts` 写法一致，未改。
