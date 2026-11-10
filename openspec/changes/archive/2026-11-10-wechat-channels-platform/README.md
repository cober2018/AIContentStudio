# wechat-channels-platform

## 需求背景
「登记平台公开身份」下拉里没有视频号，角色绑不了视频号账号。详见 proposal.md。

## 当前阶段
2026-11-10 用户确认（收窄为只登记发布账号），已实现、测试、重启；未提交、未归档。

## 代码位置
apps/api/app/services/content_harness/channel_registry.py、routers/channels.py、services/content_identity.py；apps/web AccountDesk、IdentityWorkspace

## 下一步
用户在账号页登记视频号；说「提交吧」再归档提交。
