## ADDED Requirements

### Requirement: The persona is chosen per work when creating it

The product video workbench SHALL NOT show a page-wide persona selector. Every action that creates a product video work SHALL first ask which persona this work uses (required) and create the work only after one is chosen.

#### Scenario: New video for a product
- **WHEN** the user clicks 为此商品新建视频 on 敏贝贝薯乐酥
- **THEN** a dialog asks for the work's persona, and the work is created with the chosen persona after 开始制作
