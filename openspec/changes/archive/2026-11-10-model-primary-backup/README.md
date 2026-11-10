# model-primary-backup

## 需求背景
每个用途只能挂一个模型，主模型没额度就整步失败。改成主、备两个模型。详见 proposal.md。

## 当前阶段
2026-11-10 已实现、测试、重启、按主备配好、归档并提交。

## 代码位置
apps/api/app/services/generation/providers.py、model_registration.py、生图入口；apps/web/src/product/ModelRoutingSettings.tsx

## 下一步
用户确认后实现。
