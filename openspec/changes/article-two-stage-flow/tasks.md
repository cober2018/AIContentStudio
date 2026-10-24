## 1. Definition and schema

- [x] 1.1 `article.plan.v1` artifact schema (angle, facts, unknowns, outline).
- [x] 1.2 Text definition: 写作方案 (creative, 2–3 candidates, three methods) → 成稿 (master, three methods, alternative titles) → 质量检查.

## 2. Automatic check

- [x] 2.1 Start the check stage after 成稿 is accepted; show 需要处理 on failure.

## 3. Verify

- [x] 3.1 On a DB copy: a new article workflow has three stages; 写作方案 returns 2–3 plans; 成稿 returns a full article; the check runs by itself.
- [x] 3.2 Related API tests pass; web build passes.

## 4. Persona workflows and docs

- [x] 4.1 After the user's go-ahead, move persona 2 and 3 text defaults to the new definition.
- [x] 4.2 README, task_plan, progress, findings; root README entry.
