"""F6E exact published-profile and adapter capability boundary."""

import pytest

from app.models import ChannelTemplateVersion
from app.seed import seed_v1_channel_profiles
from app.services.channel_adapters import AdapterUnavailable, capability_for


@pytest.mark.parametrize(
    ("schema", "channel", "form", "artifact_kind", "executable"),
    [
        ("text.master.v2", "wechat", "article", "text", True),
        ("text.master.v2", "x", "thread", "text", True),
        ("text.master.v2", "x", "single", "text", True),
        ("graphic.master.v2", "xiaohongshu", "image_note", "image", False),
        ("video.master.v2", "douyin", "spoken_script", "script", False),
    ],
)
def test_first_batch_requires_exact_published_profile_and_only_implemented_adapter_executes(db_session, schema, channel, form, artifact_kind, executable):
    seed_v1_channel_profiles(db_session)
    db_session.commit()
    result = capability_for(db_session, schema, channel, form)
    assert result["supported_source"] is True
    assert result["profile_version_id"] is not None
    assert result["artifact_kind"] == artifact_kind
    assert result["configured"] is True
    assert result["executable"] is executable
    assert result["verified"] is False
    assert result["reason"] == (None if executable else "adapter_not_implemented")


@pytest.mark.parametrize(
    ("schema", "channel", "form"),
    [
        ("text.master.v1", "wechat", "article"),
        ("graphic.master.v2", "x", "single"),
        ("text.master.v2", "xiaohongshu", "image_note"),
        ("text.master.v2", "x_thread", "thread"),
    ],
)
def test_unsupported_source_or_legacy_target_fails_closed(db_session, schema, channel, form):
    seed_v1_channel_profiles(db_session)
    db_session.commit()
    result = capability_for(db_session, schema, channel, form)
    assert result["executable"] is False
    assert result["verified"] is False
    assert result["supported_source"] is False


def test_published_profile_artifact_kind_mismatch_fails_closed(db_session):
    seed_v1_channel_profiles(db_session)
    row = db_session.query(ChannelTemplateVersion).filter(ChannelTemplateVersion.channel == "xiaohongshu").one()
    row.profile_json = {"content_forms": {"image_note": {"artifact_kind": "text"}}}
    db_session.commit()
    with pytest.raises(AdapterUnavailable, match="artifact_kind_mismatch"):
        capability_for(db_session, "graphic.master.v2", "xiaohongshu", "image_note")
