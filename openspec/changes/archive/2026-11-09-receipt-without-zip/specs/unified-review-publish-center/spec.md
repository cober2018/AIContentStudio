## ADDED Requirements

### Requirement: Manual receipt does not require the ZIP download
复制包类目标（action 为 copy_package）在「已授权」时 SHALL 允许回填人工回执，不要求先下载成品包 ZIP；自动推送类目标在未执行推送时 SHALL NOT 允许回填；已撤销或需核对的目标规则不变。

#### Scenario: Published from the output folder
- **WHEN** 用户用「打开成果文件夹」里的成片发到头条，回到目标 #10 填入链接
- **THEN** 「回填人工回执」可点，保存后目标变为人工已确认

#### Scenario: Official draft target not pushed yet
- **WHEN** 公众号自动推草稿的目标还没推过
- **THEN** 不能回填，仍需先推到草稿箱
