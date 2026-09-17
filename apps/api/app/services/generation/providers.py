"""LLM Provider 抽象（STU-070/071/072）。

业务层只面向 LLMProvider 协议与 provider 名称，禁止 if minimax 之类分支。
MockProvider 保证无 API Key 时主链路（含原型验收 EPIC-14）可完整走通。
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from ...config import get_settings
from ...models import LLMRun

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


@dataclass
class GenerateRequest:
    purpose: str  # generate / fact_review / rewrite_selection
    channel: str | None
    system_prompt: str
    user_prompt: str
    schema_hint: str = ""
    context: dict[str, Any] | None = None  # mock provider 使用；真实 provider 只看 prompt


@dataclass
class GenerateResult:
    data: dict[str, Any]
    raw_output: str
    usage: dict[str, Any]


class LLMProvider(Protocol):
    name: str

    async def generate_json(self, request: GenerateRequest) -> GenerateResult: ...

    async def generate_text(self, request: GenerateRequest) -> str: ...


# ---------- JSON 解析与一次修复（STU-072：不允许无限 retry） ----------

_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def parse_llm_json(raw: str) -> dict[str, Any]:
    for attempt_text in (raw, _repair_attempt(raw)):
        candidate = attempt_text.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        return data
    raise LLMError("模型输出无法解析为 JSON（含一次修复尝试）")


def _repair_attempt(raw: str) -> str:
    return _TRAILING_COMMA.sub(r"\1", raw)


# ---------- Mock Provider ----------


class MockProvider:
    name = "mock"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_json(self, request: GenerateRequest) -> GenerateResult:
        from . import mock_content

        data = mock_content.build_structured_output(request, inject_unfact=self.settings.mock_inject_unfact_number)
        raw = json.dumps(data, ensure_ascii=False, indent=2)
        return GenerateResult(
            data=data,
            raw_output=raw,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "mock": True},
        )

    async def generate_text(self, request: GenerateRequest) -> str:
        return request.user_prompt


# ---------- OpenAI 兼容 Provider（minimax / openai / 任意兼容网关） ----------


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        if not (base_url and api_key and model):
            raise LLMError("openai_compatible provider 需要 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def _chat(self, request: GenerateRequest) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "temperature": 0.4,
        }
        if request.schema_hint:
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def generate_json(self, request: GenerateRequest) -> GenerateResult:
        body = await self._chat(request)
        raw = body["choices"][0]["message"]["content"]
        return GenerateResult(
            data=parse_llm_json(raw),
            raw_output=raw,
            usage=body.get("usage", {}),
        )

    async def generate_text(self, request: GenerateRequest) -> str:
        body = await self._chat(request)
        return body["choices"][0]["message"]["content"]


# ---------- Registry ----------

_providers: dict[str, LLMProvider] = {}


def get_provider() -> LLMProvider:
    settings = get_settings()
    name = settings.llm_provider
    if name not in _providers:
        if name == "mock":
            _providers[name] = MockProvider()
        elif name == "openai_compatible":
            _providers[name] = OpenAICompatibleProvider(
                settings.llm_base_url, settings.llm_api_key, settings.llm_model
            )
        else:
            raise LLMError(f"未知 provider: {name}")
    return _providers[name]


def provider_model_name() -> str:
    settings = get_settings()
    if settings.llm_provider == "openai_compatible":
        return settings.llm_model
    return "mock-structured-v1"


def input_hash(request: GenerateRequest) -> str:
    payload = json.dumps(
        {"purpose": request.purpose, "system": request.system_prompt, "user": request.user_prompt},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def record_run(db, request: GenerateRequest, result: GenerateResult | None, error: str | None = None) -> LLMRun:
    run = LLMRun(
        provider=get_settings().llm_provider,
        model=provider_model_name(),
        purpose=request.purpose,
        input_hash=input_hash(request),
        raw_output=result.raw_output if result else None,
        parsed_output_json=result.data if result else None,
        usage_json=result.usage if result else None,
        status="succeeded" if result else "failed",
        error=error,
    )
    db.add(run)
    db.flush()
    return run
