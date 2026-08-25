# LeafLens API

LeafLens is a FastAPI service for plant and crop image analysis. It validates an uploaded image, sends it to a selected vision-capable AI provider, and returns a structured crop-health assessment with detected diseases and treatment recommendations.

## Features

- Crop disease and health analysis from JPEG, PNG, and WebP images
- OpenAI and Google Gemini(google_genai) provider integrations
- Provider/model discovery and connection checks
- Structured responses for safety gating, severity, diseases, treatments, and notes
- Redis-backed, IP-based rate limiting
- Automatic in-memory image resizing before analysis

## Requirements

- Python 3.10 or newer
- Redis running locally or reachable from the application
- An API key for the provider you want to use

## Setup

From the repository root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Edit `.env` and provide the Redis connection values. The application checks Redis during startup, so Redis must be available before the API is launched.

```dotenv
ENVIRONMENT="dev"
DEBUG=false
LOG_TO_FILE=true

REDIS_CONFIG__REDIS_HOST=localhost
REDIS_CONFIG__REDIS_PORT=6379
REDIS_CONFIG__REDIS_DB=0
REDIS_CONFIG__REDIS_USERNAME=
REDIS_CONFIG__REDIS_PASSWORD=

FRONTEND_URL=http://localhost:3000
```

## Run the API

```powershell
uvicorn src.app.main:app --reload
```

The API is available at `http://localhost:8000`. In non-production environments, interactive documentation is available at [`/docs`](http://localhost:8000/docs) and [`/redoc`](http://localhost:8000/redoc).

## API

All feature routes use the `/api/v1` prefix.

### Health checks

```http
GET /
GET /health
```

### List supported providers and models

```http
GET /api/v1/ai/providers/
```

The currently configured providers are:

- `openai`: `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`
- `google_genai`: `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3-flash`, `gemini-2.5-pro`, `gemini-2.5-flash`

### Test a provider connection

```http
POST /api/v1/ai/providers/test-connection
Content-Type: application/json
```

```json
{
	"provider": "openai",
	"model": "gpt-5.4-mini",
	"api_key": "your-provider-api-key"
}
```

### Analyze an image

```http
POST /api/v1/analyze/
Content-Type: multipart/form-data
```

Required form fields:

- `file`: JPEG, PNG, or WebP image
- `provider`: `openai` or `google_genai`
- `model`: a model returned by the provider discovery endpoint
- `api_key`: the provider API key

Example with `curl`:

```bash
curl -X POST http://localhost:8000/api/v1/analyze/ \
	-F "file=@demo_images/leaf.jpg" \
	-F "provider=openai" \
	-F "model=gpt-5.4-mini" \
	-F "api_key=your-provider-api-key"
```

The response includes the original file metadata, provider/model selection, and a structured `result` containing fields such as `is_plant_image`, `is_safe`, `crop_detected`, `severity`, `diseases`, `treatments`, and `overall_health`.

## Image limits

- Accepted MIME types: `image/jpeg`, `image/png`, `image/webp`
- Maximum upload size: 5 MB
- Minimum dimensions: 100 x 100 pixels
- Maximum input dimension: 8000 pixels
- Images larger than 2048 pixels on either side are resized in memory

Images are processed in memory and are not written to disk by the analysis service.

## Rate limiting

Rate limits are applied per client IP and stored in Redis:

- Analysis routes: 10 requests per 60 seconds
- Other API routes: 60 requests per 60 seconds
- `GET /` and `GET /health` are not rate limited

    To apply rate limit to `GET /` and `GET /health` endpoints, comment below code form line **176** in `src/app/middleware/rate_limit.py` file.
    ```python
    if scope["path"] in SKIP_RATE_LIMIT_PATHS:   # early exit, zero Redis calls
            return None
    ```       

Rate-limited responses return HTTP `429` and include `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.

## Project layout

```text
src/app/
├── analyze/          Image validation and crop analysis
├── ai_providers/     Provider and model discovery/connection checks
├── common/           Shared response builders and examples
├── core/             Configuration, Redis, logging, exceptions, prompts
└── middleware/       Rate-limit middleware
```

## Production notes

- Set `ENVIRONMENT=prod` to disable the built-in Swagger and ReDoc routes.
- Do not commit `.env` or provider API keys.
- Configure the reverse proxy to set `X-Forwarded-For` or `X-Real-IP` correctly so IP rate limiting identifies clients as intended.
