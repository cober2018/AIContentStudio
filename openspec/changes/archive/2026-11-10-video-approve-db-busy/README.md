# video-approve-db-busy

## 需求背景
2026-11-10 作品107 点「成片通过」时数据库被后台任务占着写，通过被拒，页面停在「正在通过…」。详见 proposal.md。

## 当前阶段
2026-11-10 已实现、验证、重启 api，已提交并归档（规范已并入 openspec/specs/video-chain-led-by-mcp-model）。

## 代码位置
apps/api/app/routers/edit_agent.py、services/maintenance.py、services/project_authorization.py；apps/web/src/product/VideoChainPanel.tsx

## 下一步
无。下次用户点通过时留意页面提示和按钮是否正常恢复（浏览器里还没实际点过）。备注：search_promotion.py、search_runner.py、video_chain.py 现在有别的需求未提交的改动，动之前先看清楚、分开提交。
