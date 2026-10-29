"""Loudness mastering for finished voice/mix tracks before the video edit."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
import wave

from fastapi import HTTPException

_MAX_BYTES = 30 * 1024 * 1024


def _loudnorm(executable, content, audio_filter, output, timeout):
    done = subprocess.run([executable, "-nostdin", "-hide_banner", "-protocol_whitelist", "pipe,file", "-threads", "1",
                           "-i", "pipe:0", "-af", audio_filter, *output], input=content, capture_output=True,
                          timeout=timeout, check=True, env={key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL") if key in os.environ})
    text = done.stderr[-8192:].decode("utf-8", "replace")
    return done.stdout, json.loads(text[text.rindex("{"):text.rindex("}") + 1])


def master_loudness(content: bytes, *, target_lufs: float = -16.0, true_peak_dbtp: float = -1.5) -> tuple[bytes, dict]:
    """Two-pass EBU R128 normalization; dynamic mode acts as the limiter when the peak ceiling needs it."""
    executable = shutil.which("ffmpeg")
    if executable is None or len(content) > _MAX_BYTES:
        raise HTTPException(422, {"code": "audio_mastering_unavailable"})
    try:
        with wave.open(io.BytesIO(content)) as source:
            rate, channels, frames = source.getframerate(), source.getnchannels(), source.getnframes()
        target = f"I={target_lufs}:TP={true_peak_dbtp}:LRA=11"
        _, first = _loudnorm(executable, content, f"loudnorm={target}:print_format=json", ["-f", "null", "-"], 120)
        measured = ":".join(f"{name}={first[key]}" for name, key in (("measured_I", "input_i"), ("measured_TP", "input_tp"),
                            ("measured_LRA", "input_lra"), ("measured_thresh", "input_thresh"), ("offset", "target_offset")))
        # A seekable file keeps complete WAV header sizes, which a pipe cannot.
        with tempfile.NamedTemporaryFile(suffix=".wav") as target_file:
            _, second = _loudnorm(executable, content, f"loudnorm={target}:{measured}:linear=true:print_format=json",
                                  ["-ar", str(rate), "-ac", str(channels), "-c:a", "pcm_s16le", "-fflags", "+bitexact", "-y", target_file.name], 180)
            mastered = target_file.read()
        with wave.open(io.BytesIO(mastered)) as result:
            if result.getnframes() != frames:
                raise ValueError("duration_changed")
    except (OSError, ValueError, KeyError, EOFError, wave.Error, subprocess.SubprocessError):
        raise HTTPException(422, {"code": "audio_mastering_failed"}) from None
    report = {"schema": "studio.audio.loudness-master.v1", "target_lufs": target_lufs, "true_peak_ceiling_dbtp": true_peak_dbtp,
              "input": {"integrated_lufs": float(first["input_i"]), "true_peak_dbtp": float(first["input_tp"]), "lra_lu": float(first["input_lra"])},
              "output": {"integrated_lufs": float(second["output_i"]), "true_peak_dbtp": float(second["output_tp"]), "lra_lu": float(second["output_lra"])},
              "normalization_type": second.get("normalization_type"), "sample_rate": rate, "channels": channels, "frames": frames}
    return mastered, report
