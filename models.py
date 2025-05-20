from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AssessmentData(BaseModel):
    """Assessment section of ADIME note"""
    summary: str = Field(default="")
    weight: Optional[str] = Field(default=None)
    labs: Optional[List[str]] = Field(default=None)
    current_intake: Optional[str] = Field(default=None)


class ActionItem(BaseModel):
    """Action item from intervention section"""
    title: str
    description: str
    visualization_prompt: Optional[str] = None


class DiagnosisData(BaseModel):
    """Diagnosis section of ADIME note"""
    summary: str = Field(default="")
    problems: Optional[List[str]] = Field(default_factory=list)


class InterventionData(BaseModel):
    """Intervention section of ADIME note"""
    summary: str = Field(default="")
    action_items: Optional[List[ActionItem]] = Field(default_factory=list)


class MonitoringData(BaseModel):
    """Monitoring section of ADIME note"""
    follow_up: str = Field(default="")
    metrics: Optional[List[str]] = Field(default_factory=list)
    timeline: Optional[str] = Field(default=None)


class ADIMEData(BaseModel):
    """Full ADIME note data"""
    assessment: AssessmentData
    diagnosis: DiagnosisData
    intervention: InterventionData
    monitoring: MonitoringData


class ImageInfo(BaseModel):
    """Information about a generated image"""
    title: str
    description: str
    image_path: str 