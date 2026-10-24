"""Video submit must keep the original task receipt and not hide a finished rejection."""

import subprocess

from app.services.minimax_cli_provider import MiniMaxCLIVideoProvider


def _request():
    return {"prompt": "蓝色方块缓慢旋转", "model_id": "MiniMax-H3",
            "parameters": {"items": 1, "seconds": 6}, "timeout_seconds": 20}


def test_video_submit_returns_immediately_with_task_id(monkeypatch):
    seen = {}

    def fake_run(args, *, timeout):
        seen["args"] = args
        seen["timeout"] = timeout
        return subprocess.CompletedProcess(args, 0, stdout='{"taskId":"424010985738629"}\n', stderr="")

    monkeypatch.setattr("app.services.minimax_cli_provider._run", fake_run)
    output = MiniMaxCLIVideoProvider().submit_task(_request())

    assert "--no-wait" in seen["args"]
    assert "--async" not in seen["args"]
    assert output.status == "running"
    assert output.metadata["job_id"] == "424010985738629"


def test_video_submit_accepts_task_id_field(monkeypatch):
    def fake_run(args, *, timeout):
        return subprocess.CompletedProcess(args, 0, stdout='{"task_id":"106916112212032"}', stderr="")

    monkeypatch.setattr("app.services.minimax_cli_provider._run", fake_run)
    output = MiniMaxCLIVideoProvider().submit_task(_request())

    assert output.status == "running"
    assert output.metadata["job_id"] == "106916112212032"


def test_completed_video_rejection_is_failed_not_unknown(monkeypatch):
    def fake_run(args, *, timeout):
        return subprocess.CompletedProcess(args, 4, stdout="", stderr='{"error":{"code":4}}')

    monkeypatch.setattr("app.services.minimax_cli_provider._run", fake_run)
    output = MiniMaxCLIVideoProvider().submit_task(_request())

    assert output.status == "failed"


def test_video_submit_timeout_stays_unknown(monkeypatch):
    monkeypatch.setattr("app.services.minimax_cli_provider._run", lambda args, *, timeout: None)
    output = MiniMaxCLIVideoProvider().submit_task(_request())

    assert output.status == "unknown"


def test_hailuo_submit_keeps_the_six_second_default(monkeypatch):
    seen = {}

    def fake_run(args, *, timeout):
        seen["args"] = args
        return subprocess.CompletedProcess(args, 0, stdout='{"taskId":"106916112212032"}', stderr="")

    monkeypatch.setattr("app.services.minimax_cli_provider._run", fake_run)
    request = _request()
    request["model_id"] = "MiniMax-Hailuo-2.3"
    output = MiniMaxCLIVideoProvider().submit_task(request)

    assert "--duration" not in seen["args"]
    assert "--no-wait" in seen["args"]
    assert seen["args"][seen["args"].index("--model") + 1] == "MiniMax-Hailuo-2.3"
    assert output.status == "running"
    assert output.metadata["job_id"] == "106916112212032"


def test_hailuo_submit_refuses_a_duration_the_cli_would_drop(monkeypatch):
    monkeypatch.setattr("app.services.minimax_cli_provider._run", lambda args, *, timeout: (_ for _ in ()).throw(AssertionError("submitted")))
    request = _request()
    request["model_id"] = "MiniMax-Hailuo-2.3"
    request["parameters"] = {"items": 1, "seconds": 10}

    assert MiniMaxCLIVideoProvider().submit_task(request).status == "unavailable"
