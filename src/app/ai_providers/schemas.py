from typing import Literal
from pydantic import BaseModel, Field

ModelProvider = Literal[
    "openai",
    "google_genai",
]

class ProviderModel(BaseModel): 
    id: str 
    label: str 
    note: str | None = None

class Provider(BaseModel): 
    id: ModelProvider 
    label: str 
    base_url: str 
    key_prefix: str 
    key_hint: str 
    docs_url: str 
    models: list[ProviderModel] = Field(default_factory=list)

class TestConnectionRequest(BaseModel):
    api_key: str
    provider: ModelProvider
    model: str

class TestConnectionResponse(BaseModel):
    connection_successful: bool
    provider: ModelProvider
    model: str