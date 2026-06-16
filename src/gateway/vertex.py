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
        content = types.Content(parts=parts)
        if "role" in c:
            content.role = c["role"]
        result.append(content)
    return result


def response_to_dict(response: types.GenerateContentResponse) -> dict[str, Any]:
    candidates = []
    for cand in response.candidates or []:
        parts = []
        if cand.content and cand.content.parts:
            for part in cand.content.parts:
                if part.text is not None:
                    parts.append({"text": part.text})
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
        result["usageMetadata"] = {
            "promptTokenCount": meta.prompt_token_count,
            "candidatesTokenCount": meta.candidates_token_count,
            "totalTokenCount": meta.total_token_count,
        }

    return result


async def generate(
    client: genai.Client,
    model: str,
    request_body: dict[str, Any],
) -> dict[str, Any]:
    contents = build_contents(request_body.get("contents", []))

    config_dict = request_body.get("generationConfig") or {}
    gen_config = types.GenerateContentConfig(**config_dict) if config_dict else None

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

    config_dict = request_body.get("generationConfig") or {}
    gen_config = types.GenerateContentConfig(**config_dict) if config_dict else None

    async for chunk in await client.aio.models.generate_content_stream(
        model=model,
        contents=contents,
        config=gen_config,
    ):
        yield response_to_dict(chunk)
