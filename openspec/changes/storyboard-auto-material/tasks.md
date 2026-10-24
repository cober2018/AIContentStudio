## 1. API

- [x] 1.1 `material_autofill.start`: shots run with `auto_fill`, rows without pick or bound material only.
- [x] 1.2 After search: accept eligible top candidates with licence rights; record auto source, score and reason.
- [x] 1.3 Template step: one model call over motion and gap rows; validate content; render; attach; record outcome.
- [x] 1.4 Skip rows picked by the user; never bind or save the master.
- [x] 1.5 Route `POST .../units/{u}/material-autofill` and MCP `start_material_autofill`.

## 2. Web

- [x] 2.1 分镜表: AI 补齐素材 button with progress; 素材 column shows 自动 source, 缺口 reason, or 已选.

## 3. Verify

- [x] 3.1 On a DB copy, run auto-fill for U80's draft: stock rows picked with licence and score; motion rows rendered from templates; gaps carry reasons; earlier picks untouched; master unchanged.
- [x] 3.2 Related API tests pass; web build passes.

## 4. Docs

- [x] 4.1 README, task_plan, progress, findings; root README entry.
