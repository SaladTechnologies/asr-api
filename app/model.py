from transformers import (
    AutoModelForSpeechSeq2Seq,
    AutoProcessor,
    pipeline,
)
import torch
import os
import time

use_flash_attention_2 = False
flash_attention_user_override = os.environ.get("FLASH_ATTENTION_2", "") == "1"
if torch.cuda.is_available():
    device = "cuda:0"
    torch_dtype = torch.float16
    device_properties = torch.cuda.get_device_properties(0)
    compute_capability = float(f"{device_properties.major}.{device_properties.minor}")
    print(f"GPU Compute Capability: {compute_capability}", flush=True)
    if compute_capability >= 8.9:
        use_flash_attention_2 = flash_attention_user_override and True
else:
    device = "cpu"
    torch_dtype = torch.float32

model_id = os.environ.get("MODEL_ID", "openai/whisper-large-v3")
cache_dir = os.environ.get("CACHE_DIR", "/data")
batch_size = int(os.environ.get("BATCH_SIZE", "16"))
max_new_tokens = int(os.environ.get("MAX_NEW_TOKENS", "128"))
chunk_length_s = int(os.environ.get("CHUNK_LENGTH_S", "30"))
stride_length_s = int(os.environ.get("STRIDE_LENGTH_S", chunk_length_s / 6))


def load_model():
    print(f"Loading model {model_id} on device {device}", flush=True)
    start = time.perf_counter()
    model_kwargs = {
        "torch_dtype": torch_dtype,
        "low_cpu_mem_usage": True,
        "use_safetensors": True,
        "cache_dir": cache_dir,
    }
    if use_flash_attention_2:
        model_kwargs["use_flash_attention_2"] = True

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        **model_kwargs,
    )
    model.to(device)

    if device == "cuda:0" and not use_flash_attention_2:
        model = model.to_bettertransformer()

    processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
    end = time.perf_counter()
    print(f"Loaded model in {end - start} seconds", flush=True)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=chunk_length_s,
        stride_length_s=stride_length_s,
        max_new_tokens=max_new_tokens,
        batch_size=batch_size,
        return_timestamps=True,
        torch_dtype=torch_dtype,
        device=device,
    )

    return pipe
