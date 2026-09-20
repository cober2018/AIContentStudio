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


_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


def parse_llm_json(raw: str) -> dict[str, Any]:
    # 思考模型（MiniMax-M3 / DeepSeek-R1 等）把 reasoning 以 <think> 内联在 content 里
    raw = _THINK_BLOCK.sub("", raw)
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

        inject = bool(effective_llm_config().get("mock_inject_unfact_number", False))
        data = mock_content.build_structured_output(request, inject_unfact=inject)
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
        # 思考模型（MiniMax-M3 等）会把 <think> 推理内联在正文里，文本场景同样要剥掉
        return _THINK_BLOCK.sub("", body["choices"][0]["message"]["content"]).strip()


# ---------- Registry ----------

# 按解析后的配置档缓存 provider 实例；配置变更时整体失效
_providers: dict[str, LLMProvider] = {}

# 场景路由键：内容生成 / 选区改写 / 事实校验与审核复核 / 选题发现（基于 FactPack 荐题）
ROUTE_KEYS = ("generate", "rewrite", "fact_check", "topic_discovery")


def _models_override() -> dict:
    """system_settings 里 models key 的运行时覆盖（profiles + routes）。"""
    from ... import runtime_config

    return runtime_config.get_runtime(runtime_config.KEY_MODELS) or {}


def _profile_config(name: str, profiles: dict) -> dict | None:
    profile = profiles.get(name)
    if not isinstance(profile, dict):
        return None
    return {
        "provider": profile.get("provider", "mock"),
        "base_url": profile.get("base_url", ""),
        "api_key": profile.get("api_key", ""),
        "model": profile.get("model", ""),
        "mock_inject_unfact_number": profile.get("mock_inject_unfact_number", False),
    }


def effective_llm_config(purpose: str | None = None) -> dict:
    """按场景解析生效 LLM 配置。

    优先级：models.routes[purpose] 指向的启用 profile → 旧 llm 覆盖 → .env 环境变量。
    purpose=None 时取默认（旧 llm 覆盖 / env），与既有行为兼容。
    """
    from ... import runtime_config

    override = runtime_config.get_runtime(runtime_config.KEY_LLM) or {}
    fallback = {
        "provider": override.get("provider", get_settings().llm_provider),
        "base_url": override.get("base_url", get_settings().llm_base_url),
        "api_key": override.get("api_key", get_settings().llm_api_key),
        "model": override.get("model", get_settings().llm_model),
        "mock_inject_unfact_number": override.get(
            "mock_inject_unfact_number", get_settings().mock_inject_unfact_number
        ),
    }
    if purpose:
        models = _models_override()
        route_name = (models.get("routes") or {}).get(purpose)
        if route_name:
            raw_profile = (models.get("profiles") or {}).get(route_name) or {}
            if raw_profile and raw_profile.get("enabled", True):
                profile = _profile_config(route_name, models.get("profiles") or {})
                if profile and profile["provider"]:
                    profile["profile"] = route_name
                    return profile
    fallback["profile"] = "default"
    return fallback


def reset_provider_cache() -> None:
    """配置变更后使已构建的 provider 实例失效（按配置档名缓存）。"""
    _providers.clear()


def get_provider(purpose: str | None = None) -> LLMProvider:
    config = effective_llm_config(purpose)
    cache_key = config.get("profile") or "default"
    if cache_key not in _providers:
        name = config["provider"]
        if name == "mock":
            _providers[cache_key] = MockProvider()
        elif name == "openai_compatible":
            _providers[cache_key] = OpenAICompatibleProvider(
                config["base_url"], config["api_key"], config["model"]
            )
        else:
            raise LLMError(f"未知 provider: {name}")
    return _providers[cache_key]


def provider_model_name(purpose: str | None = None) -> str:
    config = effective_llm_config(purpose)
    if config["provider"] == "openai_compatible":
        return config["model"]
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
        provider=effective_llm_config()["provider"],
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
