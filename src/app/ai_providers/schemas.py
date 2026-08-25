from typing import Literal
from pydantic import BaseModel, Field

ModelProvider = Literal[
    "openai",
    "google_genai",
]

class SupportedModels(BaseModel):
    openai: list[str] = Field(default_factory=list)
    google_genai: list[str] = Field(default_factory=list)

class ModelProviderResponse(BaseModel):
    provider: ModelProvider
    models: list[str]

class TestConnectionRequest(BaseModel):
    api_key: str
    provider: ModelProvider
    model: str

class TestConnectionResponse(BaseModel):
    connection_successful: bool
    provider: ModelProvider
    model: str