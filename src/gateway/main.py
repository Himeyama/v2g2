import json
import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response

from .config import load_config
from .routes.generate import router as generate_router
from .routes.models import router as models_router
from .routes.stream import router as stream_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.config = load_config()
    yield


app = FastAPI(title="Gemini Gateway", lifespan=lifespan)

app.include_router(models_router, prefix="/v1beta")
app.include_router(generate_router, prefix="/v1beta")
app.include_router(stream_router, prefix="/v1beta")


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    start = time.monotonic()
    response = await call_next(request)
    latency_ms = int((time.monotonic() - start) * 1000)

    model = request.path_params.get("model", "")

    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": request.method,
        "path": request.url.path,
        "model": model,
        "latency_ms": latency_ms,
        "status": response.status_code,
    }
    print(json.dumps(log_entry), flush=True)

    return response


if __name__ == "__main__":
    config = load_config()
    uvicorn.run(
        "gateway.main:app",
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )
