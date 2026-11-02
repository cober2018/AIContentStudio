# findings

- sohu 出现在 7 个后端文件（种子、注册表、改写要求、适配器、表单、文档 schema、跳转入口），前端没有写死。
- 正式库：channel_template_version 有 sohu 2 行（id 11 已归档、24 已发布），无任何表引用；账号、作品、渠道版本里 sohu 均为 0。
