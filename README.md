# asr-api
A minimalist, performance-oriented server for automatic speech recognition

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

## Docker Images

- `saladtechnologies/asr-api:latest`, `saladtechnologies/asr-api:0.0.2` - The base image, no models included. Does not support flash attention 2, but is a smaller base image.
- `saladtechnologies/asr-api:latest-fa2` ,`saladtechnologies/asr-api:0.0.2-fa2` - The base image, no models included. Supports flash attention 2, but is a larger base image.
- `saladtechnologies/asr-api:latest-openai-whisper-large-v3`, `saladtechnologies/asr-api:0.0.2-openai-whisper-large-v3` - The base image, with the [OpenAI Whisper Large v3](openai/whisper-large-v3) model included. Does not support flash attention 2.
- `saladtechnologies/asr-api:latest-fa2-openai-whisper-large-v3`, `saladtechnologies/asr-api:0.0.2-fa2-openai-whisper-large-v3` - The base image, with the [OpenAI Whisper Large v3](openai/whisper-large-v3) model included. Supports flash attention 2.
- `saladtechnologies/asr-api:latest-distil-whisper-distil-large-v2`, `saladtechnologies/asr-api:0.0.2-distil-whisper-distil-large-v2` - The base image, with the [Distil Whisper Distil Large v2](https://huggingface.co/distil-whisper/distil-large-v2) model included. Does not support flash attention 2.
- `saladtechnologies/asr-api:latest-fa2-distil-whisper-distil-large-v2`, `saladtechnologies/asr-api:0.0.2-fa2-distil-whisper-distil-large-v2` - The base image, with the [Distil Whisper Distil Large v2](https://huggingface.co/distil-whisper/distil-large-v2) model included. Supports flash attention 2.
