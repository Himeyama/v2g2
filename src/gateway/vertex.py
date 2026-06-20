from typing import Any

from google import genai
from google.genai import types


def build_contents(raw_contents: list[dict[str, Any]]) -> list[types.Content]:
    result = []
    for c in raw_contents:
        parts = []
        for p in c.get("parts", []):
            if "text" in p:
                parts.append(types.Part(text=p["text"]))
            elif "functionCall" in p:
                fc = p["functionCall"]
                parts.append(
                    types.Part(
                        function_call=types.FunctionCall(
                            name=fc.get("name"),
                            args=fc.get("args"),
                        )
                    )
                )
            elif "functionResponse" in p:
                fr = p["functionResponse"]
                parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fr.get("name"),
                            response=fr.get("response"),
                        )
                    )
                )
        # The Gemini Developer API treats ``role`` as optional and defaults a
        # missing role to "user"; Vertex AI rejects content without a valid
        # role ("Please use a valid role: user, model."). Mirror the Developer
        # API default so single-turn requests that omit the role still work.
        content = types.Content(parts=parts, role=c.get("role", "user"))
        result.append(content)
    return result


def _sanitize_schema(node: Any) -> Any:
    """Make JSON-schema function parameters acceptable to Vertex AI.

    Vertex rejects an ``anyOf`` node that has any sibling fields set. Clients
    (e.g. Pydantic ``Optional[...]``) commonly emit ``{"anyOf": [...],
    "description": ...}``. Collapse the common nullable pattern, and otherwise
    keep ``anyOf`` as the sole key as Vertex requires.
    """
    if isinstance(node, list):
        return [_sanitize_schema(n) for n in node]
    if not isinstance(node, dict):
        return node

    node = {k: _sanitize_schema(v) for k, v in node.items()}

    any_of_key = next((k for k in ("anyOf", "any_of") if k in node), None)
    if any_of_key is None:
        return node

    members = node[any_of_key] or []
    non_null = [
        m
        for m in members
        if not (isinstance(m, dict) and str(m.get("type", "")).lower() == "null")
    ]
    had_null = len(non_null) != len(members)

    if len(non_null) == 1:
        # Collapse into a single schema, preserving siblings like description.
        merged = {k: v for k, v in node.items() if k != any_of_key}
        for k, v in non_null[0].items():
            merged.setdefault(k, v)
        if had_null:
            merged["nullable"] = True
        return merged

    # Multiple variants: Vertex requires anyOf to be the only field set.
    return {any_of_key: non_null}


def _sanitize_tools(tools: list[Any]) -> list[Any]:
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        decls = tool.get("functionDeclarations") or tool.get("function_declarations")
        for decl in decls or []:
            if isinstance(decl, dict) and "parameters" in decl:
                decl["parameters"] = _sanitize_schema(decl["parameters"])
    return tools


def build_config(request_body: dict[str, Any]) -> types.GenerateContentConfig | None:
    config_dict = dict(request_body.get("generationConfig") or {})
    if "tools" in request_body:
        tools = request_body["tools"]
        tools = tools if isinstance(tools, list) else [tools]
        config_dict["tools"] = _sanitize_tools(tools)
    if "toolConfig" in request_body:
        config_dict["tool_config"] = request_body["toolConfig"]
    if "systemInstruction" in request_body:
        config_dict["system_instruction"] = request_body["systemInstruction"]
    if "cachedContent" in request_body:
        config_dict["cached_content"] = request_body["cachedContent"]
    return types.GenerateContentConfig(**config_dict) if config_dict else None


def response_to_dict(response: types.GenerateContentResponse) -> dict[str, Any]:
    candidates = []
    for cand in response.candidates or []:
        parts = []
        if cand.content and cand.content.parts:
            for part in cand.content.parts:
                if part.function_call is not None:
                    fc = part.function_call
                    parts.append(
                        {
                            "functionCall": {
                                "name": fc.name,
                                "args": dict(fc.args) if fc.args else {},
                            }
                        }
                    )
                elif part.function_response is not None:
                    fr = part.function_response
                    parts.append(
                        {
                            "functionResponse": {
                                "name": fr.name,
                                "response": fr.response,
                            }
                        }
                    )
                elif part.text:
                    text_part: dict[str, Any] = {"text": part.text}
                    if part.thought:
                        text_part["thought"] = True
                    parts.append(text_part)
        finish_reason = None
        if cand.finish_reason is not None:
            finish_reason = cand.finish_reason.name if hasattr(cand.finish_reason, "name") else str(cand.finish_reason)
        entry: dict[str, Any] = {
            "content": {
                "role": cand.content.role if cand.content else "model",
                "parts": parts,
            }
        }
        if finish_reason:
            entry["finishReason"] = finish_reason
        candidates.append(entry)

    result: dict[str, Any] = {"candidates": candidates}

    if response.usage_metadata:
        meta = response.usage_metadata
        usage: dict[str, Any] = {
            "promptTokenCount": meta.prompt_token_count,
            "candidatesTokenCount": meta.candidates_token_count,
            "totalTokenCount": meta.total_token_count,
        }
        if meta.cached_content_token_count is not None:
            usage["cachedContentTokenCount"] = meta.cached_content_token_count
        if meta.thoughts_token_count is not None:
            usage["thoughtsTokenCount"] = meta.thoughts_token_count
        result["usageMetadata"] = usage

    return result


def model_to_dict(model: types.Model) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if model.name is not None:
        # Vertex returns paths like "publishers/google/models/gemini-2.0-flash";
        # the Gemini Developer API exposes them as "models/<id>".
        model_id = model.name.rsplit("/", 1)[-1]
        result["name"] = f"models/{model_id}"
    if model.version is not None:
        result["version"] = model.version
    if model.display_name is not None:
        result["displayName"] = model.display_name
    if model.description is not None:
        result["description"] = model.description
    if model.input_token_limit is not None:
        result["inputTokenLimit"] = model.input_token_limit
    if model.output_token_limit is not None:
        result["outputTokenLimit"] = model.output_token_limit
    if model.supported_actions is not None:
        result["supportedGenerationMethods"] = model.supported_actions
    if model.temperature is not None:
        result["temperature"] = model.temperature
    if model.max_temperature is not None:
        result["maxTemperature"] = model.max_temperature
    if model.top_p is not None:
        result["topP"] = model.top_p
    if model.top_k is not None:
        result["topK"] = model.top_k
    return result


async def list_models(
    client: genai.Client,
    page_size: int | None = None,
    page_token: str | None = None,
) -> dict[str, Any]:
    config_dict: dict[str, Any] = {}
    if page_size is not None:
        config_dict["page_size"] = page_size
    if page_token is not None:
        config_dict["page_token"] = page_token
    pager = await client.aio.models.list(config=config_dict or None)

    result: dict[str, Any] = {
        "models": [model_to_dict(m) for m in pager.page],
    }
    next_token = pager.config.get("page_token")
    if next_token:
        result["nextPageToken"] = next_token
    return result


def build_cache_config(request_body: dict[str, Any]) -> types.CreateCachedContentConfig:
    config_dict: dict[str, Any] = {}
    if "contents" in request_body:
        config_dict["contents"] = build_contents(request_body["contents"])
    if "systemInstruction" in request_body:
        config_dict["system_instruction"] = request_body["systemInstruction"]
    if "tools" in request_body:
        tools = request_body["tools"]
        tools = tools if isinstance(tools, list) else [tools]
        config_dict["tools"] = _sanitize_tools(tools)
    if "toolConfig" in request_body:
        config_dict["tool_config"] = request_body["toolConfig"]
    if "ttl" in request_body:
        config_dict["ttl"] = request_body["ttl"]
    if "expireTime" in request_body:
        config_dict["expire_time"] = request_body["expireTime"]
    if "displayName" in request_body:
        config_dict["display_name"] = request_body["displayName"]
    return types.CreateCachedContentConfig(**config_dict)


def _format_time(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def cached_content_to_dict(cc: types.CachedContent) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if cc.name is not None:
        result["name"] = cc.name
    if cc.model is not None:
        result["model"] = cc.model
    if cc.display_name is not None:
        result["displayName"] = cc.display_name
    if cc.create_time is not None:
        result["createTime"] = _format_time(cc.create_time)
    if cc.update_time is not None:
        result["updateTime"] = _format_time(cc.update_time)
    if cc.expire_time is not None:
        result["expireTime"] = _format_time(cc.expire_time)
    if cc.usage_metadata is not None:
        result["usageMetadata"] = {
            "totalTokenCount": cc.usage_metadata.total_token_count,
        }
    return result


async def create_cache(
    client: genai.Client,
    request_body: dict[str, Any],
) -> dict[str, Any]:
    model = request_body["model"]
    config = build_cache_config(request_body)
    cc = await client.aio.caches.create(model=model, config=config)
    return cached_content_to_dict(cc)


async def get_cache(client: genai.Client, name: str) -> dict[str, Any]:
    cc = await client.aio.caches.get(name=name)
    return cached_content_to_dict(cc)


async def list_caches(
    client: genai.Client,
    page_size: int | None = None,
    page_token: str | None = None,
) -> dict[str, Any]:
    config_dict: dict[str, Any] = {}
    if page_size is not None:
        config_dict["page_size"] = page_size
    if page_token is not None:
        config_dict["page_token"] = page_token
    pager = await client.aio.caches.list(config=config_dict or None)

    result: dict[str, Any] = {
        "cachedContents": [cached_content_to_dict(cc) for cc in pager.page],
    }
    next_token = pager.config.get("page_token")
    if next_token:
        result["nextPageToken"] = next_token
    return result


async def update_cache(
    client: genai.Client,
    name: str,
    request_body: dict[str, Any],
) -> dict[str, Any]:
    config_dict: dict[str, Any] = {}
    if "ttl" in request_body:
        config_dict["ttl"] = request_body["ttl"]
    if "expireTime" in request_body:
        config_dict["expire_time"] = request_body["expireTime"]
    config = types.UpdateCachedContentConfig(**config_dict)
    cc = await client.aio.caches.update(name=name, config=config)
    return cached_content_to_dict(cc)


async def delete_cache(client: genai.Client, name: str) -> dict[str, Any]:
    await client.aio.caches.delete(name=name)
    return {}


async def generate(
    client: genai.Client,
    model: str,
    request_body: dict[str, Any],
) -> dict[str, Any]:
    contents = build_contents(request_body.get("contents", []))
    gen_config = build_config(request_body)

    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=gen_config,
    )
    return response_to_dict(response)


async def generate_stream(
    client: genai.Client,
    model: str,
    request_body: dict[str, Any],
):
    contents = build_contents(request_body.get("contents", []))
    gen_config = build_config(request_body)

    stream = await client.aio.models.generate_content_stream(
        model=model,
        contents=contents,
        config=gen_config,
    )
    async for chunk in stream:
        yield response_to_dict(chunk)
