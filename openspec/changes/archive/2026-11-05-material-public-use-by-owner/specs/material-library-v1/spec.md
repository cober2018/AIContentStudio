## ADDED Requirements

### Requirement: The owner can allow public use of their own upload

A user SHALL be able to mark a material revision they uploaded themselves (source_kind upload, created by that user, rights_status cleared, not revoked or archived) as allowed for public use from the material detail page, after one confirmation; the change SHALL be audited. Other revisions SHALL be refused with a reason. No MCP tool SHALL offer this, and existing derived materials SHALL keep the rights they were made with.

#### Scenario: Own logo made public
- **WHEN** the user marks their own uploaded logo revision 309 as public
- **THEN** 309 has public use allowed and an audit entry records who did it

#### Scenario: Not the owner's upload
- **WHEN** the revision is an AE render or was uploaded by someone else
- **THEN** the request is refused and nothing changes
