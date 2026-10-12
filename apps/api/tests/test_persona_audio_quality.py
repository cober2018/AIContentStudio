"""Task 18.8: local WAV/receipt contract evidence, not real TTS or speech-quality acceptance."""

import hashlib
import io
import json
import socket
import struct
import subprocess
import uuid
import wave
from copy import deepcopy
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import event, select

from app.config import get_settings
from app.models import (
    ContentMasterAssetRef,
    ContentMasterRevision,
    ContentPersona,
    ContentProject,
    ContentUnit,
    Material,
    MaterialRevision,
    ProviderGenerationTask,
    SystemSetting,
    User,
)
from app.services import (
    asr_suggestions,
    asset_media,
    audio_quality,
    generation_tasks,
    local_mlx_asr_provider,
    material_storage,
    minimax_cli_provider,
    model_capability_routing,
    provider_calls,
    stage_audio,
    stage_audio_asr,
    studio_creative_catalog,
)
from app.services.creative_artifacts import validate_artifact
from app.services.stage_contracts import digest
from app.services.stage_invocations import StageInvocationError


@pytest.fixture(autouse=True)
def offline_audio(monkeypatch, tmp_path):
    for key, value in {
        "APP_ENV": "test", "DATABASE_URL": "sqlite://", "LLM_PROVIDER": "mock",
        "LLM_API_KEY": "", "LLM_BASE_URL": "", "MATERIAL_STORAGE_BACKEND": "local",
        "MINIO_ENABLED": "false", "TASK_QUEUE_ENABLED": "false",
        "AICS_ENABLE_MINIMAX_CLI": "0", "AICS_ENABLE_NATIVE_MODEL_ADAPTERS": "0",
        "AICS_ENABLE_LOCAL_MLX_ASR": "false", "AICS_MLX_ASR_PYTHON": "",
        "AICS_MLX_ASR_WORKER": "", "AICS_MLX_ASR_MODEL_DIR": "",
        "AI_STUDIO_MEDIA_ROOT": str(tmp_path), "AICS_GENERATION_RECEIPT_KEY_ID": "audio-fixture",
        "AICS_GENERATION_RECEIPT_KEYS": json.dumps({"audio-fixture": "12" * 32}),
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(asset_media, "MEDIA_ROOT", tmp_path)
    get_settings.cache_clear()
    calls = []

    def forbidden(*args, **kwargs):
        calls.append("external execution")
        # pytest.fail is not caught by QC's fail-closed Exception handler.
        pytest.fail("Audio QC must not use network, providers, subprocesses or ASR inference")

    for target, name in (
        (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket, "create_connection"),
        (socket, "getaddrinfo"), (httpx.Client, "request"), (httpx.AsyncClient, "request"),
        (subprocess, "Popen"), (provider_calls, "call"), (generation_tasks, "execute"),
        (generation_tasks, "recover"), (asr_suggestions, "suggest"), (stage_audio_asr, "execute_asr"),
        (local_mlx_asr_provider.LocalMLXASRProvider, "transcribe"), (local_mlx_asr_provider, "_run"),
        (minimax_cli_provider, "_run"), (minimax_cli_provider, "_run_bounded"),
    ):
        monkeypatch.setattr(target, name, forbidden)
    try:
        yield calls
        assert calls == []
    finally:
        get_settings.cache_clear()


@pytest.fixture(params=["studio.quality.audio.explainer@1", "studio.quality.audio.conversational@1"])
def quality_profile(request):
    return request.param


def _wav(samples=None, *, frames=8000, rate=8000, channels=1):
    if samples is None:
        samples = [8192 if index % 2 else -8192 for index in range(frames * channels)]
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buffer.getvalue()


def _seal(task):
    task.plan_hash = generation_tasks._hash(task.plan_json)
    task.request_hash = generation_tasks._hash({
        "request": task.request_json, "plan": task.plan_json, "sources": task.source_refs_json,
    })
    task.receipt_signature = generation_tasks._sign(task, generation_tasks._receipt(task))
    task.result_signature = generation_tasks._sign(task, generation_tasks._result_receipt(task))


@pytest.fixture
def audio_case(db_session, offline_audio, tmp_path):
    def create(content=None, *, mime="audio/wav", seconds=2, parameters=None):
        content = _wav() if content is None else content
        user = User(email=f"audio-{uuid.uuid4().hex}@studio.test", name="Audio fixture")
        db_session.add(user)
        db_session.flush()
        project = ContentProject(owner_user_id=user.id, title="Audio QC fixture")
        material = Material(kind="audio", title="Synthetic WAV", created_by=user.email)
        db_session.add_all([project, material])
        db_session.flush()
        digest = hashlib.sha256(content).hexdigest()
        key = f"material/{digest[:2]}/{digest}.wav"
        material_storage.provider().put(key, content)
        revision = MaterialRevision(
            material_id=material.id, status="usable", source_kind="ai_generated",
            content_hash=digest, file_path=key, mime_type=mime, duration_ms=999,
            rights_status="cleared", public_use_allowed=True, model_use_allowed=True,
            commercial_use_allowed=True, provider_key="minimax.cli", provider_version="1",
        )
        db_session.add(revision)
        db_session.flush()
        binding = model_capability_routing.Binding.model_validate({
            "adapter_key": "minimax.cli", "adapter_version": "1", "model_id": "speech-02-hd",
            "base_url": "local://mmx", "credential_ref": "AUDIO_FIXTURE_CREDENTIAL",
        }).model_dump(mode="json")
        request = {
            "capability": "tts", "selected_profile": "fixture.tts", "prompt": "你好，今天聊聊本地音频。",
            "parameters": {"seconds": seconds, **({"voice_id": "fixture_voice", "rate": 1.0}
                                                   if parameters is None else parameters)},
        }
        input_hash = generation_tasks._hash({"request": request, "sources": [], "actor": user.id})
        plan = {
            "required_capability": "tts", "status": "ready", "dispatch_ready": True,
            "selected_profile": "fixture.tts", "execution_profile": "fixture.tts",
            "adapter_key": "minimax.cli", "adapter_version": "1", "model_id": binding["model_id"],
            "binding_hash": generation_tasks._hash(binding), "input_hash": input_hash,
            "runtime_hash": "a" * 64, "source_refs": [], "parameters": deepcopy(request["parameters"]),
        }
        task_id = uuid.uuid4().hex
        result_key = f"generation/{task_id}/{digest}.bin"
        material_storage.provider().put(result_key, content)
        task = ProviderGenerationTask(
            id=task_id, owner_user_id=user.id, project_id=project.id, idempotency_key=task_id,
            state="accepted", request_json=request, plan_json=plan, source_refs_json=[],
            provider_kind="tts_provider", provider_key="minimax.cli", provider_version="1",
            model_id=binding["model_id"], protocol_version="minimax.tts.fixture.v1",
            runtime_hash=plan["runtime_hash"], credential_epoch="b" * 64, input_hash=input_hash,
            receipt_key_id="audio-fixture", result_hash=digest, result_size=len(content), result_mime=mime,
            result_storage_key=result_key, accepted_material_revision_id=revision.id,
            acceptance_hash=generation_tasks._hash({"rights_status": "cleared", "public_use_allowed": True}),
        )
        _seal(task)
        revision.source_metadata_json = {
            "provider_kind": task.provider_kind, "runtime_hash": task.runtime_hash,
            "input_hash": input_hash, "source_refs": [],
            "tts_applied_parameters": generation_tasks.tts_applied_parameters(task),
        }
        setting = db_session.get(SystemSetting, "models")
        configuration = {"profiles": {"fixture.tts": {
            "enabled": True, "declared_capabilities": ["tts"], "capability_bindings": {"tts": binding},
        }}}
        if setting is None:
            db_session.add(SystemSetting(key="models", value=configuration))
        else:
            setting.value = configuration
        db_session.add(task)
        db_session.commit()
        return SimpleNamespace(db=db_session, user=user, project=project, material=material,
                               revision=revision, task=task, content=content, path=tmp_path / key)
    return create


def _check(case, profile, **kwargs):
    return audio_quality.check_audio(case.db, case.revision, quality_profile_ref=profile, **kwargs)


def _issue(report, severity, code):
    assert {"severity": severity, "code": code} in report["issues"], report
    assert report["status"] == severity, report
    assert report["coverage"]["complete"] is (severity == "warning")


def _snapshot(case):
    tables = [User, ContentProject, ContentPersona, ContentUnit, Material, MaterialRevision,
              ProviderGenerationTask, SystemSetting, ContentMasterRevision, ContentMasterAssetRef]
    with case.db.no_autoflush:
        rows = {model.__tablename__: [deepcopy(dict(row)) for row in case.db.execute(
            select(model.__table__).order_by(*model.__table__.primary_key)).mappings()] for model in tables}
    files = {str(path.relative_to(asset_media.MEDIA_ROOT)): path.read_bytes()
             for path in asset_media.MEDIA_ROOT.rglob("*") if path.is_file()}
    return rows, files


def test_exact_wav_and_signed_receipt_pass_without_mutating_inputs(audio_case, quality_profile, offline_audio):
    case = audio_case()
    generation_tasks._verify(case.task)
    before = _snapshot(case)
    statements = []

    def record(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(case.db.get_bind(), "before_cursor_execute", record)
    try:
        report = _check(case, quality_profile)
        frozen = deepcopy(report)
        case.material.title = "Pending caller edit"
        case.revision.duration_ms = 123456
        assert _check(case, quality_profile, task=case.task) == frozen
        assert case.material in case.db.dirty and case.revision in case.db.dirty
    finally:
        event.remove(case.db.get_bind(), "before_cursor_execute", record)
    assert report["status"] == "pass", report
    assert report["issues"] == []
    assert report["material_revision_id"] == case.revision.id
    assert report["content_hash"] == hashlib.sha256(case.content).hexdigest()
    assert report["quality_profile_ref"] == quality_profile
    assert report["quality_profile_hash"] == studio_creative_catalog.digest(
        studio_creative_catalog.QUALITY[quality_profile])
    assert report["rules_hash"] == generation_tasks._hash(report["thresholds"])
    assert report["measured"]["duration_ms"] == 1000
    assert report["measured"]["rms_dbfs"] == pytest.approx(-12.041, abs=0.001)
    assert report["measured"]["clipping_ratio"] == report["measured"]["silence_ratio"] == 0
    assert report["coverage"]["waveform"] == "wave"
    assert report["coverage"]["bytes_hash"] == "verified_live_bytes"
    assert report["coverage"]["current_binding"] == "verified"
    assert report["coverage"]["provider_model"] == "verified_receipt"
    assert report["coverage"]["voice_rate"] == "verified_signed_result_and_material_receipt"
    assert report["task"]["tts_applied_parameters"] == case.revision.source_metadata_json["tts_applied_parameters"]
    assert report["human_review_required"] is True
    assert report["coverage"]["loudness"] == "rms_dbfs_only_lufs_not_measured"
    assert report["coverage"]["asr_alignment"] == "not_run"
    assert report["coverage"]["perceptual_quality"] == "human_review_required"
    assert statements and all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    assert _snapshot(case) == before
    assert report == frozen and offline_audio == []


@pytest.mark.parametrize("frames,seconds,code", [
    (0, 2, "audio_duration_out_of_bounds"),
    (8001, 1, "audio_requested_duration_exceeded"),
    (601, 600, "audio_duration_out_of_bounds"),
])
def test_duration_uses_real_frames_and_enforces_bounds(audio_case, quality_profile, frames, seconds, code):
    case = audio_case(_wav(frames=frames, rate=1 if frames == 601 else 8000), seconds=seconds)
    report = _check(case, quality_profile)
    _issue(report, "blocker", code)
    assert report["measured"]["duration_ms"] == frames * 1000 / (1 if frames == 601 else 8000)


def test_exact_requested_duration_is_allowed(audio_case, quality_profile):
    report = _check(audio_case(seconds=1), quality_profile)
    assert report["status"] == "pass", report
    assert report["measured"]["duration_ms"] == 1000


@pytest.mark.parametrize("samples,code,severity", [
    ([0] * 8000, "audio_silent", "blocker"),
    ([32767] * 80 + [8192] * 7920, "audio_gross_clipping", "blocker"),
    ([32767] * 8 + [8192] * 7992, "audio_clipping", "warning"),
    ([0] * 7200 + [8192] * 800, "audio_excessive_silence", "warning"),
    ([64] * 8000, "audio_rms_outside_bounds", "warning"),
    ([20000] * 8000, "audio_rms_outside_bounds", "warning"),
], ids=["silent", "clipping-blocker-boundary", "clipping-warning-boundary", "mostly-silent", "quiet", "loud"])
def test_waveform_thresholds_are_measured_from_pcm(audio_case, quality_profile, samples, code, severity):
    case = audio_case(_wav(samples))
    before = _snapshot(case)
    report = _check(case, quality_profile)
    _issue(report, severity, code)
    assert report["measured"]["duration_ms"] == 1000
    assert report["measured"]["clipping_ratio"] == sum(sample == 32767 for sample in samples) / len(samples)
    assert report["measured"]["silence_ratio"] == samples.count(0) / len(samples)
    assert _snapshot(case) == before


def test_long_edge_silence_warns(audio_case, quality_profile):
    case = audio_case(_wav([0] * 16008 + [8192] * 8000 + [0] * 16008), seconds=6)
    report = _check(case, quality_profile)
    _issue(report, "warning", "audio_excessive_silence")
    assert report["measured"]["leading_silence_ms"] == report["measured"]["trailing_silence_ms"] == 2001


def test_opposite_phase_stereo_is_not_mistaken_for_silence(audio_case, quality_profile):
    report = _check(audio_case(_wav([8192, -8192] * 8000, channels=2)), quality_profile)
    assert report["status"] == "pass", report
    assert report["measured"]["channels"] == 2
    assert report["measured"]["silence_ratio"] == 0


@pytest.mark.parametrize("content,mime,severity,code", [
    (_wav(), "text/plain", "incomplete", "audio_mime_unsupported"),
    (b"not a WAV", "audio/wav", "blocker", "audio_mime_mismatch"),
    (b"RIFF\x00\x00\x00\x00WAVE", "audio/wav", "blocker", "audio_decode_invalid"),
    (_wav()[:-2], "audio/wav", "blocker", "audio_truncated_frames"),
], ids=["unsupported-mime", "wrong-mime", "corrupt-riff", "truncated-frames"])
def test_invalid_mime_and_corrupt_bytes_fail_closed(audio_case, quality_profile, content, mime, severity, code):
    case = audio_case(content, mime=mime)
    before = _snapshot(case)
    report = _check(case, quality_profile)
    _issue(report, severity, code)
    assert report["coverage"]["bytes_hash"] == "verified_live_bytes"
    assert report["coverage"]["waveform"] == "not_run"
    assert _snapshot(case) == before


def test_changed_local_bytes_invalidate_prior_snapshot(audio_case, quality_profile):
    case = audio_case()
    frozen = deepcopy(_check(case, quality_profile))
    assert frozen["status"] == "pass"
    case.path.write_bytes(_wav([4096] * 8000))
    _issue(_check(case, quality_profile), "blocker", "audio_live_bytes_unavailable_or_changed")
    assert frozen["status"] == "pass" and frozen["content_hash"] == case.revision.content_hash


@pytest.mark.parametrize("target,status", [("material", "archived"), ("revision", "revoked")])
def test_revocation_blocks_recheck_without_rewriting_old_result(audio_case, quality_profile, target, status):
    case = audio_case()
    frozen = deepcopy(_check(case, quality_profile))
    assert frozen["status"] == "pass"
    getattr(case, target).status = status
    case.db.commit()
    _issue(_check(case, quality_profile), "blocker", "audio_revision_changed_or_revoked")
    assert frozen["status"] == "pass" and frozen["issues"] == []


@pytest.mark.parametrize("field,value", [
    ("provider_key", "other.provider"), ("provider_version", "2"),
])
def test_material_provider_must_match_signed_task(audio_case, quality_profile, field, value):
    case = audio_case()
    setattr(case.revision, field, value)
    case.db.commit()
    _issue(_check(case, quality_profile), "blocker", "audio_provenance_mismatch")


@pytest.mark.parametrize("field,value", [("voice_id", "another_voice"), ("rate", 1.25)])
def test_material_voice_and_rate_must_match_signed_result(audio_case, quality_profile, field, value):
    case = audio_case()
    metadata = deepcopy(case.revision.source_metadata_json)
    metadata["tts_applied_parameters"][field] = value
    case.revision.source_metadata_json = metadata
    case.db.commit()
    _issue(_check(case, quality_profile), "blocker", "audio_applied_voice_rate_mismatch")


@pytest.mark.parametrize("field,value", [("voice_id", "another_voice"), ("rate", 1.25)])
def test_tampered_planned_voice_or_rate_cannot_reuse_receipt(audio_case, quality_profile, field, value):
    case = audio_case()
    plan = deepcopy(case.task.plan_json)
    plan["parameters"][field] = value
    case.task.plan_json = plan
    case.db.commit()
    _issue(_check(case, quality_profile), "blocker", "audio_task_receipt_invalid")


@pytest.mark.parametrize("field,value", [
    ("result_hash", "c" * 64), ("result_mime", "audio/mpeg"), ("result_size", 1),
    ("state", "result_ready"),
])
def test_accepted_task_must_bind_exact_hash_mime_size_and_state(audio_case, quality_profile, field, value):
    case = audio_case()
    setattr(case.task, field, value)
    case.db.commit()
    _issue(_check(case, quality_profile), "blocker", "audio_accepted_task_mismatch")


@pytest.mark.parametrize("field", ["receipt_signature", "result_signature"])
def test_signed_request_and_result_receipts_cannot_be_forged(audio_case, quality_profile, field):
    case = audio_case()
    setattr(case.task, field, "0" * 64)
    case.db.commit()
    _issue(_check(case, quality_profile), "blocker", "audio_task_receipt_invalid")


def test_missing_receipt_key_is_incomplete_not_pass(audio_case, quality_profile, monkeypatch):
    case = audio_case()
    monkeypatch.setenv("AICS_GENERATION_RECEIPT_KEYS", "{}")
    _issue(_check(case, quality_profile), "incomplete", "audio_receipt_key_unavailable")


def test_legacy_task_without_applied_voice_rate_is_incomplete(audio_case, quality_profile):
    case = audio_case(parameters={})
    report = _check(case, quality_profile)
    _issue(report, "incomplete", "audio_applied_voice_rate_unavailable")
    assert report["coverage"]["voice_rate"] == "applied_parameters_not_recorded"


def test_current_model_binding_change_invalidates_receipt(audio_case, quality_profile):
    case = audio_case()
    setting = case.db.get(SystemSetting, "models")
    configuration = deepcopy(setting.value)
    configuration["profiles"]["fixture.tts"]["capability_bindings"]["tts"]["model_id"] = "speech-02-turbo"
    setting.value = configuration
    case.db.commit()
    _issue(_check(case, quality_profile), "blocker", "audio_current_binding_changed")


def test_unaccepted_audio_has_waveform_coverage_but_no_provider_proof(audio_case, quality_profile):
    case = audio_case()
    case.db.delete(case.task)
    case.db.commit()
    report = _check(case, quality_profile)
    _issue(report, "incomplete", "audio_accepted_task_unavailable")
    assert report["coverage"]["waveform"] == "wave"
    assert report["coverage"]["provider_model"] == "not_run"


def test_estimated_srt_has_explicit_labels_and_no_alignment_proof(audio_case, quality_profile, offline_audio):
    case = audio_case()
    before = _snapshot(case)
    report = _check(case, quality_profile, script=case.task.request_json["prompt"],
                    alignment={"enabled": False, "srt_mode": "estimated"})
    _issue(report, "warning", "audio_subtitles_estimated_not_asr")
    subtitles = report["subtitles"]
    assert subtitles["mode"] == "estimated" and subtitles["estimated"] is True
    assert subtitles["filename"] == "audio-estimated.srt"
    assert subtitles["timing_basis"] == "script_character_weighted_estimate"
    assert "[ESTIMATED / 估算；非ASR时轴]" in subtitles["srt"]
    assert "00:00:00,000 --> 00:00:01,000" in subtitles["srt"]
    assert subtitles["srt_hash"] == hashlib.sha256(subtitles["srt"].encode()).hexdigest()
    assert subtitles["content_hash"] == case.revision.content_hash
    assert report["coverage"]["asr_alignment"] == "not_run" and "alignment" not in report
    assert _snapshot(case) == before and offline_audio == []


@pytest.fixture
def accepted_asr(audio_case):
    case = audio_case()
    persona = ContentPersona(owner_user_id=case.user.id, name="Audio fixture persona")
    case.db.add(persona)
    case.db.flush()
    unit = ContentUnit(project_id=case.project.id, persona_id=persona.id, modality="video", title="ASR source")
    case.db.add(unit)
    case.db.flush()
    output = asr_suggestions._output({"status": "succeeded", "transcript": case.task.request_json["prompt"],
        "cues": [{"text": case.task.request_json["prompt"], "start_ms": 0, "end_ms": 1000}]}, 1000)
    payload = {"timeline": {"duration_ms": 1000}, "subtitles": {"cues": []}}
    base = ContentMasterRevision(
        project_id=case.project.id, content_unit_id=unit.id, revision_no=1, modality="video",
        payload_schema="video.master.v2", payload_json=payload, payload_hash=generation_tasks._hash(payload),
        context_hash="d" * 64, source_kind="manual", idempotency_key="asr-base",
        request_fingerprint="e" * 64, created_by=case.user.email,
    )
    case.db.add(base)
    case.db.flush()
    receipt_id = uuid.uuid4().hex
    # This is a saved legacy ASR contract fixture; no inference or provider capability is claimed.
    provenance = {
        "status": "verified_output_match", "base_master_id": base.id,
        "source": {"revision_id": case.revision.id, "content_hash": case.revision.content_hash},
        "provider_key": "asr.fixture", "provider_version": "1", "runtime_hash": "f" * 64,
        "input_hash": generation_tasks._hash({"source": case.revision.content_hash, "base": base.payload_hash}),
        "output_hash": generation_tasks._hash(output), "accepted_cues_hash": generation_tasks._hash(output["cues"]),
    }
    saved_payload = {"timeline": {"duration_ms": 1000}, "subtitles": {"cues": output["cues"]}}
    accepted = ContentMasterRevision(
        project_id=case.project.id, content_unit_id=unit.id, revision_no=2, parent_revision_id=base.id,
        modality="video", payload_schema="video.master.v2", payload_json=saved_payload,
        payload_hash=generation_tasks._hash(saved_payload), context_hash=base.context_hash,
        source_kind="manual", idempotency_key="asr-accepted", request_fingerprint="e" * 64,
        edit_summary_json={"asr_receipt_id": receipt_id, "asr_provenance": provenance}, created_by=case.user.email,
    )
    case.db.add(accepted)
    case.db.flush()
    for master in (base, accepted):
        case.db.add(ContentMasterAssetRef(master_revision_id=master.id, material_revision_id=case.revision.id,
            role="voice_audio", content_hash_snapshot=case.revision.content_hash))
    case.db.commit()
    case.asr_master, case.asr_base = accepted, base
    case.alignment = {"enabled": True, "srt_mode": "asr", "master_revision_id": accepted.id,
                      "receipt_id": receipt_id, "output_hash": provenance["output_hash"]}
    return case


def test_saved_exact_asr_segments_prove_alignment_on_read_without_inference(accepted_asr, quality_profile, offline_audio):
    case = accepted_asr
    before = _snapshot(case)
    report = _check(case, quality_profile, script=case.task.request_json["prompt"], alignment=case.alignment)
    assert report["status"] == "pass", report
    proof, subtitles = report["alignment"], report["subtitles"]
    assert report["coverage"]["asr_alignment"] == "verified_accepted_receipt_comparison"
    assert proof["material_revision_id"] == case.revision.id and proof["content_hash"] == case.revision.content_hash
    assert proof["master_revision_id"] == case.asr_master.id
    assert proof["master_payload_hash"] == case.asr_master.payload_hash
    assert proof["difference_ratio"] == 0 and proof["different_characters"] == 0
    assert proof["timing_alignment"] == "verified_asr_segment_timing" and proof["word_alignment"] == "not_run"
    assert subtitles["mode"] == "asr" and subtitles["estimated"] is False
    assert subtitles["filename"] == "audio-asr.srt" and "ESTIMATED" not in subtitles["srt"]
    assert subtitles["srt_hash"] == hashlib.sha256(subtitles["srt"].encode()).hexdigest()
    assert subtitles["receipt_id"] == case.alignment["receipt_id"]
    assert subtitles["output_hash"] == case.alignment["output_hash"]
    assert _check(case, quality_profile, script=case.task.request_json["prompt"], alignment=case.alignment) == report
    assert _snapshot(case) == before and offline_audio == []


@pytest.mark.parametrize("field,value", [
    ("master_revision_id", 999999), ("receipt_id", "0" * 32), ("output_hash", "0" * 64),
])
def test_missing_or_foreign_asr_proof_never_falls_back_to_estimates(accepted_asr, quality_profile, field, value):
    case = accepted_asr
    options = {**case.alignment, field: value}
    report = _check(case, quality_profile, script=case.task.request_json["prompt"], alignment=options)
    _issue(report, "blocker", "audio_alignment_accepted_receipt_required" if field == "master_revision_id"
           else "audio_alignment_receipt_mismatch")
    assert "alignment" not in report and "subtitles" not in report


def test_changed_saved_asr_cues_are_not_alignment_evidence(accepted_asr, quality_profile):
    case = accepted_asr
    payload = deepcopy(case.asr_master.payload_json)
    payload["subtitles"]["cues"][0]["text"] = "被修改的字幕"
    case.asr_master.payload_json = payload
    case.asr_master.payload_hash = generation_tasks._hash(payload)
    case.db.commit()
    report = _check(case, quality_profile, script=case.task.request_json["prompt"], alignment=case.alignment)
    _issue(report, "blocker", "audio_alignment_cues_changed")
    assert "subtitles" not in report and "alignment" not in report


def test_model_use_revocation_invalidates_saved_asr_proof(accepted_asr, quality_profile):
    case = accepted_asr
    case.revision.model_use_allowed = False
    case.db.commit()
    report = _check(case, quality_profile, script=case.task.request_json["prompt"], alignment=case.alignment)
    _issue(report, "blocker", "audio_alignment_scope_or_rights_changed")
    assert "subtitles" not in report and "alignment" not in report


def test_unsigned_spoken_script_cannot_be_exported_as_estimated_srt(audio_case, quality_profile):
    case = audio_case()
    report = _check(case, quality_profile, script="另一个未经接受的稿子",
                    alignment={"enabled": False, "srt_mode": "estimated"})
    _issue(report, "blocker", "audio_signed_script_mismatch")
    assert "subtitles" not in report


def _tts_snapshot(config, *, script="你好，今天聊聊本地音频。", direction_rate=0.9):
    spoken = validate_artifact("audio.spoken-adaptation.v1", {
        "script": script, "pronunciation_notes": [], "source_summary": "Accepted fixture content",
    })
    direction = validate_artifact("audio.voice-direction.v1", {
        "voice_character": "calm", "pace": "medium", "energy": "steady",
        "pause_policy": "sentence boundaries", "pronunciation_notes": [], "rate": direction_rate,
    })

    def proof(schema, content, attempt_id):
        output_hash = digest({"schema": schema, "content": content})
        return {
            "target": {"output_kind": "creative_attempt", "output_schema": schema,
                       "decision": "accepted", "output_hash": output_hash},
            "attempt_id": attempt_id, "attempt_input_hash": digest({"attempt_id": attempt_id}),
            "attempt_output_hash": output_hash, "config_hash": digest({}), "content_hash": digest(content),
        }

    effective, parameters = stage_audio._tts_config(config, direction_rate=direction_rate)
    snapshot = {
        "schema": "studio.audio.stage.tts.v1", "run_id": 1, "unit_id": 2, "project_id": 3,
        "node_id": "tts", "workflow": {"id": 1, "version": 1, "checksum": "a" * 64},
        "tts_source": "accepted_spoken", "config_hash": digest(effective),
        "spoken": proof("audio.spoken-adaptation.v1", spoken, 1),
        "voice_direction": {**proof("audio.voice-direction.v1", direction, 2), "content": direction},
        "script": spoken["script"], "script_hash": digest(spoken["script"]), "parameters": parameters,
        "rate_difference": {"direction_rate": direction_rate, "config_rate": parameters["rate"],
            "source": "config" if "rate" in effective else "accepted_voice_direction",
            "differs": direction_rate != parameters["rate"]},
    }
    snapshot["input_hash"] = digest(snapshot)
    return effective, {"run_id": 1, "unit_id": 2, "project_id": 3, "audio_stage": snapshot}


@pytest.mark.parametrize("field,value,request_field", [
    ("voice", "another_voice", "voice_id"), ("rate", 1.25, "rate"),
])
def test_native_tts_tunables_reach_exact_signed_request(audio_case, quality_profile, field, value, request_field):
    assert set(studio_creative_catalog.SKILLS["studio.audio.tts@1"]["tunable_fields"]) == {"voice", "rate"}
    config = {"selected_profile": "fixture.tts", "voice": "fixture_voice", "rate": 1.0}
    baseline_config, baseline_context = _tts_snapshot(config)
    baseline = stage_audio.tts_request(baseline_config, baseline_context)
    effective, context = _tts_snapshot({**config, field: value})
    before = deepcopy((effective, context))
    native = stage_audio.tts_request(effective, context)
    assert native == stage_audio._request(effective, context["audio_stage"]["script"],
                                         context["audio_stage"]["parameters"])
    assert native["parameters"][request_field] == value
    assert {name for name in native["parameters"] if native["parameters"][name] != baseline["parameters"][name]} == {
        request_field,
    }
    assert native["prompt"] == baseline["prompt"] == context["audio_stage"]["script"]
    assert native["source_revision_ids"] == [] and native["capability"] == "tts"
    assert native["selected_profile"] == "fixture.tts"
    assert (effective, context) == before
    case = audio_case(parameters=native["parameters"])
    generation_tasks._verify(case.task)
    assert case.task.request_json["parameters"] == native["parameters"]
    assert case.task.request_json["prompt"] == native["prompt"]
    assert _check(case, quality_profile)["status"] == "pass"
    applied = generation_tasks.tts_applied_parameters(case.task)
    assert applied[request_field] == value
    assert case.task.result_signature == generation_tasks._sign(case.task, generation_tasks._result_receipt(case.task))


@pytest.mark.parametrize("blueprint_key", [
    "starter.ai-tech-engineer.v1", "starter.lifestyle-observer.v1",
])
@pytest.mark.parametrize("voice,rate", [("fixture_voice_a", 0.85), ("fixture_voice_b", 1.25)])
def test_native_tts_tunables_flow_from_frozen_stage_to_real_request(
        db_session, audio_case, blueprint_key, voice, rate, monkeypatch):
    from app.services import creative_configuration, stage_domain_integrations, stage_resolver, starter_personas
    from app.services.content_harness.nodes import bootstrap_builtin_nodes
    from app.services.content_harness.registry import registry

    bootstrap_builtin_nodes()
    node = starter_personas.audio_definition(blueprint_key)["nodes"][2]
    node["config"]["selected_profile"] = "fixture.tts"
    override = {"voice": voice, "rate": rate}
    contract = registry.descriptor("node", node["plugin"], node["plugin_version"]).stage_contract
    profile = deepcopy(studio_creative_catalog.BLUEPRINTS[blueprint_key]["audio_creative_profile"])
    context = {"modality": "audio", "identity": {"content": {"audio_creative_profile": profile}},
               "master": {"id": 1}}
    monkeypatch.setattr(creative_configuration, "_configured_binding", lambda *_args, **_kwargs: {
        "status": "ready",
        "selected_binding": {"provider": "minimax.cli", "model": "speech-02-hd", "profile": "fixture.tts"},
        "route": {"plugin_id": "minimax.cli"}, "fallback_reason": None,
    })
    effective_node, method, creative, blockers = creative_configuration.frozen_stage(
        db_session, SimpleNamespace(id=1), SimpleNamespace(id=2, project_id=3, modality="audio"),
        node, contract, context, override)
    assert not blockers, blockers
    config = contract.effective_config(effective_node["config"], override)[1]
    assert config["selected_profile"] == "fixture.tts"
    assert config["voice"] == voice and config["rate"] == rate
    assert method["stack"] and creative["selected_binding"]["profile"] == "fixture.tts"
    _effective, audio_context = _tts_snapshot(config)
    resolved = stage_resolver.resolve_stage(
        workflow={"id": 1, "version": 1, "checksum": "a" * 64}, node=effective_node,
        contract=contract, context={**context, **audio_context}, upstream={}, method=method,
        model=None, override=override, creative=creative)
    assert resolved["ready"], resolved["blockers"]
    resolved = stage_domain_integrations.native_media_resolution(resolved)
    assert resolved["override"] == override
    request = stage_audio.tts_request(resolved["effective_config"], resolved["context"])
    assert resolved["effective_prompt"] == request["prompt"]
    assert request["capability"] == "tts"
    assert request["selected_profile"] == "fixture.tts"
    assert request["parameters"]["voice_id"] == voice
    assert request["parameters"]["rate"] == rate


@pytest.mark.parametrize("override,expected", [(None, 0.85), (1.0, 1.0), (1.5, 1.5)])
def test_native_tts_rate_uses_accepted_direction_unless_explicitly_overridden(override, expected):
    config = {"selected_profile": "fixture.tts", "voice": "fixture_voice"}
    if override is not None:
        config["rate"] = override
    effective, context = _tts_snapshot(config, direction_rate=0.85)
    assert stage_audio.tts_request(effective, context)["parameters"] == {
        "items": 1, "seconds": 120, "timeout_seconds": 25, "voice_id": "fixture_voice", "rate": expected,
    }


def test_native_tts_uses_exact_accepted_script_including_whitespace_and_long_text():
    script = "  " + "这是已经接受的口播稿。" * 220 + "\n"
    effective, context = _tts_snapshot({"selected_profile": "fixture.tts", "voice": "fixture_voice"}, script=script)
    assert len(script) > 2000
    assert stage_audio.tts_request(effective, context)["prompt"] == script


@pytest.mark.parametrize("change", ["voice", "rate", "script", "accepted-decision"])
def test_native_tts_rejects_changed_controls_script_or_unaccepted_snapshot(change):
    effective, context = _tts_snapshot({"selected_profile": "fixture.tts", "voice": "fixture_voice", "rate": 1.0})
    if change == "voice":
        effective["voice"] = "another_voice"
    elif change == "rate":
        effective["rate"] = 1.25
    elif change == "script":
        context["audio_stage"]["script"] = "替换了已接受稿件"
    else:
        context["audio_stage"]["spoken"]["target"]["decision"] = "proposed"
        context["audio_stage"]["input_hash"] = digest({
            key: value for key, value in context["audio_stage"].items() if key != "input_hash"
        })
    with pytest.raises(StageInvocationError) as exc:
        stage_audio.tts_request(effective, context)
    assert exc.value.code == "stage_audio_tts_snapshot_invalid"


@pytest.fixture
def image_batch_case(db_session, offline_audio, monkeypatch, tmp_path):
    from PIL import Image

    from app.services.content_harness import providers
    from app.services.content_harness.registry import PluginRegistry
    from app.services.multimedia_generation import normalize_request

    class ImageProvider:
        key, version = "minimax.cli", "1"

        def runtime_fingerprint(self):
            return "a" * 64

        def durable_identity(self, model_id):
            return {"credential_epoch": "b" * 64, "protocol_version": "image-fixture.v1"}

    registry = PluginRegistry()
    registry.register("image_provider", "minimax.cli", "1", ImageProvider())
    monkeypatch.setattr(providers, "registry", registry)
    user = User(email="image-batch@studio.test", name="Image selection fixture")
    db_session.add(user)
    db_session.flush()
    project = ContentProject(owner_user_id=user.id, title="Image batch fixture")
    db_session.add(project)
    db_session.flush()
    request = {"capability": "image_generation", "selected_profile": "fixture.image",
               "prompt": "Four synthetic color cards", "parameters": {"items": 4, "pixels": 1024}}
    plan = {"parameters": deepcopy(request["parameters"]), "multimedia": normalize_request(
        capability="image_generation", prompt=request["prompt"], parameters=request["parameters"],
        binding={"adapter_key": "minimax.cli", "adapter_version": "1", "model_id": "image-01"},
        configuration_mode="custom", candidate_mode="native")}
    task_id = uuid.uuid4().hex
    task = ProviderGenerationTask(
        id=task_id, owner_user_id=user.id, project_id=project.id, idempotency_key=task_id,
        state="prepared", request_json=request, plan_json=plan, source_refs_json=[],
        provider_kind="image_provider", provider_key="minimax.cli", provider_version="1", model_id="image-01",
        protocol_version="image-fixture.v1", runtime_hash="a" * 64, credential_epoch="b" * 64,
        input_hash=generation_tasks._hash({"request": request, "sources": [], "actor": user.id}),
        receipt_key_id="audio-fixture",
    )
    contents = []
    for color in ("red", "green", "blue", "yellow"):
        output = io.BytesIO()
        Image.new("RGB", (16, 16), color).save(output, format="PNG")
        contents.append(output.getvalue())
    result = generation_tasks._persist_batch_result(task, [
        {"content": content, "mime_type": "image/png"} for content in contents])
    task.result_storage_key, task.result_hash = result["storage"], result["hash"]
    task.result_mime, task.result_size, task.state = result["mime"], result["size"], "result_ready"
    _seal(task)
    db_session.add(task)
    db_session.commit()
    decision = {"confirmed": True, "title": "Chosen synthetic card", "license_code": "local-test-only",
                "license_evidence_hash": "c" * 64, "public_use_allowed": False,
                "model_use_allowed": False, "commercial_use_allowed": False, "candidate_index": 2}
    return SimpleNamespace(db=db_session, user=user, project=project, task=task, contents=contents,
                           decision=decision, path=tmp_path)


def test_exact_image_candidate_acceptance_preserves_batch_and_master(image_batch_case):
    from app.services import materials

    case = image_batch_case
    original_key = case.task.result_storage_key
    original_manifest = material_storage.provider().read(original_key)
    saved = generation_tasks.accept(case.db, case.user, case.task.id, case.task.revision, case.decision)
    revision = case.db.get(MaterialRevision, saved["material_revision_id"])
    assert materials.read_bytes_checked(case.db, revision) == case.contents[2]
    assert revision.content_hash == hashlib.sha256(case.contents[2]).hexdigest()
    assert revision.source_metadata_json["generation_candidate"]["candidate_index"] == 2
    assert not revision.public_use_allowed and not revision.model_use_allowed and not revision.commercial_use_allowed
    assert case.db.query(MaterialRevision).count() == 1 and case.db.query(Material).count() == 1
    assert case.db.query(ContentMasterRevision).count() == 0
    assert case.task.result_storage_key != original_key
    assert material_storage.provider().read(original_key) == original_manifest
    for index, content in enumerate(case.contents):
        assert generation_tasks.raw(case.db, case.user, case.task.id, index) == (content, "image/png")
    assert generation_tasks.accept(case.db, case.user, case.task.id, case.task.revision, case.decision) == saved
    assert case.db.query(MaterialRevision).count() == 1


@pytest.mark.parametrize("index", [-1, 4, True, "2"])
def test_image_selection_out_of_contract_creates_no_material(image_batch_case, index):
    from fastapi import HTTPException

    case = image_batch_case
    before = _snapshot(case)
    with pytest.raises(HTTPException) as exc:
        generation_tasks.accept(case.db, case.user, case.task.id, case.task.revision,
                                {**case.decision, "candidate_index": index})
    assert exc.value.status_code == 422 and exc.value.detail == "multimedia_candidate_selection_invalid"
    assert _snapshot(case) == before


@pytest.mark.parametrize("tamper", ["request", "result_signature", "manifest", "candidate_bytes"])
def test_image_receipt_and_bytes_tampering_blocks_acceptance(image_batch_case, tamper):
    from fastapi import HTTPException

    case = image_batch_case
    if tamper == "request":
        case.task.request_json = {**case.task.request_json, "prompt": "foreign prompt"}
        case.db.commit()
    elif tamper == "result_signature":
        case.task.result_signature = "0" * 64
        case.db.commit()
    elif tamper == "manifest":
        (case.path / case.task.result_storage_key).write_bytes(b"{}")
    else:
        manifest = generation_tasks._batch_manifest(case.task, required=True)
        (case.path / manifest["candidates"][2]["storage_key"]).write_bytes(case.contents[0])
    before = _snapshot(case)
    with pytest.raises(HTTPException) as exc:
        generation_tasks.accept(case.db, case.user, case.task.id, case.task.revision, case.decision)
    assert exc.value.status_code == 409
    assert _snapshot(case) == before
    assert case.db.query(MaterialRevision).count() == 0


def test_accepted_image_selection_cannot_be_replaced(image_batch_case):
    from fastapi import HTTPException

    case = image_batch_case
    saved = generation_tasks.accept(case.db, case.user, case.task.id, case.task.revision, case.decision)
    with pytest.raises(HTTPException) as exc:
        generation_tasks.accept(case.db, case.user, case.task.id, case.task.revision,
                                {**case.decision, "candidate_index": 1})
    assert exc.value.status_code == 409 and exc.value.detail == "provider_acceptance_conflict"
    assert case.task.accepted_material_revision_id == saved["material_revision_id"]
    assert case.db.query(MaterialRevision).count() == 1
