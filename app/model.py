from transformers import (
    AutoModelForSpeechSeq2Seq,
    AutoProcessor,
    AutoModelForCausalLM,
    pipeline,
)
import torch
import os
import time

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = os.environ.get("MODEL_ID", "openai/whisper-large-v2")
assistant_model_id = os.environ.get(
    "ASSISTANT_MODEL_ID", "distil-whisper/distil-large-v2"
)
cache_dir = os.environ.get("CACHE_DIR", "/data")


def load_model():
    print(f"Loading model {model_id} on device {device}", flush=True)
    start = time.perf_counter()
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        use_flash_attention_2=True,
        cache_dir=cache_dir,
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
    end = time.perf_counter()
    print(f"Loaded model in {end - start} seconds", flush=True)

    print(
        f"Loading assistant model {assistant_model_id} on device {device}", flush=True
    )
    start = time.perf_counter()
    assistant_model = AutoModelForCausalLM.from_pretrained(
        assistant_model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        use_flash_attention_2=True,
        cache_dir=cache_dir,
    )
    assistant_model.to(device)
    end = time.perf_counter()
    print(f"Loaded assistant model in {end - start} seconds", flush=True)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=30,
        generate_kwargs={"assistant_model": assistant_model},
        torch_dtype=torch_dtype,
        device=device,
    )

    return pipe
