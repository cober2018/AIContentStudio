## ADDED Requirements

### Requirement: Video workflows end at 导演稿

New video workflows SHALL have only the 导演稿 stage. The product video default and the persona video defaults SHALL move to this definition; existing runs SHALL keep their stages.

#### Scenario: New video work
- **WHEN** a new video work starts from a persona or product default
- **THEN** its flow shows 导演稿 only

### Requirement: The old stage is hidden in existing runs

For runs that still contain 专业执行准备, the step list, the 内容方案 summary and 准备剪辑 SHALL ignore it.

#### Scenario: 海底光缆
- **WHEN** the user opens 海底光缆
- **THEN** the step list shows no 专业执行准备 and no 「需要处理」 for it, and 准备剪辑 does not rebuild it
