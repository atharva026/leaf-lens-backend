from src.app.ai_providers.schemas import SupportedModels

SUPPORTED_MODELS = SupportedModels(
    openai=[
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
    ],
    gemini=[
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ],
    groq=[
        "qwen/qwen3.6-27b",
    ],
)