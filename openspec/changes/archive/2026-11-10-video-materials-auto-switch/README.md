# video-materials-auto-switch

## 需求背景
素材这一站加「手动 / 自动」开关。详见 proposal.md。

## 当前阶段
2026-11-10 已实现、本地验证、重启、归档并提交；页面实测待用户切一次开关。

## 代码位置
apps/api/app/services/video_chain.py、product_video.py、creative_mcp.py、routers/edit_agent.py；apps/web/src/product（VideoChainPanel、ShotWork）

## 下一步
第三方模型重连 /mcp；用户在页面上切一次开关看看；说「提交吧」后归档并提交。
