# Findings

## 2026-10-23
- U80 auto-fill gaps: best stock 0.45 / 0.40 / 0.20; no template for a UI transition or a 3D dive.
- Segments already carry a first-frame image prompt, and the platform already has image generation tasks with AI-generated provenance.
- A script that uses TestClient without its context manager skips app startup, so registered media adapters are not loaded (`adapter_not_loaded`). Use `with TestClient(app)`.
- The material route (purpose material_match → registered gemini-3.8-flash-high) currently fails with provider_request_failed on the live config too; its last success was 2026-10-22 10:19 UTC. Auto-fill then cannot judge stock or choose templates and falls back to pictures.
- Generated material re-enters later searches through the own library; the vision judge cannot tell an illustration from footage and may call it proof. Provenance (ai_generated, or rendered from ai_generated inputs) is what separates them.
