# progress

- 2026-11-02 方案已写，等用户确认。
- 2026-11-02 用户确认后已本地实施，未提交：content_identity.public_platform_id 放宽（任意文字 1–64 字、去首尾空格；拦控制字符、网址、www.、sk- 开头、密钥字样、32 位以上令牌串；公众号仍只收 wx AppID）；两处登记表单提示与报错文案同步。
  - 抽查：「Kubo酱｜冲浪少女」「desk-talk」「知数 Talk 🚀」「@zhishu_talk」通过；sk-abc123、网址、www.、含 token、换行、40 位长串被拒；公众号填昵称被拒。全量 2441 通过、只剩 5 个已知失败；tsc 通过；API 已重启。
