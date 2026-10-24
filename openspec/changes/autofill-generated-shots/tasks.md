## 1. Templates

- [x] 1.1 `photo-push` and `compare-pair` in `make_templates.py`; manifests; two checked renders each; previews.

## 2. Auto-fill

- [x] 2.1 Template choice sees image-slot templates and returns picture descriptions.
- [x] 2.2 Image step: generate (≤ 8 per run), accept as AI-generated material, render with images, attach as `ai_image`; proof rows tagged 非实拍.
- [x] 2.3 Web: 素材 column and slot show 「AI 示意」.

## 3. Verify

- [x] 3.1 On a DB copy, re-run auto-fill on U80's empty rows: the four earlier gaps get compare-pair or photo-push results, tagged as illustrations; picks and master untouched.
- [x] 3.2 Related API tests pass; web build passes.

## 4. Docs

- [x] 4.1 README, task_plan, progress, findings; ae-motion index; root README entry.
