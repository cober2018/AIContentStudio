# exfat-material-drive

- 阶段：缺陷修复（用户反馈粘贴主图没缩略图），已本地实施，未提交
- 问题：素材盘换成 500g（exFAT）后，所有新文件写入素材库都报 500：material_storage 先写临时文件再 os.link 硬链接到正式位置（保证不覆盖已有文件），exFAT 不支持硬链接（Errno 45）。粘贴主图、上传素材、生成图片都受影响。
- 修复：apps/api/app/services/material_storage.py 新增 _place：先试硬链接；不支持时用 O_EXCL 独占建正式文件名，再 os.replace 临时文件过去；失败清掉占位。仍然不覆盖已有文件。三处写入都改用 _place。
- 验证：在 500g 上实测放置成功、已有文件不被覆盖；真实存储写入读回一致（测试文件已删）；存储相关测试 30 passed；API 已重启。
- 同时：粘贴 / 上传成功后显示本地缩略图（ProductWorkbench），记录在 project-product-opens-new-sku。
