import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from google.genai.errors import ClientError

from ..auth import get_client
from ..vertex import generate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/models/{model}:generateContent")
async def generate_content(model: str, request: Request):
    body: dict[str, Any] = await request.json()
    cfg = request.app.state.config
    client = get_client(cfg)

    try:
        result = await generate(client, model, body)
    except ClientError as exc:
        status_code = exc.code if hasattr(exc, "code") else 500
        log = logger.warning if status_code < 500 else logger.error
        log("Vertex AI request failed for model=%s: %s", model, exc, exc_info=status_code >= 500)
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": {
                    "code": status_code,
                    "message": f"Vertex AI request failed: {exc}",
                    "status": exc.status if hasattr(exc, "status") else "INTERNAL",
                }
            },
        ) from exc
    except ValueError as exc:
        # genai validates the request locally and raises ValueError for
        # malformed input (e.g. "contents are required."). That is a client
        # error, not an internal failure, so report it as 400 INVALID_ARGUMENT.
        logger.warning("Invalid request for model=%s: %s", model, exc)
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": 400,
                    "message": f"Vertex AI request failed: {exc}",
                    "status": "INVALID_ARGUMENT",
                }
            },
        ) from exc
    except Exception as exc:
        logger.error("Vertex AI request failed for model=%s: %s", model, exc, exc_info=True)
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

    return result
