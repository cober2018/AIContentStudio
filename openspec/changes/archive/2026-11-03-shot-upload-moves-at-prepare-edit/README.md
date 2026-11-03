# shot-upload-moves-at-prepare-edit

## 需求背景
补充镜头手动上传视频时，平台当场把素材盘上的同内容原文件挪进作品文件夹，用户以为原视频丢了；页面也看不出已上传。改成和其他素材一样到「准备剪辑」才挪，页面讲清楚。详见 proposal.md。

## 当前阶段
用户 2026-11-03「确认」；本地完成、验证通过（progress.md）。2026-11-03 已重启 api 和 worker，健康检查 200。2026-11-03 已归档、已提交（未推送）。

## 代码位置
apps/api/app/services/product_video.py；apps/web/src/product/ShotWork.tsx、ProductShotPanel.tsx

## 下一步
无（推送等用户说「推送」）。
