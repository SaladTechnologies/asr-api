import time
from pydantic import BaseModel
from fastapi import FastAPI, Response
import uvicorn
import os
from typing import Optional
from model import load_model
from __version__ import version

host = os.environ.get("HOST", "*")
port = os.environ.get("PORT", "8000")
port = int(port)

start = time.perf_counter()
pipe = load_model()
end = time.perf_counter()
print(f"Initialized ASR Pipeline in {end - start} seconds", flush=True)

app = FastAPI()


@app.get("/hc")
async def healthcheck():
    return {"status": "ok", "version": version}


class ASRRequest(BaseModel):
    url: str


@app.post("/asr")
async def asr(request: ASRRequest, response: Response):
    start = time.perf_counter()
    try:
        result = pipe(request.url)
    except Exception as e:
        response.status_code = 500
        return {"error": str(e)}
    end = time.perf_counter()
    print(f"Processed ASR request in {end - start} seconds", flush=True)
    response.headers["X-Processing-Time"] = str(end - start)
    return result


if __name__ == "__main__":
    uvicorn.run(app, host=host, port=port)
