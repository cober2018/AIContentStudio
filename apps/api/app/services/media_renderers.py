"""Media renderer lookup: the registered renderer and its code-and-runtime fingerprint, used by automatic graphic rendering."""

import hashlib
import marshal
import re
import types

from fastapi import HTTPException

from . import content_masters
from .content_harness import channel_registry, providers

_HASH = re.compile(r"[0-9a-f]{64}\Z")


def resolve_renderer(key, version):
    try:
        renderer = providers.registry.resolve("renderer", key, version)
        runtime = renderer.runtime_fingerprint()
        function = getattr(renderer.render_master, "__func__", renderer.render_master)
        if (renderer.key != key or renderer.version != version or renderer.modality not in {"graphic", "video"}
                or renderer.schema != f"{renderer.modality}.master.v2" or not isinstance(runtime, str)
                or not _HASH.fullmatch(runtime) or not isinstance(function, types.FunctionType)
                or not isinstance(renderer.output_mimes, tuple) or not renderer.output_mimes
                or not isinstance(renderer.supported_forms, tuple) or not renderer.supported_forms
                or any(not isinstance(form, tuple) or len(form) != 2 or any(not isinstance(part, str) or len(part) > 100 for part in form) for form in renderer.supported_forms)
                or set(renderer.output_mimes) - ({"image/png", "image/jpeg", "image/webp"} if renderer.modality == "graphic" else {"video/mp4"})):
            raise ValueError("unavailable")
        code = marshal.dumps((function.__code__, function.__defaults__, function.__kwdefaults__,
                              tuple(cell.cell_contents for cell in function.__closure__ or ())), 2)
        fingerprint = content_masters._hash({"runtime": runtime, "code": hashlib.sha256(code).hexdigest(),
            "key": key, "version": version, "schema": renderer.schema, "mimes": renderer.output_mimes,
            "forms": renderer.supported_forms})
        return renderer, fingerprint
    except Exception:  # noqa: BLE001 Never expose renderer configuration/errors.
        raise HTTPException(422, "media_renderer_unavailable") from None


def scope_fingerprint(db, renderer, scope):
    try:
        actual, fingerprint = resolve_renderer(scope["renderer_key"], scope["renderer_version"])
        if (actual is not renderer or scope["modality"] != renderer.modality or scope["payload_schema"] != renderer.schema
                or scope["output_mime"] not in renderer.output_mimes
                or (scope["channel"], scope["content_form"]) not in renderer.supported_forms):
            return None
        profile = channel_registry.resolve_content_form(db, scope["channel"], scope["content_form"]).to_dict()
        return content_masters._hash({"implementation": fingerprint, "scope": scope, "profile": profile})
    except (HTTPException, channel_registry.ChannelRegistryError):
        return None
