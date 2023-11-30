# asr-api
A minimalist, performance-oriented inference server for automatic speech recognition. More extensive benchmarks will come soon, but for now, here's some prelimary performance numbers. These numbers are for total round-trip request time, including downloading the audio file, and parsing the response.

**RTX 3080 Ti w/ BetterTransformers**

| Model | Input Audio Length | Realtime Multiple |
| --- | --- | --- |
| [OpenAI Whisper Large v3](openai/whisper-large-v3) | 19 min 51s | 50x |
| [Distil Whisper Distil Large v2](https://huggingface.co/distil-whisper/distil-large-v2) | 19 min 51s | 78x

**RTX 4090 w/ BetterTransformers**

| Model | Input Audio Length | Realtime Multiple |
| --- | --- | --- |
| [OpenAI Whisper Large v3](openai/whisper-large-v3) | 19 min 51s | 68x |
| [Distil Whisper Distil Large v2](https://huggingface.co/distil-whisper/distil-large-v2) | 19 min 51s | 83x

## API

### GET /hc

This healthcheck will not respond until the server is fully ready to accept requests.

#### Response

```json
{
  "status": "ok",
  "version": "0.0.2",
}
```

### POST /asr

#### Request

URL should be a download link to an audio file. Currently only supports mp3, flac, and wav.

```json
{
  "url": "https://example.com/audio.mp3",
}
```

#### Response

```json
{
  "text": "hello world",
  "chunks": [
    {
      "timestamp": [
        0.0,
        2.1
      ],
      "text": "hello world"
    },
  ]
}
```

### GET /docs

Swagger docs for the API.

## Configuration

All configuration is via environment variables.

See documentation for the [ASR Pipeline](https://huggingface.co/docs/transformers/main/en/main_classes/pipelines#transformers.AutomaticSpeechRecognitionPipeline) for more information on the model configuration options:

| Name | Description | Default |
| --- | --- | --- |
| `HOST` | The host to listen on | `*` |
| `PORT` | The port to listen on | `8000` |
| `MODEL_ID` | The model to use. See [Automatic Speech Recognition Models](https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&sort=trending) | `openai/whisper-large-v3` |
| `CACHE_DIR` | The directory to cache models in | `/data` |
| `FLASH_ATTENTION_2` | Whether to use flash attention 2. Must be `1` to enable. Enabled by default in `-fa2` images. Note, if your GPU does not support compute capability >= 8.9, BetterTransformers will be used instead.  | **None** |
| `BATCH_SIZE` | The batch size to use. | `16` |
| `MAX_NEW_TOKENS` | Not sure what this does. | `128` |
| `CHUNK_LENGTH_S` | The length of each chunk in seconds. | `30` |
| `STRIDE_LENGTH_S` | The stride length in seconds. Defaults to 1/6 of `CHUNK_LENGTH_S` | `CHUNK_LENGTH_S` / 6 |


## Docker Images

- `saladtechnologies/asr-api:latest`, `saladtechnologies/asr-api:0.0.2` - The base image, no models included. Does not support flash attention 2, but is a smaller base image. Will download the model at runtime.
- `saladtechnologies/asr-api:latest-fa2` ,`saladtechnologies/asr-api:0.0.2-fa2` - The base image, no models included. Supports flash attention 2, but is a larger base image. Will download the model at runtime.
- `saladtechnologies/asr-api:latest-openai-whisper-large-v3`, `saladtechnologies/asr-api:0.0.2-openai-whisper-large-v3` - The base image, with the [OpenAI Whisper Large v3](openai/whisper-large-v3) model included. Does not support flash attention 2.
- `saladtechnologies/asr-api:latest-fa2-openai-whisper-large-v3`, `saladtechnologies/asr-api:0.0.2-fa2-openai-whisper-large-v3` - The base image, with the [OpenAI Whisper Large v3](openai/whisper-large-v3) model included. Supports flash attention 2.
- `saladtechnologies/asr-api:latest-distil-whisper-distil-large-v2`, `saladtechnologies/asr-api:0.0.2-distil-whisper-distil-large-v2` - The base image, with the [Distil Whisper Distil Large v2](https://huggingface.co/distil-whisper/distil-large-v2) model included. Does not support flash attention 2.
- `saladtechnologies/asr-api:latest-fa2-distil-whisper-distil-large-v2`, `saladtechnologies/asr-api:0.0.2-fa2-distil-whisper-distil-large-v2` - The base image, with the [Distil Whisper Distil Large v2](https://huggingface.co/distil-whisper/distil-large-v2) model included. Supports flash attention 2.
