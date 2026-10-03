# FE-F6C Graphic Production Studio Design

## 1. Schema

New default schema: `graphic.master.v2`.

Payload:

```json
{
  "title": "string",
  "canvases": [
    {
      "id": "c1",
      "order": 0,
      "width": 1080,
      "height": 1440,
      "background": {"type":"solid","value":"#ffffff"},
      "layers": []
    }
  ],
  "variant_of": null
}
```

Layer types:
- `text`: stable id, order, x/y/w/h, text runs, font family token, weight, size, alignment, line-height, color
- `image`: exact `material_revision_id`, crop/fit/focal/opacity
- `chart`: exact chart MaterialRevision or deterministic chart spec that is rendered into a MaterialRevision before Candidate freeze
- `shape`: bounded primitive/background support only

No layer may contain local paths, arbitrary remote URLs or copied bytes.

## 2. Exact assets

Every image/chart MaterialRevision embedded in payload must have a matching ContentMasterAssetRef with exact content hash and project visibility. Repeated use is allowed but uses stable layer IDs and placement metadata.

## 3. Text is content

Text layers participate in:
- payload hash
- structured diff
- identity/fact/platform checks where applicable
- Candidate hash
- Review preview/diff

No renderer/publisher may silently substitute text after Approval.

## 4. Canvas presets

Channel/content-form profile may expose graphic presets such as:
- width/height/aspect
- maximum canvases
- cover requirement
- safe-area hints

Presets are suggestions/validation rules. Existing manually valid dimensions remain versioned content if allowed by the profile.

## 5. Rendering

F6C does not require a server raster engine to exist before editor completion.

Supported readiness paths:
1. verified renderer capability, or
2. explicit Studio/manual render attestation already supported by F6A.

A final render must cover every canvas exactly and bind to the canonical render-input hash. Changing any content/layer/ref invalidates the render.

## 6. AI image/search hooks

Graphic Studio may request:
- material search
- image generation
- image variation

The provider result itself is never embedded directly. Save/import creates a MaterialRevision with:
origin/source/provider/version/prompt/hash/rights/license metadata.
Only then may a layer reference it.

If provider capability is unavailable, UI shows unavailable; it does not fake success.

## 7. Checks

Required v2 graphic checks:
- master_schema
- evidence
- rights
- graphic_structure
- graphic_text_identity
- graphic_platform
- render

Optional profile-driven checks may be added by exact channel profile.

## 8. Diff

Compare:
- canvas add/remove/move/resize
- layer add/remove/move/change
- text changes
- exact asset changes
- evidence/context
- render changes

No fake text-similarity score for the whole graphic.

## 9. Frontend

Recommended files:
- `product/graphic/GraphicStudio.tsx`
- `GraphicCanvasStage.tsx`
- `GraphicCanvasList.tsx`
- `GraphicLayersPanel.tsx`
- `GraphicTextLayerEditor.tsx`
- `GraphicAssetPanel.tsx`
- `GraphicVariantPanel.tsx`
- `GraphicChecksPanel.tsx`
- `GraphicRevisionDiff.tsx`

Keep common Production/Workflow state independent.

## 10. Backend

Recommended files:
- `services/graphic_documents.py`
- `services/graphic_master_checks.py`
- `services/graphic_master_diff.py`
- optional `routers/graphic_production.py`

Modify:
- `production_modalities.py`
- `content_masters.py`
- Review projection/package code only through schema adapter boundaries.

## 11. Acceptance

Real browser chain:

`Graphic unit
→ create multiple canvases
→ add text/image/chart layers
→ reorder/resize
→ save v2
→ checks
→ bind exact final render(s)
→ Candidate v4
→ Review
→ Approval
→ local package`

All packaged bytes/hash/order must equal the approved Candidate.
