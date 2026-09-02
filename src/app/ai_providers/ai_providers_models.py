from src.app.ai_providers.schemas import ProviderModel, Provider

SUPPORTED_PROVIDERS_MODELS = [
    Provider(
        id="openai",
        label="OpenAI",
        base_url="https://platform.openai.com",
        key_prefix="sk-",
        key_hint="Starts with sk- — created at platform.openai.com",
        docs_url="https://platform.openai.com/api-keys",
        models=[
            ProviderModel(
                id="gpt-5.5",
                label="GPT-5.5",
            ),
            ProviderModel(
                id="gpt-5.4",
                label="GPT-5.4",
            ),
            ProviderModel(
                id="gpt-5.4-mini",
                label="GPT-5.4 mini",
            ),
        ],
    ),
    Provider(
        id="google_genai",
        label="Google Gemini",
        base_url="https://aistudio.google.com",
        key_prefix="AQ",
        key_hint="Starts with AQ. — created at aistudio.google.com",
        docs_url="https://aistudio.google.com/api-keys",
        models=[
            ProviderModel(
                id="gemini-3.7-flash",
                label="Gemini 3.7 Flash",
            ),
            ProviderModel(
                id="gemini-3.6-flash",
                label="Gemini 3.6 Flash",
            ),
            ProviderModel(
                id="gemini-3.5-flash",
                label="Gemini 3.5 Flash",
            ),
            ProviderModel(
                id="gemini-3.5-flash-lite",
                label="Gemini 3.5 Flash Lite",
            ),
            ProviderModel(
                id="gemini-3.1-flash-lite",
                label="Gemini 3.1 Flash Lite",
            ),
            ProviderModel(
                id="gemini-3-flash",
                label="Gemini 3 Flash",
            ),
            ProviderModel(
                id="gemini-2.5-pro",
                label="Gemini 2.5 Pro",
            ),
            ProviderModel(
                id="gemini-2.5-flash",
                label="Gemini 2.5 Flash",
            ),
        ],
    ),
]