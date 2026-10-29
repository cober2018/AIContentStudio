"""Render the library preview clip of each template and record it in the manifest.

Usage: python3 make_previews.py <store> [template-id ...] [--aspect 9:16|16:9]
Each preview uses the template's sample content (SAMPLES in make_templates.py) and sample pictures from
<store>/_samples/, renders through aerender without touching the running After Effects, puts overlay templates
over a sample picture, and writes preview-9x16.mp4 / preview-16x9.mp4 beside the project.
"""
import html
import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_templates import SAMPLES, VERSIONS  # noqa: E402

AERENDER = "/Applications/Adobe After Effects 2026/aerender"
MANIFESTS = Path(__file__).resolve().parent.parent / "templates"
DATA = re.compile(r"/\*AICS_DATA\*/.*?/\*AICS_END\*/", re.S)
# Slot file -> sample picture; per-template entries override the defaults.
DEFAULT_PICTURES = {"image.png": "doc.jpg", "host.png": "host.jpg", "graphic.png": "chart.png", "map.png": "map.png", "avatar.png": "avatar.jpg"}
PICTURES = {
    "line-carry": {"image.png": "desk-flat.jpg"}, "split-6040": {"image.png": "typing.jpg"},
    "slider-compare": {"before.png": "land-before.jpg", "after.png": "land-after.jpg"}, "before-after-scrub": {"after.png": "dash.png"},
    "news-desk": {"image1.png": "news1.png", "image2.png": "news2.png"},
    "layout-relay": {"image1.png": "camera-a.jpg", "image2.png": "camera-b.jpg", "image3.png": "typing.jpg"},
    "grid-hero": {"image1.png": "land-after.jpg", "image2.png": "desk-flat.jpg", "image3.png": "camera-a.jpg", "image4.png": "waves.jpg"},
    "echo-bed": {"image.png": "waves.jpg"}, "color-slam": {"image.png": "dash.png"},
    "host-parallel": {"img1.png": "camera-a.jpg", "img2.png": "land-after.jpg", "img3.png": "typing.jpg"},
    "product-hero": {"product.png": "prod-product.jpg"}, "selling-points": {"product.png": "prod-product.jpg"}, "spec-table": {"product.png": "prod-product.jpg"},
    "dimension-mark": {"product.png": "prod-product.jpg"}, "buy-cta": {"product.png": "prod-product.jpg"}, "cert-card": {"cert.png": "prod-cert.png"},
    "product-angles": {"img1.png": "prod-product.jpg", "img2.png": "prod-angle2.jpg", "img3.png": "prod-angle3.jpg"},
    "use-steps": {"img1.png": "prod-product.jpg", "img2.png": "prod-step1.jpg", "img3.png": "prod-step2.jpg"},
    "color-swatch": {"img1.png": "prod-product.jpg", "img2.png": "prod-color2.jpg", "img3.png": "prod-color3.jpg"},
}
SIZES = {"9:16": (1080, 1920), "16:9": (1920, 1080)}


def ff(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def preview(store: Path, tid: str, aspect: str) -> str:
    mf = MANIFESTS / tid / VERSIONS.get(tid, "v1") / "manifest.json"
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    folder = store / tid / manifest["version"]
    project = manifest["project"] if aspect == "9:16" else (manifest.get("variants") or {}).get(aspect, {}).get("project")
    if not project or not (folder / project["file"]).is_file():
        return f"{tid} {aspect}: no project"
    samples = store / "_samples"
    data = dict(SAMPLES.get(tid, {}))
    data.setdefault("_images", [])
    data["_duration_ms"] = manifest["duration_ms"]["default"]
    job = store.parent / "ae-jobs" / uuid.uuid4().hex
    job.mkdir(parents=True)
    try:
        pictures = {**DEFAULT_PICTURES, **PICTURES.get(tid, {})}
        if aspect == "16:9":
            # A landscape film comes with a landscape map, so relative pin coordinates still land on it.
            pictures["map.png"] = "map-16x9.png"
        for item in folder.iterdir():
            if item.suffix != ".png":
                continue
            sample = samples / pictures[item.name] if item.name in pictures else None
            if sample is not None and sample.is_file():
                # AE reads footage by extension, so every sample picture becomes the PNG the project expects.
                ff("-i", str(sample), "-vf", "scale='min(2000,iw)':-2", str(job / item.name))
            else:
                shutil.copyfile(item, job / item.name)
        xml = (folder / project["file"]).read_text(encoding="utf-8").replace(str(folder), str(job))
        xml = DATA.sub(lambda _: "/*AICS_DATA*/" + html.escape(json.dumps(data, ensure_ascii=False), quote=False) + "/*AICS_END*/", xml)
        (job / "job.aepx").write_text(xml, encoding="utf-8")
        alpha = manifest.get("alpha") is True
        out = job / ("out.mov" if alpha else "out.mp4")
        frames = round(data["_duration_ms"] * manifest["fps"] / 1000)
        done = subprocess.run([AERENDER, "-project", str(job / "job.aepx"), *(["-rqindex", "1"] if alpha else ["-comp", manifest["comp"]]),
                               "-s", "0", "-e", str(frames - 1), "-output", str(out)], capture_output=True, text=True, timeout=900)
        if not out.is_file():
            return f"{tid} {aspect}: render failed {(done.stdout + done.stderr)[-300:]}"
        name = f"preview-{aspect.replace(':', 'x')}.mp4"
        w, h = SIZES[aspect]
        if alpha:
            ff("-i", str(samples / "host.jpg"), "-i", str(out), "-filter_complex",
               f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},loop=-1:1:0,fps=30[bg];[bg][1:v]overlay=0:0:shortest=1,format=yuv420p",
               "-c:v", "libx264", "-crf", "22", "-movflags", "+faststart", str(folder / name))
        else:
            ff("-i", str(out), "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(folder / name))
        manifest["previews"] = {**(manifest.get("previews") or {}), aspect: name}
        mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return f"{tid} {aspect}: {name}"
    finally:
        shutil.rmtree(job, ignore_errors=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    aspect = "9:16"
    if "--aspect" in args:
        i = args.index("--aspect")
        aspect = args[i + 1]
        del args[i:i + 2]
    store = Path(args[0]).expanduser()
    ids = args[1:] or sorted(SAMPLES)
    for tid in ids:
        print(preview(store, tid, aspect), flush=True)
