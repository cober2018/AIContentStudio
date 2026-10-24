# 商品业务域解耦工程验收

## PRD / 范围
SKU商品制作独立于角色，底层共用，历史保全。

## 目录结构
formal-migration.json为旧字段指纹与迁移结果；formal-api.json为正式API/关键历史回读；candidate-api.json为复制库；zero-persona-chain.log为mock链；formal-ui-readback.log为只读页面；implementation-scope.json为58文件边界。

## 已完成
第8节8项通过，本机启用。回归范围重叠，数字不累加。

## TODO
原真实素材和新成片质量待验，不以mock证明商业质量。

## 关键决策
新产品不创建Identity；历史只读用冻结上下文；未明确关联SKU不迁移；公开权限保持。

## 依赖与启动
既有8000/5173与launchd API/Worker；备份位置见同change README。无新服务。
