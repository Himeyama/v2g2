from typing import Any

from pydantic import BaseModel


class Part(BaseModel):
    text: str | None = None


class Content(BaseModel):
    role: str | None = None
    parts: list[Part]


class GenerateContentRequest(BaseModel):
    contents: list[Content]
    generationConfig: dict[str, Any] | None = None
    systemInstruction: Content | None = None
    tools: list[dict[str, Any]] | None = None
    safetySettings: list[dict[str, Any]] | None = None
