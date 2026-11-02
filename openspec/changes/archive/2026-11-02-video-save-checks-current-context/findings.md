# findings

- 报错来自 content_masters.save_revision：expected_context_hash 与 _hash(_context(...当前...)) 不等即 409 master_context_conflict。
- MCP 视频保存走 video_chain._save → edit_handoff._save，后者传 get_revision()["context_hash"]，即上一版存的 row.context_hash（旧上下文）。
- save_revision 写入后还有一道复核（再算一次当前上下文），并发保护不依赖这个期望值。
