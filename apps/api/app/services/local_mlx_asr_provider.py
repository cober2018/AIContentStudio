"""Offline MLX bridge; suggestions still require explicit Master acceptance/save."""

from __future__ import annotations

import hashlib
import json
import math
import os
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from ..config import get_settings
from .materials import sniff_mime
from .provider_calls import ProviderCapacityError

KEY = "local.mlx_whisper"
VERSION = "1"
TIMEOUT_SECONDS = 120
_SANDBOX = Path("/usr/bin/sandbox-exec")
_PROFILE = "(version 1) (allow default) (deny network*)"
_JSON_LIMIT = 4 * 1024 * 1024
_slot = threading.BoundedSemaphore(1)
_identity_lock = threading.Lock()
_identity_cache: tuple[tuple, str] | None = None


class LocalASRUnavailable(ValueError):
    pass


def _configuration():
    settings = get_settings()
    if not settings.aics_enable_local_mlx_asr:
        raise LocalASRUnavailable("local_asr_not_enabled")
    if sys.platform != "darwin" or not os.access(_SANDBOX, os.X_OK):
        raise LocalASRUnavailable("local_asr_offline_runtime_unavailable")
    configured = (settings.aics_mlx_asr_python, settings.aics_mlx_asr_worker, settings.aics_mlx_asr_model_dir)
    if not all(value and Path(value).is_absolute() for value in configured):
        raise LocalASRUnavailable("local_asr_configuration_missing")
    python, worker, model = (Path(value) for value in configured)
    if not python.is_file() or not os.access(python, os.X_OK) or not worker.is_file():
        raise LocalASRUnavailable("local_asr_runtime_missing")
    if not model.is_dir() or not (model / "config.json").is_file():
        raise LocalASRUnavailable("local_asr_cached_model_missing")
    weights = model / "weights.safetensors"
    if not weights.is_file():
        weights = model / "weights.npz"
    if not weights.is_file():
        raise LocalASRUnavailable("local_asr_cached_model_missing")
    site = worker.parent
    required = (site / "_mlx_quantize_polyfill.py", site / "mlx_whisper/assets/mel_filters.npz",
                site / "mlx_whisper/assets/gpt2.tiktoken", site / "mlx_whisper/assets/multilingual.tiktoken")
    if not all(path.is_file() for path in required):
        raise LocalASRUnavailable("local_asr_runtime_missing")
    tools = tuple(shutil.which(name) for name in ("ffmpeg", "ffprobe"))
    if not all(tools):
        raise LocalASRUnavailable("local_asr_audio_tools_missing")
    return python, worker, model, weights, tuple(Path(tool) for tool in tools), required


def _runtime_files(configuration):
    python, worker, model, weights, tools, required = configuration
    paths = [Path(__file__), python, worker, model / "config.json", weights, _SANDBOX, *tools, *required]
    venv_config = python.parent.parent / "pyvenv.cfg"
    if venv_config.is_file():
        paths.append(venv_config)
    for package in ("mlx", "mlx_whisper", "numpy", "tiktoken", "huggingface_hub"):
        root = worker.parent / package
        if not root.is_dir():
            raise LocalASRUnavailable("local_asr_runtime_missing")
        for path in root.rglob("*"):
            if "__pycache__" not in path.parts and path.is_file() and path.suffix in {".py", ".so", ".dylib", ".npz", ".tiktoken"}:
                paths.append(path)
                if len(paths) > 20_000:
                    raise LocalASRUnavailable("local_asr_runtime_unbounded")
    return sorted(set(paths), key=str)


def _signature(paths):
    rows = []
    for path in paths:
        stat = path.stat()
        if not 0 <= stat.st_size <= 4 * 1024 ** 3:
            raise LocalASRUnavailable("local_asr_runtime_invalid")
        rows.append((str(path.resolve()), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))
    return tuple(rows)


class LocalMLXASRProvider:
    key = KEY
    version = VERSION

    def option(self):
        try:
            _configuration()
            available, reason = True, "local_asr_ready_not_verified"
        except (LocalASRUnavailable, OSError) as exc:
            available = False
            reason = str(exc) if isinstance(exc, LocalASRUnavailable) else "local_asr_runtime_missing"
        return {"key": self.key, "version": self.version, "label": "本机 MLX Whisper",
                "execution_mode": "local", "available": available, "reason": reason, "verified": False}

    def runtime_fingerprint(self):
        global _identity_cache
        try:
            paths = _runtime_files(_configuration())
            before = _signature(paths)
            with _identity_lock:
                if _identity_cache is not None and _identity_cache[0] == before:
                    return _identity_cache[1]
                digest = hashlib.sha256(f"{KEY}@{VERSION}|{_PROFILE}".encode())
                for path in paths:
                    digest.update(str(path.resolve()).encode())
                    with path.open("rb") as source:
                        for chunk in iter(lambda: source.read(1024 * 1024), b""):
                            digest.update(chunk)
                if _signature(_runtime_files(_configuration())) != before:
                    return None
                value = digest.hexdigest()
                _identity_cache = before, value
                return value
        except (LocalASRUnavailable, OSError):
            return None

    def transcribe(self, request):
        if not _slot.acquire(blocking=False):
            raise ProviderCapacityError
        try:
            return self._transcribe(request)
        finally:
            _slot.release()

    def _transcribe(self, request):
        timeout = request.get("timeout_seconds")
        if type(timeout) not in {int, float} or not math.isfinite(timeout) or not 0 < timeout <= TIMEOUT_SECONDS:
            raise LocalASRUnavailable("local_asr_deadline_invalid")
        # Reserve time to reap processes before the enclosing call releases capacity.
        deadline = time.monotonic() + max(0, timeout - 2)
        content, mime = request.get("source_bytes"), request.get("mime_type")
        duration = request.get("max_duration_ms")
        if (not isinstance(content, bytes) or not 0 < len(content) <= 30 * 1024 * 1024
                or hashlib.sha256(content).hexdigest() != request.get("source_hash")
                or mime not in {"audio/wav", "video/mp4"}
                or sniff_mime(content, None) != mime
                or type(duration) is not int or not 0 < duration <= 600_000):
            raise LocalASRUnavailable("local_asr_source_invalid")
        python, worker, model, _, tools, _ = _configuration()
        identity = self.runtime_fingerprint()
        if identity is None:
            raise LocalASRUnavailable("local_asr_runtime_missing")
        with tempfile.TemporaryDirectory(prefix="aics-local-asr-") as directory:
            root = Path(directory)
            root.chmod(0o700)
            source = root / ("input.wav" if mime == "audio/wav" else "input.mp4")
            source.write_bytes(content)
            source.chmod(0o600)
            environment = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "TMPDIR": str(root),
                           "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "TOKENIZERS_PARALLELISM": "false"}
            probe = _run([str(tools[1]), "-v", "error", "-protocol_whitelist", "file,pipe", "-select_streams", "a:0",
                          "-show_entries", "stream=duration:format=duration", "-of", "json", str(source)],
                         root, environment, deadline)
            try:
                metadata = json.loads(probe)
                actual_duration = float(metadata["format"]["duration"])
                if not metadata.get("streams") or not math.isfinite(actual_duration) or not 0 < actual_duration <= 600:
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                raise LocalASRUnavailable("local_asr_audio_unavailable") from None
            audio = root / "audio.wav"
            _run([str(tools[0]), "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe", "-i", str(source),
                  "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio)],
                 root, environment, deadline)
            output = root / "transcript.json"
            _run([str(python), str(worker), "--audio", str(audio), "--model", str(model), "--lang", "auto",
                  "--output-json", str(output)], root, environment, deadline, output=output)
            if self.runtime_fingerprint() != identity:
                raise LocalASRUnavailable("local_asr_runtime_changed")
            try:
                with output.open("rb") as result:
                    raw = result.read(_JSON_LIMIT + 1)
                if len(raw) > _JSON_LIMIT:
                    raise ValueError
                payload = json.loads(raw)
                if not isinstance(payload, dict) or payload.get("model") != str(model) or payload.get("task") != "transcribe":
                    raise ValueError
                source_duration = math.ceil(actual_duration * 1000)
                return {**_segments(payload.get("segments"), min(duration, source_duration)),
                        "source_duration_ms": source_duration}
            except (ValueError, TypeError, OSError):
                raise LocalASRUnavailable("local_asr_output_invalid") from None


def _run(arguments, root, environment, deadline, *, output=None):
    if time.monotonic() >= deadline:
        raise TimeoutError("local_asr_timeout")
    process = subprocess.Popen([str(_SANDBOX), "-p", _PROFILE, *arguments], cwd=root, env=environment,
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True, umask=0o077)
    stdout = bytearray()
    counts = {process.stdout: 0, process.stderr: 0}
    try:
        with selectors.DefaultSelector() as selector:
            for stream in counts:
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ)
            while selector.get_map() or process.poll() is None:
                if time.monotonic() >= deadline:
                    raise TimeoutError("local_asr_timeout")
                if output is not None and output.exists() and output.stat().st_size > _JSON_LIMIT:
                    raise LocalASRUnavailable("local_asr_output_invalid")
                if any(path.is_file() and path.stat().st_size > 30 * 1024 * 1024 for path in root.iterdir()):
                    raise LocalASRUnavailable("local_asr_temporary_file_limit")
                for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    chunk = os.read(key.fileobj.fileno(), 4096)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    counts[key.fileobj] += len(chunk)
                    limit = 64 * 1024 if key.fileobj is process.stdout else 4096
                    if counts[key.fileobj] > limit:
                        raise LocalASRUnavailable("local_asr_diagnostic_limit")
                    if key.fileobj is process.stdout:
                        stdout.extend(chunk)
        if process.wait() != 0:
            raise LocalASRUnavailable("local_asr_execution_failed")
        return bytes(stdout)
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        process.stdout.close()
        process.stderr.close()


def _segments(segments, duration):
    if not isinstance(segments, list) or not 1 <= len(segments) <= 1000:
        raise ValueError("segments invalid")
    cues, previous = [], 0
    for segment in segments:
        if not isinstance(segment, dict):
            raise TypeError("segment invalid")
        start, end, text = segment.get("start"), segment.get("end"), segment.get("text")
        if (type(start) not in {int, float} or type(end) not in {int, float}
                or not math.isfinite(start) or not math.isfinite(end) or start < 0
                or not isinstance(text, str) or not text.strip() or len(text.strip()) > 500 or "\x00" in text):
            raise ValueError("segment invalid")
        start_ms, end_ms = round(start * 1000), round(end * 1000)
        if not previous <= start_ms < end_ms <= duration:
            raise ValueError("segment times invalid")
        cues.append({"text": text.strip(), "start_ms": start_ms, "end_ms": end_ms})
        previous = end_ms
    transcript = "\n".join(cue["text"] for cue in cues)
    if len(transcript) > 100_000:
        raise ValueError("transcript invalid")
    return {"status": "succeeded", "transcript": transcript, "cues": cues}


def bootstrap(registry):
    if not get_settings().aics_enable_local_mlx_asr:
        return
    if KEY not in {row.key for row in registry.list("asr_provider")}:
        registry.register("asr_provider", KEY, VERSION, LocalMLXASRProvider(), label="本机 MLX Whisper", human_gate=True)
