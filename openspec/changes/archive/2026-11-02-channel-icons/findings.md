# findings

- 试下载各平台官网 favicon.ico：15 个能取到图片；视频号 channels.weixin.qq.com/favicon.ico 返回网页，需要从页面声明的图标地址取。网易号、头条、YouTube 只有 16px。
- 渠道显示文字来自后端 /channels，前端多处自己拼 channelLabel；下拉框里不能放图片。
- 用的是平台官方图标原样，只做界面标识，不是仿制，也不进生成内容。
- 视频号官网 favicon.ico 是网页，实际图标在页面声明的 res.wx.qq.com/.../favicon-v2.ico。
