## 1. Foundation

- [x] 1.1 Tokens (CSS variables), Tailwind palette mapping, type stack, base styles.
- [x] 1.2 App shell and workflow navigation.
- [x] 1.3 Shared components (header, section, card, tabs, definition list, badges, fields, modal, drawer, empty/loading/error).
- [x] 1.4 Replace arbitrary hex colours with tokens.

## 2. 角色与账号

- [x] 2.1 Directories (persona, account, series, brand) as editorial index cards.
- [x] 2.2 Detail header, tabs and overview with readable profile and creative configuration.
- [x] 2.3 Edit, history, creative configuration, relations, workflow, memory, publisher tabs.
- [x] 2.4 Account detail and series targets.

## 3. Main pages

- [x] 3.1 Home. - [x] 3.2 Opportunities. - [x] 3.3 Projects and project page. - [x] 3.4 Production workbench (header, stepper, step header, assistant pill). - [x] 3.5 Review & delivery (list grouped by project, tabs). - [x] 3.6 Assets & knowledge (header, tabs, list). - [x] 3.7 Learning (header, tabs, empty lists). - [x] 3.8 Settings.

## 4. Verify

- [ ] 4.1 Screenshot review loop at 1440 and 390 for every redesigned page; record issues fixed.
- [x] 4.2 `npm run build` (types + bundle check) and frontend model tests.

## Verification record (2026-10-21)

- Screenshot loop at 1440×900 for identities (directory, persona overview, account overview, creative, memory), home, projects, project page, production, review, assets, learning, opportunities, settings; phone width checked on persona overview (no horizontal overflow).
- Issues found and fixed in the loop: double rule and scrollbar under tabs; full-width select; duplicated positioning; dense reference-style paragraph → numbered list; narrow creative cards overlapping; machine preset names; display-font digits; grey empty grid cell; account page not saying the profile is inherited; English eyebrows and statuses; vertical wrapping status chip; raw ISO times; IDs instead of project names; floating assistant covering fields; wide label tracking on Chinese.
- `npm run build` passes (types + bundle gate); `node --test tests/*.test.mjs` 37/37.
- Open: 4.1 continues for deep panels (stage results, creative execution, candidate preview, delivery forms) which inherit tokens but keep their old layouts.
