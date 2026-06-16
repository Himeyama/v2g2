from typing import Any

from pydantic import BaseModel


AVAILABLE_MODELS = [
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-3.1-flash-lite",
    "models/gemini-3.1-pro-preview",
    "models/gemini-3-flash-preview",
    "models/gemini-3.5-flash",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it"
]


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
