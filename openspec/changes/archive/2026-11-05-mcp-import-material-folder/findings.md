# findings

- 页面接口 `POST /content-projects/{id}/materials/folder-import` 先做 `mutable_project`（项目归属 + 串行锁；已归档项目返回 409「已归档项目仅可查看历史」），再调 `project_folders.import_folder`。
- 「锁定的项目」按 `mutable_project` 的定义，就是已归档项目。作品级的「成片通过后锁定」是视频链路的概念，不在这个检查里。
- 409 的说明是纯文字，MCP 会把它显示成 `creative_domain_conflict`，模型看不到中文原因。验收只要求拒绝，这次不改。
- 验收文件夹现有 10 张 png。
