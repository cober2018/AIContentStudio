# findings

- 现规则在 content_identity.py：_PUBLIC_HANDLE=^[\w.@-]{1,64}$，_SECRET_MARKERS 用「包含」判断（含 sk-），_TOKEN_LIKE 32 位以上长串；公众号单独要求 wx AppID。
- 用户登记 X 账号填「Kubo酱｜冲浪少女」因全角竖线和空格被拒。
