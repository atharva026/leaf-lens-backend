from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class AnalyzeImageResponse(BaseModel):
    file_name: str
    provider: str
    model: str
    content_type: str
    result: dict

class Severity(str, Enum):
    HEALTHY = "healthy"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class TreatmentType(str, Enum):
    ORGANIC = "organic"
    CHEMICAL = "chemical"
    PREVENTIVE = "preventive"

class Urgency(str, Enum):
    IMMEDIATE = "immediate"
    WITHIN_WEEK = "within_week"
    SEASONAL = "seasonal"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    
class Disease(BaseModel):
    """
    Schema for diseases.
    """
    name: str = Field(..., description="Name of the disease")
    confidence: ConfidenceLevel = Field(..., description="Confidence level of the disease detection")
    description: Optional[str] = Field(None, max_length=500, description="Brief description of the disease and visible symptoms")

class Treatment(BaseModel):
    """
    Schema for recommended treatments.
    """
    treatment_name: str = Field(..., max_length=100, description="Name of the treatment")
    treatment_type: TreatmentType = Field(..., description="Type of treatment")
    instructions: str = Field(..., max_length=1000, description="Step by step treatment instructions")
    urgency: Urgency = Field(..., description="Urgency of applying the treatment")

class CropHealthResponse(BaseModel):
    """
    Schema for crop disease detection and health assessment.
    """
    # Safety / gating fields — always populated, checked first
    is_plant_image: bool = Field(..., description="True only if the image clearly shows a crop, plant, leaf, or agricultural produce")
    is_safe: bool = Field(..., description="False if the image contains harmful, inappropriate, or non-agricultural content")
    rejection_reason: Optional[str] = Field(
        None,
        max_length=300,
        description="Set only when is_plant_image is False or is_safe is False. "
                     "One short, neutral sentence explaining the rejection. "
                     "Never describe harmful content in detail.",
    )

    # Analysis fields — only meaningful when is_plant_image=True and is_safe=True
    crop_detected: str = Field(..., max_length=100, description="Name of the crop or plant visible in the image")
    severity: Severity = Field(None, description="Overall severity of the crop condition")
    diseases: List[Disease] = Field(default_factory=list, max_length=10, description="List of detected diseases")
    treatments: List[Treatment] = Field(default_factory=list, max_length=10, description="List of recommended treatments")
    overall_health: str = Field(None, max_length=300, description="One sentence summary of plant health")
    additional_notes: Optional[str] = Field(None, max_length=500, description="Other observations or recommendations")