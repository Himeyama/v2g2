from fastapi import APIRouter

from ..models import AVAILABLE_MODELS

router = APIRouter()


@router.get("/models")
async def list_models():
    return {
        "models": [{"name": name} for name in AVAILABLE_MODELS]
    }
