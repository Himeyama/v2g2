import json
import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from google.genai.errors import ClientError

from ..auth import get_client
from ..vertex import generate_stream

router = APIRouter()
logger = logging.getLogger(__name__)


def _client_error_to_http(exc: ClientError, model: str) -> HTTPException:
    status_code = exc.code if hasattr(exc, "code") else 500
    log = logger.warning if status_code < 500 else logger.error
    log("Vertex AI stream failed for model=%s: %s", model, exc, exc_info=status_code >= 500)
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": status_code,
                "message": f"Vertex AI request failed: {exc}",
                "status": exc.status if hasattr(exc, "status") else "INTERNAL",
            }
        },
    )


async def _sse_generator(
    first_chunk: dict[str, Any],
    gen: AsyncGenerator[dict[str, Any], None],
    model: str,
) -> AsyncGenerator[str, None]:
    yield f"data: {json.dumps(first_chunk)}\n\n"
    try:
        async for chunk in gen:
            yield f"data: {json.dumps(chunk)}\n\n"
    except ClientError as exc:
        raise _client_error_to_http(exc, model)
    except Exception as exc:
        logger.error("Vertex AI stream failed mid-stream for model=%s: %s", model, exc, exc_info=True)
        raise
    yield "data: [DONE]\n\n"


@router.post("/models/{model}:streamGenerateContent")
async def stream_generate_content(model: str, request: Request):
    body: dict[str, Any] = await request.json()
    cfg = request.app.state.config
    client = get_client(cfg)

    gen = generate_stream(client, model, body)
    try:
        first_chunk = await gen.__anext__()
    except StopAsyncIteration:
        return StreamingResponse(iter([]), media_type="text/event-stream")
    except ClientError as exc:
        raise _client_error_to_http(exc, model) from exc
    except Exception as exc:
        logger.error("Vertex AI stream failed for model=%s: %s", model, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": 500,
                    "message": f"Vertex AI request failed: {exc}",
                    "status": "INTERNAL",
                }
            },
        ) from exc

    return StreamingResponse(
        _sse_generator(first_chunk, gen, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
