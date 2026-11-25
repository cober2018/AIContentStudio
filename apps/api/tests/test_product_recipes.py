"""Finished-video recipes: the library, the no-repeat rule, the 导演稿 field, frame grabs and the clip check."""

import shutil
import subprocess

import pytest
from fastapi import HTTPException

from app.models import ContentMasterRevision, ProductSku, ProductSkuWork, User
from app.services import product_recipes, product_video
from app.services.video_documents import VideoDocumentError, canonical_board, canonical_payload


def test_library_holds_all_recipes_with_platform_ids():
    recipes = product_recipes.catalog()
    assert len(recipes) == 391
    assert len({item["id"] for item in recipes}) == 391
    for item in recipes:
        assert 2 <= len(item["name"]) <= 8 and len(item["pitch"]) <= 30
        assert len(item["direction"]) <= 120 and len(item["make"]) <= 160 and len(item["check"]) <= 60
        assert set(item["needs"]) == {"proof", "person"}
        assert set(item["categories"]) <= {"beauty", "food", "home", "fashion", "tech"}
    fashion = [item for item in recipes if product_recipes.fits(item, "fashion")]
    assert len(fashion) == 50 + sum(1 for item in recipes if not item["categories"])


def _work(db, owner, unit_id, recipe=None, category="fashion"):
    link = ProductSkuWork(sku_id=1, sku_revision_id=1, project_id=1, unit_id=unit_id, settings_snapshot_json={"category": {"key": category}})
    db.add(link)
    if recipe:
        db.add(ContentMasterRevision(project_id=1, content_unit_id=unit_id, revision_no=1, modality="video", payload_schema="video.master.v2",
                                     payload_json={"recipe": {"id": recipe, "reason": ""}}, payload_hash="0" * 64, context_hash="0" * 64,
                                     source_kind="user_edit", idempotency_key=f"k{unit_id}", request_fingerprint="0" * 64))
    db.commit()
    return link


@pytest.fixture
def works(db_session):
    db_session.add(User(id=1, email="editor@studio.local", name="editor", role="editor"))
    db_session.add(ProductSku(id=1, owner_user_id=1, request_key="sku"))
    db_session.commit()
    fashion = [item["id"] for item in product_recipes.catalog() if "fashion" in item["categories"]]
    for unit_id, recipe in enumerate(fashion[:6], start=10):
        _work(db_session, 1, unit_id, recipe)
    _work(db_session, 1, 30, product_recipes.catalog()[0]["id"], category="food")
    return db_session, fashion, _work(db_session, 1, 99)


def test_recent_lists_the_five_latest_of_the_category(works):
    db, fashion, link = works
    assert [item["recipe_id"] for item in product_recipes.recent(db, link)] == list(reversed(fashion[1:6]))


def test_draft_must_name_a_fresh_fitting_recipe(works):
    db, fashion, link = works
    with pytest.raises(HTTPException) as missing:
        product_recipes.check_draft(db, link, {}, None)
    assert missing.value.detail["code"] == "product_recipe_required"
    with pytest.raises(HTTPException) as recent:
        product_recipes.check_draft(db, link, {"recipe": {"id": fashion[5]}}, None)
    assert recent.value.detail["code"] == "product_recipe_recent"
    # The sixth-latest one is free again.
    product_recipes.check_draft(db, link, {"recipe": {"id": fashion[0]}}, None)
    food_only = next(item["id"] for item in product_recipes.catalog() if item["categories"] == ["food"])
    with pytest.raises(HTTPException) as category:
        product_recipes.check_draft(db, link, {"recipe": {"id": food_only}}, None)
    assert category.value.detail["code"] == "product_recipe_category"


def test_the_users_pick_wins(works):
    db, fashion, link = works
    product_recipes.check_draft(db, link, {"recipe": {"id": fashion[5]}}, fashion[5])
    with pytest.raises(HTTPException) as other:
        product_recipes.check_draft(db, link, {"recipe": {"id": fashion[0]}}, fashion[5])
    assert other.value.detail["code"] == "product_recipe_not_chosen"


def test_listing_marks_recently_used(works):
    db, fashion, link = works
    listed = product_recipes.listing(db, link)
    used = {item["id"]: item.get("recently_used_by_unit") for item in listed["recipes"]}
    assert used[fashion[5]] == 15 and used[fashion[0]] is None
    assert product_recipes.listing(db, link, recipe_id=fashion[0])["recipe"]["make"]


def test_payload_keeps_recipe_and_footage_frame_source():
    payload = {
        "title": "短片", "aspect_ratio": [9, 16], "script": {"blocks": [{"id": "opening", "order": 0, "text": "开场"}]},
        "shots": [{"id": "shot-1", "order": 0, "label": "开场镜头", "duration_ms": 4_000, "script_block_id": "opening", "transition": "cut"}],
        "timeline": {"duration_ms": 4_000, "tracks": [{"id": "visual", "order": 0, "kind": "video",
                                                       "items": [{"id": "item-1", "order": 0, "shot_id": "shot-1", "start_ms": 0, "end_ms": 4_000}]}]},
        "voice": {"mode": "none"}, "subtitles": {"cues": []}, "overlays": [], "music": {}, "cover": {},
        "recipe": {"id": "abc-def", "reason": "素材少"}}
    assert canonical_payload(payload)["recipe"] == {"id": "abc-def", "reason": "素材少"}
    with pytest.raises(VideoDocumentError):
        canonical_payload({**payload, "recipe": {"id": "Bad_Id"}})
    assert canonical_board({"source_kind": "footage_frame"})["source_kind"] == "footage_frame"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_grab_converts_hlg_and_keeps_sdr(tmp_path):
    from PIL import Image

    sdr, hlg = tmp_path / "sdr.mp4", tmp_path / "hlg.mov"
    base = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x808080:s=320x240:d=1"]
    subprocess.run([*base, "-pix_fmt", "yuv420p", str(sdr)], check=True)
    subprocess.run([*base, "-pix_fmt", "yuv420p10le", "-c:v", "libx265", "-x265-params", "log-level=error",
                    "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", str(hlg)], check=True)
    import io

    with Image.open(io.BytesIO(product_video._grab(sdr, 500))) as picture:
        assert picture.size == (320, 240) and abs(picture.getpixel((10, 10))[0] - 128) <= 3
    with Image.open(io.BytesIO(product_video._grab(hlg, 500))) as picture:
        # The Apple SDR LUT changes HLG mid-grey; without it the frame would equal the raw code value.
        assert picture.size == (320, 240) and picture.getpixel((10, 10))[0] != 128
    with pytest.raises(HTTPException):
        product_video._grab(tmp_path / "missing.mp4", 0)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_clip_check_holds_middle_and_end_against_the_photo(tmp_path, monkeypatch):
    from app.services import shot_image

    clip = tmp_path / "clip.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=160x120:d=2", "-pix_fmt", "yuv420p", str(clip)], check=True)
    monkeypatch.setattr(product_video, "work", lambda db, unit_id: object())
    monkeypatch.setattr(product_video, "references", lambda db, user, unit_id: {"product": [7], "person": [], "scene": []})
    monkeypatch.setattr(product_video, "_image_bytes", lambda db, revision_id: b"photo")
    monkeypatch.setattr(shot_image, "to_png", lambda content: content)
    seen = []

    def check(photo, frame, absent_ok=False):
        seen.append(absent_ok)
        return {"pass": len(seen) == 1, "problems": [] if len(seen) == 1 else ["颜色变灰"]}

    monkeypatch.setattr(shot_image, "check", check)
    verdict = product_video._clip_check(None, None, 1, clip.read_bytes())
    assert seen == [True, True]
    assert verdict == {"pass": False, "problems": ["结尾：颜色变灰"]}
    monkeypatch.setattr(product_video, "work", lambda db, unit_id: None)
    assert product_video._clip_check(None, None, 1, clip.read_bytes()) is None


def test_saved_profile_round_trips_without_server_added_keys():
    # The page keeps the save response as its draft and sends it back on the next save (作品 132 got HTTP 422 on the second save).
    from app.routers.product_skus import ProfileIn, editable_settings
    stored = {"recipe": "three-reasons-list", "hook_pinned": "反差对比", "product_production_methods": {"video": {"schema": "x"}}}
    settings = editable_settings(stored)
    assert "product_production_methods" not in settings
    assert ProfileIn.model_validate({"expected_revision": 2, "settings": settings}).settings.recipe == "three-reasons-list"
