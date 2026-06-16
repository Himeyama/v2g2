import logging

from fastapi import APIRouter, HTTPException, Request
from google.genai.errors import ClientError

from ..auth import get_client
from ..vertex import list_models

router = APIRouter()
logger = logging.getLogger(__name__)


def _handle_error(exc: Exception, op: str):
    if isinstance(exc, ClientError):
        status_code = exc.code if hasattr(exc, "code") else 500
        status = exc.status if hasattr(exc, "status") else "INTERNAL"
    else:
        status_code = 500
        status = "INTERNAL"
    log = logger.warning if status_code < 500 else logger.error
    log("Vertex AI models %s failed: %s", op, exc, exc_info=status_code >= 500)
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


@router.get("/models")
async def list_models_route(request: Request):
    client = get_client(request.app.state.config)
    page_size = request.query_params.get("pageSize")
    page_token = request.query_params.get("pageToken")
    try:
        return await list_models(
            client,
            page_size=int(page_size) if page_size is not None else None,
            page_token=page_token,
        )
    except Exception as exc:
        raise _handle_error(exc, "list") from exc
