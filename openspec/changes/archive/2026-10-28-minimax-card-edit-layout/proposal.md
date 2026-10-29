# MiniMax 卡片改成和其他厂商一样的「编辑」版式

## Why

厂商与模型里，CPA 等厂商默认只显示概要，点「编辑」才展开表单；MiniMax 卡片却把 Key、地址、区域、测试全部平铺，两套版式不一致，看着乱。

## What Changes

- MiniMax 卡片默认只显示 logo、名称、状态和概要行，右侧「编辑」「测试」两个按钮，与 CPA 卡片一致。
- 点「编辑」在卡片下方展开灰底编辑区：带标签的 API Key、访问地址、区域字段，加「启用」「清除本页保存的密钥」两个勾选框，一个「保存」按钮一次保存所有改动。
- 后端接口和数据不变。

## 不做

改后端、改测试逻辑、改其他厂商卡片。

## Impact

- `apps/web/src/product/ModelRegistrationSettings.tsx`：`MiniMaxVendorCard`。
