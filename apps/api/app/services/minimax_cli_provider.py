"""Bounded local MiniMax CLI providers.

The application never accepts a shell command or arbitrary credential path from
configuration.  With explicit local authorization, the fixed official CLI
config is read only to derive an in-memory credential continuity fingerprint;
raw credentials never leave this process.  The installed ``mmx`` process still
owns provider authentication and this module only invokes fixed subcommands.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import logging
import math
import multiprocessing
import os
import pwd
import re
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
import wave
from contextvars import ContextVar
from decimal import Decimal, InvalidOperation
from pathlib import Path

import httpx

from .content_harness.providers import MediaOutput

CLI_VERSION = "1"
CLI_KEY = "minimax.cli"
_MAX_OUTPUT = 30 * 1024 * 1024
_MAX_STDOUT = 512 * 1024
_MAX_PROMPT = 10_000

_IMAGE_MODELS = {"image-01", "image-01-live"}
_VIDEO_MODELS = {"MiniMax-H3", "MiniMax-Hailuo-2.3"}
_TTS_MODELS = {
    "speech-2.8-hd", "speech-2.8-turbo", "speech-2.6-hd", "speech-2.6-turbo",
    "speech-02-hd", "speech-02-turbo", "speech-01-hd", "speech-01-turbo",
}
_ASR_MODELS = {"asr-1.0"}
_JOB_ID = re.compile(r"[A-Za-z0-9_.-]{1,100}")
_downloading = ContextVar("minimax_result_download", default=False)
_CLI_CONFIG = Path(pwd.getpwuid(os.getuid()).pw_dir) / ".mmx" / "config.json"
_MAX_CONFIG_BYTES = 64 * 1024
_RECEIPT_ID = re.compile(r"[A-Za-z0-9_.-]{1,200}\Z")


class _PrivateDownloadLogs(logging.Filter):
    def filter(self, _record):
        return not _downloading.get()


for _logger in ("httpx", "httpcore", "httpcore.connection", "httpcore.http11", "httpcore.http2"):
    logging.getLogger(_logger).addFilter(_PrivateDownloadLogs())


def _command_json(args: list[str], timeout: int) -> dict | None:
    result = _run(args, timeout=timeout)
    if result is None or result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except (ValueError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def _job_id(value) -> str | None:
    if type(value) is int and value > 0:
        value = str(value)
    return value if isinstance(value, str) and _JOB_ID.fullmatch(value) else None


def _download_video_bytes(url: str, deadline: float) -> bytes:
    from .url_fetch import pinned_transport

    original = httpx.URL(url)
    if (original.scheme != "https" or not original.host or original.port not in {None, 443}
            or original.username or original.password or original.fragment or len(url) > 8192):
        raise ValueError("generation_download_unavailable")
    token = _downloading.set(True)
    try:
        current = original
        for _ in range(4):
            transport = pinned_transport(str(current))
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                transport.close()
                raise ValueError("generation_download_unavailable")
            with (
                httpx.Client(transport=transport, trust_env=False, follow_redirects=False,
                             timeout=remaining) as client,
                client.stream("GET", current, headers={"Accept-Encoding": "identity"}) as response,
            ):
                if response.status_code in {301, 302, 303, 307, 308}:
                    redirected = current.join(response.headers["location"])
                    if ((redirected.scheme, redirected.host, redirected.port)
                            != (original.scheme, original.host, original.port)
                            or redirected.username or redirected.password or redirected.fragment):
                        raise ValueError("generation_download_unavailable")
                    current = redirected
                    continue
                response.raise_for_status()
                if response.headers.get("content-encoding", "identity").lower().strip() != "identity":
                    raise ValueError("generation_download_unavailable")
                content = bytearray()
                for chunk in response.iter_raw():
                    if time.monotonic() >= deadline or len(content) + len(chunk) > _MAX_OUTPUT:
                        raise ValueError("generation_download_unavailable")
                    content.extend(chunk)
                if not content or time.monotonic() >= deadline:
                    raise ValueError("generation_download_unavailable")
                return bytes(content)
        raise ValueError("generation_download_unavailable")
    finally:
        _downloading.reset(token)


def _download_worker(url: str, deadline: float, path: str) -> None:
    try:
        content = _download_video_bytes(url, deadline)
        with Path(path).open("xb") as target:
            target.write(content)
    except Exception:  # noqa: BLE001 No signed URL/error escapes the isolated worker.
        return


def _download_video(url: str, deadline: float) -> bytes:
    # DNS and a trickling response cannot be interrupted by a thread timeout.
    # A fresh process provides an actual stop boundary without inheriting clients.
    with tempfile.TemporaryDirectory(prefix="aics-mmx-download-") as directory:
        output = Path(directory) / "result.bin"
        process = multiprocessing.get_context("spawn").Process(
            target=_download_worker, args=(url, deadline, str(output)), daemon=True,
        )
        try:
            if time.monotonic() >= deadline:
                raise ValueError("generation_download_unavailable")
            process.start()
            process.join(max(0, deadline - time.monotonic()))
            if process.is_alive() or process.exitcode != 0 or time.monotonic() >= deadline:
                raise ValueError("generation_download_unavailable")
            with output.open("rb") as source:
                content = source.read(_MAX_OUTPUT + 1)
            if not content or len(content) > _MAX_OUTPUT or time.monotonic() >= deadline:
                raise ValueError("generation_download_unavailable")
            return content
        finally:
            if process.pid is not None:
                if process.is_alive():
                    process.kill()
                process.join()
                process.close()


def _executable() -> str | None:
    return shutil.which("mmx")


def _run(args: list[str], *, timeout: int) -> subprocess.CompletedProcess[str] | None:
    return _run_bounded(_executable(), args, timeout=timeout, output_limit=_MAX_STDOUT)


def _run_bounded(executable: str | None, args: list[str], *, timeout: float,
                 output_limit: int) -> subprocess.CompletedProcess[str] | None:
    if executable is None or type(timeout) not in {int, float} or not 0 < timeout <= 300:
        return None
    process = None
    try:
        process = subprocess.Popen(
            [executable, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        deadline = time.monotonic() + timeout
        outputs = [bytearray(), bytearray()]
        with selectors.DefaultSelector() as selector:
            for index, stream in enumerate((process.stdout, process.stderr)):
                selector.register(stream, selectors.EVENT_READ, index)
            total = 0
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fd, min(65536, output_limit - total + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    if total > output_limit:
                        return None
                    outputs[key.data].extend(chunk)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        returncode = process.wait(timeout=remaining)
        return subprocess.CompletedProcess(
            process.args, returncode, *(data.decode("utf-8", errors="replace") for data in outputs)
        )
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        if process is not None:
            # The CLI can spawn download helpers; a timed-out request must not
            # leave them running or submit a replacement request.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()


def _read_output(path: Path, *, mime: str | None, command: subprocess.CompletedProcess[str] | None) -> MediaOutput:
    if command is None:
        return MediaOutput("unknown")
    if command.returncode != 0:
        # A CLI error can occur after the supplier accepted a paid request.
        return MediaOutput("unknown")
    try:
        with path.open("rb") as source:
            content = source.read(_MAX_OUTPUT + 1)
    except OSError:
        return MediaOutput("unknown")
    if not content or len(content) > _MAX_OUTPUT:
        return MediaOutput("unknown")
    if mime is None:
        from .materials import sniff_mime

        mime = sniff_mime(content, None)
    return MediaOutput("succeeded", content, mime, {"executor": CLI_KEY, "stdout_bounded": True})


def _prompt(request: dict) -> str | None:
    prompt = request.get("prompt") or request.get("text")
    return prompt if isinstance(prompt, str) and prompt.strip() and len(prompt) <= _MAX_PROMPT else None


def _runtime_identity() -> str | None:
    result = _run(["--version", "--no-color"], timeout=5)
    if result is None or result.returncode != 0 or not result.stdout or len(result.stdout) > 200:
        return None
    safe = f"{_executable()}|{result.stdout.strip()}|{CLI_VERSION}"
    return hashlib.sha256(safe.encode()).hexdigest()


def _read_cli_config() -> dict | None:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if no_follow is None or directory is None:
        return None
    parent_fd = None
    config_fd = None
    try:
        parent_fd = os.open(_CLI_CONFIG.parent, os.O_RDONLY | directory | no_follow)
        config_fd = os.open(_CLI_CONFIG.name, os.O_RDONLY | no_follow, dir_fd=parent_fd)
        with os.fdopen(config_fd, "rb") as source:
            config_fd = None
            stat = os.fstat(source.fileno())
            if (not stat.st_mode & 0o100000 or stat.st_uid != os.getuid()
                    or stat.st_mode & 0o077 or stat.st_size > _MAX_CONFIG_BYTES):
                return None
            raw = source.read(_MAX_CONFIG_BYTES + 1)
        if len(raw) > _MAX_CONFIG_BYTES:
            return None
        config = json.loads(raw)
        return config if isinstance(config, dict) else None
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    finally:
        if config_fd is not None:
            os.close(config_fd)
        if parent_fd is not None:
            os.close(parent_fd)


def _credential_epoch() -> str | None:
    """Return an opaque HMAC fingerprint without exposing local CLI secrets."""
    try:
        config = _read_cli_config()
        region = config.get("region") if config else None
        if not isinstance(region, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", region):
            return None
        auth = config.get("oauth") if isinstance(config.get("oauth"), dict) else None
        if auth is None and isinstance(config.get("auth"), dict):
            auth = config.get("auth")
        api_key = config.get("api_key")
        access_token = auth.get("access_token") if auth else config.get("access_token")
        refresh_token = auth.get("refresh_token") if auth else config.get("refresh_token")
        account = auth.get("account") if auth else config.get("account")
        auth_version = auth.get("version") if auth else config.get("auth_version")
        token_expires = auth.get("expires_at") if auth else config.get("expires_at")
        resource_url = auth.get("resource_url") if auth else config.get("resource_url")
        if not any(isinstance(value, str) and value for value in (api_key, access_token, refresh_token)):
            return None
        keys = json.loads(os.environ.get("AICS_GENERATION_RECEIPT_KEYS", "{}"))
        key_id = os.environ.get("AICS_GENERATION_RECEIPT_KEY_ID")
        key = keys.get(key_id) if isinstance(keys, dict) and isinstance(key_id, str) else None
        if (not _RECEIPT_ID.fullmatch(key_id or "") or not isinstance(key, str)
                or not re.fullmatch(r"[0-9a-f]{64}", key)):
            return None
        material = json.dumps({"region": region, "api_key": api_key if isinstance(api_key, str) else None,
                               "access_token": access_token if isinstance(access_token, str) else None,
                               "refresh_token": refresh_token if isinstance(refresh_token, str) else None,
                               "account": account if isinstance(account, (str, int)) else None,
                               "auth_version": auth_version if isinstance(auth_version, (str, int)) else None,
                               "expires_at": token_expires if isinstance(token_expires, (str, int, float)) else None,
                               "resource_url": resource_url if isinstance(resource_url, str) else None},
                              sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(bytes.fromhex(key), b"aics:minimax-cli:credential:v1:" + material,
                        hashlib.sha256).hexdigest()
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _protocol_for_model(model_id: str) -> str | None:
    if model_id in _IMAGE_MODELS:
        return "minimax.image.v1"
    if model_id == "MiniMax-H3":
        return "minimax.video.v2"
    if model_id == "MiniMax-Hailuo-2.3":
        return "minimax.video.v1"
    if model_id in _TTS_MODELS:
        return "minimax.tts.v1"
    if model_id in _ASR_MODELS:
        return "minimax.asr.v1"
    return None


class _MiniMaxCredentialIdentity:
    def durable_identity(self, model_id: str) -> dict | None:
        epoch = _credential_epoch()
        protocol = _protocol_for_model(model_id)
        return ({"credential_epoch": epoch, "protocol_version": protocol}
                if epoch and protocol else None)


def _image_model() -> str | None:
    result = _run(["image", "generate", "--prompt", "capability-contract-probe", "--dry-run",
        "--output", "json", "--quiet", "--non-interactive", "--no-color"], timeout=5)
    if result is None or result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except (TypeError, ValueError):
        return None
    request = value.get("request") if isinstance(value, dict) else None
    model = request.get("model") if isinstance(request, dict) else None
    # Do not project arbitrary dry-run fields (which may contain auth data).
    return model if isinstance(model, str) and model in _IMAGE_MODELS else None


def _image_runtime_identity(expected_model: str | None = None) -> str | None:
    runtime, model = _runtime_identity(), _image_model()
    if expected_model is not None and model != expected_model:
        return None
    return hashlib.sha256(f"{runtime}|{model}".encode()).hexdigest() if runtime and model else None


class MiniMaxCLIModelAdapter(_MiniMaxCredentialIdentity):
    key = CLI_KEY
    version = CLI_VERSION

    def runtime_fingerprint(self) -> str | None:
        return _runtime_identity()

    def binding_state(self, capability: str, binding: dict) -> dict:
        if binding.get("base_url") != "local://mmx":
            return {"reason": "connection_unavailable", "runtime_hash": None}
        model_id = binding.get("model_id")
        models_by_capability = {
            "image_generation": _IMAGE_MODELS,
            "video_generation": _VIDEO_MODELS,
            "tts": _TTS_MODELS,
            "asr": _ASR_MODELS,
        }
        models = models_by_capability.get(capability)
        # CLI help includes text, but no text dispatcher exists yet.
        if models is None or not isinstance(model_id, str) or model_id not in models:
            return {"reason": "adapter_capability_unsupported", "runtime_hash": None}
        # Inventory must not launch a CLI that may load its credential file.
        return {"reason": "credential_continuity_unverified", "runtime_hash": None}

    def execution_binding_state(self, capability: str, binding: dict) -> dict:
        configured = self.binding_state(capability, binding)
        if configured["reason"] != "credential_continuity_unverified":
            return configured
        model_id = binding["model_id"]
        runtime = _image_runtime_identity(model_id) if capability == "image_generation" else _runtime_identity()
        # Configured credentials make explicit dispatch possible; verified is
        # still reserved for a real accepted provider result.
        ready = runtime is not None and _credential_epoch() is not None
        return {"reason": None if ready else ("credential_continuity_unverified" if runtime else "connection_unavailable"),
                "runtime_hash": runtime}


class MiniMaxCLIImageProvider(_MiniMaxCredentialIdentity):
    key = CLI_KEY
    version = CLI_VERSION

    def runtime_fingerprint(self) -> str | None:
        return _image_runtime_identity()

    def submit_task(self, request: dict) -> MediaOutput:
        parameters = request.get("parameters")
        pixels = parameters.get("pixels") if isinstance(parameters, dict) else None
        timeout = request.get("timeout_seconds", 25)
        if (not isinstance(parameters, dict) or type(parameters.get("items")) is not int or parameters.get("items") != 1
                or type(pixels) is not int or pixels < 512 * 512
                or type(timeout) not in {int, float} or not 0 < timeout <= 25):
            return MediaOutput("unavailable")
        return self.generate(request)

    def generate(self, request: dict) -> MediaOutput:
        prompt = _prompt(request)
        model = request.get("model_id", "image-01")
        if (prompt is None or request.get("source_bytes") or request.get("source_revision_ids")
                or not isinstance(model, str) or model not in _IMAGE_MODELS or model != _image_model()):
            return MediaOutput("unavailable")
        parameters = request.get("parameters", {})
        pixels = parameters.get("pixels", 1024 * 1024) if isinstance(parameters, dict) else None
        if type(pixels) is not int or pixels < 512 * 512:
            return MediaOutput("unavailable")
        side = min(2048, math.isqrt(pixels) // 8 * 8)
        with tempfile.TemporaryDirectory(prefix="aics-mmx-") as directory:
            output = Path(directory) / "image.png"
            # Base64 avoids the CLI's unbounded CDN download/retry path.
            args = ["image", "generate", "--prompt", prompt, "--out", str(output), "--n", "1",
                    "--width", str(side), "--height", str(side), "--response-format", "base64",
                    "--quiet", "--non-interactive", "--no-color"]
            command = _run(args, timeout=request.get("timeout_seconds", 25))
            return _read_output(output, mime=None, command=command)


class MiniMaxCLIVideoProvider(_MiniMaxCredentialIdentity):
    key = CLI_KEY
    version = CLI_VERSION

    def runtime_fingerprint(self) -> str | None:
        return _runtime_identity()

    def submit_task(self, request: dict) -> MediaOutput:
        prompt = _prompt(request)
        parameters = request.get("parameters")
        seconds = parameters.get("seconds") if isinstance(parameters, dict) else None
        timeout = request.get("timeout_seconds", 25)
        # V1 does not expose this duration contract; do not silently discard it.
        if (prompt is None or request.get("model_id") != "MiniMax-H3"
                or len(prompt.encode("utf-16-le")) // 2 > 7000
                or type(seconds) is not int or not 4 <= seconds <= 15
                or type(timeout) not in {int, float} or not 0 < timeout <= 25
                or request.get("source_bytes") or request.get("source_revision_ids")):
            return MediaOutput("unavailable")
        value = _command_json(["video", "generate", "--model", "MiniMax-H3", "--prompt", prompt,
            "--duration", str(seconds), "--async", "--output", "json", "--non-interactive", "--no-color"],
            timeout)
        job = _job_id(value.get("taskId")) if value else None
        return MediaOutput("running", metadata={"job_id": job}) if job else MediaOutput("unknown")

    def query_task(self, request: dict) -> MediaOutput:
        job = _job_id(request.get("job_id"))
        model = request.get("model_id")
        protocol = request.get("protocol_version")
        expected_protocol = {"MiniMax-H3": "minimax.video.v2", "MiniMax-Hailuo-2.3": "minimax.video.v1"}
        timeout = request.get("timeout_seconds", 25)
        if (not job or not isinstance(model, str) or model not in expected_protocol
                or protocol != expected_protocol[model]
                or type(timeout) not in {int, float} or not 0 < timeout <= 25):
            return MediaOutput("unknown")
        deadline = time.monotonic() + timeout
        # --quiet emits only status text and destroys the original-task receipt.
        value = _command_json(["video", "task", "get", "--task-id", job, "--model", model,
            "--output", "json", "--non-interactive", "--no-color"], timeout)
        if not value or _job_id(value.get("task_id")) != job:
            return MediaOutput("unknown")
        if not isinstance(value.get("status"), str):
            return MediaOutput("unknown")
        metadata = {"job_id": job}
        if model == "MiniMax-H3":
            if value.get("model") != model:
                return MediaOutput("unknown")
            status = value.get("status")
            if status in {"queued", "running"}:
                return MediaOutput("running", metadata=metadata)
            if status == "expired":
                return MediaOutput("unknown", metadata={**metadata, "reason": "generation_job_expired"})
            if status in {"failed", "cancelled"}:
                return MediaOutput("cancelled" if status == "cancelled" else "failed")
            url = value.get("url")
            if status != "succeeded" or not isinstance(url, str):
                return MediaOutput("unknown")
            try:
                content = _download_video(url, deadline)
            except (ValueError, OSError, httpx.HTTPError, KeyError):
                return MediaOutput("running", metadata={**metadata, "reason": "generation_download_unavailable"})
            return MediaOutput("succeeded", content, "video/mp4", metadata)
        status = value.get("status")
        if status in {"Preparing", "Queueing", "Processing"}:
            return MediaOutput("running", metadata=metadata)
        if status == "Success":
            file_id = _job_id(value.get("file_id"))
            if not file_id:
                return MediaOutput("unknown")
            return MediaOutput("running", metadata={**metadata, "file_id": file_id,
                "reason": "generation_download_unavailable"})
        # Unproven terminal spellings remain unknown rather than authorizing retry.
        return MediaOutput("unknown")

    def generate(self, request: dict) -> MediaOutput:
        prompt = _prompt(request)
        model = request.get("model_id", "MiniMax-Hailuo-2.3")
        # Reference-based modes need exact byte bindings, not ignored refs
        # attached to a text-only generation result.
        if (prompt is None or not isinstance(model, str) or model not in _VIDEO_MODELS
                or request.get("source_bytes") or request.get("source_revision_ids")):
            return MediaOutput("unavailable")
        with tempfile.TemporaryDirectory(prefix="aics-mmx-") as directory:
            output = Path(directory) / "video.mp4"
            args = ["video", "generate", "--prompt", prompt, "--download", str(output), "--quiet", "--non-interactive", "--no-color"]
            args[2:2] = ["--model", model]
            command = _run(args, timeout=request.get("timeout_seconds", 25))
            if command is None:
                return MediaOutput("unknown")
            return _read_output(output, mime="video/mp4", command=command)


class MiniMaxCLITTSProvider(_MiniMaxCredentialIdentity):
    key = CLI_KEY
    version = CLI_VERSION

    def runtime_fingerprint(self) -> str | None:
        return _runtime_identity()

    def submit_task(self, request: dict) -> MediaOutput:
        parameters = request.get("parameters")
        seconds = parameters.get("seconds") if isinstance(parameters, dict) else None
        timeout = request.get("timeout_seconds", 25)
        if (not isinstance(parameters, dict) or type(parameters.get("items")) is not int or parameters.get("items") != 1
                or type(seconds) is not int or seconds < 1
                or type(timeout) not in {int, float} or not 0 < timeout <= 25):
            return MediaOutput("unavailable")
        return self.generate(request)

    def generate(self, request: dict) -> MediaOutput:
        text = _prompt(request)
        model = request.get("model_id", "speech-2.8-hd")
        if (text is None or len(text) >= 10_000 or not isinstance(model, str) or model not in _TTS_MODELS
                or request.get("source_bytes") or request.get("source_revision_ids")):
            return MediaOutput("unavailable")
        with tempfile.TemporaryDirectory(prefix="aics-mmx-") as directory:
            output = Path(directory) / "speech.wav"
            args = ["speech", "synthesize", "--text", text, "--format", "wav", "--out", str(output), "--quiet", "--non-interactive", "--no-color"]
            args[2:2] = ["--model", model]
            command = _run(args, timeout=request.get("timeout_seconds", 25))
            return _read_output(output, mime="audio/wav", command=command)


def _media_command(program: str, args: list[str], deadline: float):
    if program not in {"ffmpeg", "ffprobe"}:
        raise ValueError("asr_source_audio_unavailable")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ValueError("asr_source_preparation_timeout")
    result = _run_bounded(shutil.which(program), args, timeout=min(10, remaining), output_limit=4096)
    if result is None or result.returncode != 0 or time.monotonic() >= deadline:
        raise ValueError("asr_source_audio_unavailable")
    return result


def _asr_audio(content: bytes, mime: str, duration_ms: int, deadline: float) -> bytes:
    from .provider_media import _decode

    if mime == "video/mp4":
        from .materials import sniff_mime

        if sniff_mime(content, None) != "video/mp4":
            raise ValueError("asr_source_or_model_unsupported")
        with tempfile.TemporaryDirectory(prefix="aics-mmx-audio-") as directory:
            source, target = Path(directory) / "source.mp4", Path(directory) / "audio.wav"
            source.write_bytes(content)
            probe = _media_command("ffprobe", ["-v", "error", "-protocol_whitelist", "file",
                "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                "-of", "json", str(source)], deadline)
            try:
                value = json.loads(probe.stdout)
                streams = value["streams"]
                width, height = streams[0]["width"], streams[0]["height"]
                duration = Decimal(value["format"]["duration"])
                if (len(streams) != 1 or type(width) is not int or type(height) is not int
                        or width <= 0 or height <= 0 or width * height > 16_000_000
                        or not duration.is_finite() or not 0 < duration * 1000 <= duration_ms):
                    raise ValueError("asr_source_duration_invalid")
            except (ValueError, TypeError, KeyError, IndexError, InvalidOperation):
                raise ValueError("asr_source_duration_invalid") from None
            # Validate actual frames without allowing embedded remote sources.
            _media_command("ffmpeg", ["-nostdin", "-v", "error", "-xerror", "-threads", "1",
                "-protocol_whitelist", "file", "-i", str(source), "-map", "0:v:0", "-f", "null", "-"], deadline)
            _media_command("ffmpeg", ["-nostdin", "-v", "error", "-xerror", "-threads", "1",
                "-protocol_whitelist", "file", "-i", str(source), "-map", "0:a:0", "-vn",
                "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-f", "wav",
                "-fs", str(_MAX_OUTPUT), str(target)], deadline)
            try:
                with target.open("rb") as audio_file:
                    content = audio_file.read(_MAX_OUTPUT + 1)
            except OSError:
                raise ValueError("asr_source_audio_unavailable") from None
    if not content or len(content) > _MAX_OUTPUT or time.monotonic() >= deadline:
        raise ValueError("asr_source_audio_unavailable")
    _decode(content, "audio/wav")
    with wave.open(io.BytesIO(content)) as audio:
        if not 0 < audio.getnframes() * 1000 <= duration_ms * audio.getframerate():
            raise ValueError("asr_source_duration_invalid")
    if time.monotonic() >= deadline:
        raise ValueError("asr_source_preparation_timeout")
    return content


class MiniMaxCLIASRProvider(_MiniMaxCredentialIdentity):
    key = CLI_KEY
    version = CLI_VERSION

    def runtime_fingerprint(self) -> str | None:
        return _runtime_identity()

    def transcribe(self, request: dict) -> dict:
        content = request.get("source_bytes")
        if not isinstance(content, bytes) or not content or len(content) > _MAX_OUTPUT:
            raise ValueError("asr_source_invalid")
        mime = request.get("mime_type")
        if (not isinstance(mime, str) or mime not in {"audio/wav", "video/mp4"}
                or request.get("model_id", "asr-1.0") != "asr-1.0"):
            raise ValueError("asr_source_or_model_unsupported")
        duration_ms = request.get("max_duration_ms")
        if type(duration_ms) is not int or not 0 < duration_ms <= 500_000:
            raise ValueError("asr_source_duration_invalid")
        timeout = request.get("timeout_seconds", 25)
        if type(timeout) not in {int, float} or not 0 < timeout <= 300:
            raise ValueError("asr_timeout_invalid")
        deadline = time.monotonic() + min(timeout, 25)
        content = _asr_audio(content, mime, duration_ms, deadline)
        with tempfile.TemporaryDirectory(prefix="aics-mmx-") as directory:
            source = Path(directory) / "input.wav"
            output = Path(directory) / "transcript.srt"
            source.write_bytes(content)
            args = ["speech", "transcribe", "--model", "asr-1.0", "--file", str(source),
                "--response-format", "srt", "--timestamp-level", "sentence", "--out", str(output),
                "--quiet", "--non-interactive", "--no-color"]
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError("asr_source_preparation_timeout")
            command = _run(args, timeout=remaining)
            if command is None:
                return {"status": "unknown"}
            if command.returncode != 0:
                # Nonzero exit does not prove the paid transcription was never sent.
                return {"status": "unknown"}
            try:
                with output.open("rb") as source_output:
                    raw = source_output.read(_MAX_STDOUT + 1)
                if len(raw) > _MAX_STDOUT:
                    raise ValueError("asr_output_invalid")
                return _srt_output(raw.decode("utf-8-sig"), duration_ms)
            except (OSError, UnicodeError) as exc:
                raise RuntimeError("asr_output_invalid") from exc


def _srt_output(text: str, duration_ms: int) -> dict:
    blocks = re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n").strip())
    if not 1 <= len(blocks) <= 1000:
        raise ValueError("asr_output_invalid")
    cues, previous_end = [], 0
    for index, block in enumerate(blocks):
        lines = block.split("\n")
        if len(lines) < 3 or lines[0].strip() != str(index + 1):
            raise ValueError("asr_output_invalid")
        match = re.fullmatch(r"(\d{2}):([0-5]\d):([0-5]\d),(\d{3}) --> (\d{2}):([0-5]\d):([0-5]\d),(\d{3})", lines[1].strip())
        if match is None:
            raise ValueError("asr_output_invalid")
        values = [int(value) for value in match.groups()]
        start, end = [(values[offset] * 3600 + values[offset + 1] * 60 + values[offset + 2]) * 1000 + values[offset + 3] for offset in (0, 4)]
        cue_text = "\n".join(lines[2:]).strip()
        if not previous_end <= start < end <= duration_ms or not cue_text or len(cue_text) > 500 or "\x00" in cue_text:
            raise ValueError("asr_output_invalid")
        cues.append({"text": cue_text, "start_ms": start, "end_ms": end})
        previous_end = end
    transcript = "\n".join(cue["text"] for cue in cues)
    if len(transcript) > 100_000:
        raise ValueError("asr_output_invalid")
    return {"status": "succeeded", "transcript": transcript, "cues": cues}


def bootstrap() -> None:
    """Opt-in local registration; absence of mmx keeps the provider unavailable."""
    if os.getenv("AICS_ENABLE_MINIMAX_CLI") != "1" or _executable() is None:
        return
    from .content_harness.registry import registry

    entries = (
        ("model_provider", MiniMaxCLIModelAdapter(), "MiniMax local CLI capability adapter"),
        ("image_provider", MiniMaxCLIImageProvider(), "MiniMax local CLI image generation"),
        ("video_provider", MiniMaxCLIVideoProvider(), "MiniMax local CLI video generation"),
        ("tts_provider", MiniMaxCLITTSProvider(), "MiniMax local CLI speech synthesis"),
        ("asr_provider", MiniMaxCLIASRProvider(), "MiniMax local CLI speech transcription"),
    )
    for kind, provider, label in entries:
        if provider.key not in {item.key for item in registry.list(kind)}:
            registry.register(kind, provider.key, provider.version, provider, label=label, human_gate=kind != "model_provider")
