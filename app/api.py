import time
from pydantic import BaseModel, HttpUrl
from fastapi import FastAPI, Response, Request
import uvicorn
import os
from typing import Optional
from model import load_model, model_id
from io import BytesIO
import torch
from __version__ import version
import logging

host = os.environ.get("HOST", "*")
port = int(os.environ.get("PORT", "8000"))
salad_machine_id = os.getenv("SALAD_MACHINE_ID", "")
salad_container_group_id = os.getenv("SALAD_CONTAINER_GROUP_ID", "")

start = time.perf_counter()
pipe = load_model(True)
end = time.perf_counter()
print(f"Initialized ASR Pipeline in {end - start} seconds", flush=True)


def get_gpu_name():
    if torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    else:
        return "CUDA is not available"


gpu_name = get_gpu_name()

default_response_headers = {
    "X-Salad-Machine-ID": salad_machine_id,
    "X-Salad-Container-Group-ID": salad_container_group_id,
    "X-GPU-Name": gpu_name,
    "X-Model-ID": model_id,
}

app = FastAPI(
    title="Automatic Speech Recognition API",
    description="A minimalist, performance-oriented inference server for automatic speech recognition.",
    version=version,
)


@app.get("/hc")
async def healthcheck():
    return {"status": "ok", "version": version}


class ASRRequest(BaseModel):
    url: HttpUrl


@app.post("/asr")
async def asr(request: Request, response: Response):
    """
    This endpoint accepts either:
    - A JSON object with a key 'url' pointing to an audio file.
    - Raw bytes of an audio file with a content type starting with 'audio/'.

    The request body should be structured as follows:
    - For JSON: `{"url": "http://example.com/audio.mp3"}`
    - For audio file: The binary content of the file.
    """
    start = time.perf_counter()
    try:
        body = await request.json()
        if "url" not in body:
            raise Exception("Missing required field 'url'")
        pipe_input = body["url"]
    except Exception as e:
        pipe_input = await request.body()
    try:
        result = pipe(pipe_input)
    except Exception as e:
        logging.exception("Error during ASR inference")
        response.status_code = 500
        return {"error": str(e)}
    end = time.perf_counter()
    print(f"Processed ASR request in {end - start} seconds", flush=True)
    audio_len = [ts for ts in result["chunks"][-1]["timestamp"] if ts is not None][-1]
    response.headers.update(default_response_headers)
    response.headers["X-Processing-Time"] = str(end - start)
    response.headers["X-Audio-Length"] = str(audio_len)
    response.headers["X-Realtime-Factor"] = str(audio_len / (end - start))
    return result


if __name__ == "__main__":
    uvicorn.run(app, host=host, port=port)
