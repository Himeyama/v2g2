import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from google.genai.errors import ClientError

from ..auth import get_client
from ..vertex import (
    create_cache,
    delete_cache,
    get_cache,
    list_caches,
    update_cache,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _handle_error(exc: Exception, op: str):
    if isinstance(exc, ClientError):
        status_code = exc.code if hasattr(exc, "code") else 500
        status = exc.status if hasattr(exc, "status") else "INTERNAL"
    elif isinstance(exc, ValueError):
        # genai raises ValueError for malformed input validated locally; that
        # is a client error, not an internal failure.
        status_code = 400
        status = "INVALID_ARGUMENT"
    else:
        status_code = 500
        status = "INTERNAL"
    log = logger.warning if status_code < 500 else logger.error
    log("Vertex AI cache %s failed: %s", op, exc, exc_info=status_code >= 500)
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": status_code,
                "message": f"Vertex AI request failed: {exc}",
                "status": status,
            }
        },
    )


@router.post("/cachedContents")
async def create_cached_content(request: Request):
    body: dict[str, Any] = await request.json()
    client = get_client(request.app.state.config)
    try:
        return await create_cache(client, body)
    except Exception as exc:
        raise _handle_error(exc, "create") from exc


@router.get("/cachedContents")
async def list_cached_contents(request: Request):
    client = get_client(request.app.state.config)
    page_size = request.query_params.get("pageSize")
    page_token = request.query_params.get("pageToken")
    try:
        return await list_caches(
            client,
            page_size=int(page_size) if page_size is not None else None,
            page_token=page_token,
        )
    except Exception as exc:
        raise _handle_error(exc, "list") from exc


@router.get("/cachedContents/{cache_id}")
async def get_cached_content(cache_id: str, request: Request):
    client = get_client(request.app.state.config)
    try:
        return await get_cache(client, f"cachedContents/{cache_id}")
    except Exception as exc:
        raise _handle_error(exc, "get") from exc


@router.patch("/cachedContents/{cache_id}")
async def update_cached_content(cache_id: str, request: Request):
    body: dict[str, Any] = await request.json()
    client = get_client(request.app.state.config)
    try:
        return await update_cache(client, f"cachedContents/{cache_id}", body)
    except Exception as exc:
        raise _handle_error(exc, "update") from exc


@router.delete("/cachedContents/{cache_id}")
async def delete_cached_content(cache_id: str, request: Request):
    client = get_client(request.app.state.config)
    try:
        return await delete_cache(client, f"cachedContents/{cache_id}")
    except Exception as exc:
        raise _handle_error(exc, "delete") from exc
