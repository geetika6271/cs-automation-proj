from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CapabilityTarget(BaseModel):
    application: str
    base_url: str


class InputDefinition(BaseModel):
    type: str
    required: bool = True
    description: Optional[str] = None


class OutputDefinition(BaseModel):
    type: str
    description: Optional[str] = None


class Target(BaseModel):
    strategy: str
    name: Optional[str] = None
    role: Optional[str] = None
    value: Optional[str] = None
    safety: Optional[str] = None


class ReplayStep(BaseModel):
    id: str
    action: str
    target: Optional[Target] = None
    value: Optional[Any] = None
    output: Optional[str] = None
    description: Optional[str] = None


class Checkpoint(BaseModel):
    type: str
    target: Target
    description: Optional[str] = None

class BusinessOutcome(BaseModel):
    code: str
    type: str = "business_outcome"
    message: str
    target: Target

class Capability(BaseModel):
    schema_version: str = "1.0"
    capability_id: str
    version: str
    description: str
    
    target: CapabilityTarget
    inputs: Dict[str, InputDefinition] = Field(default_factory=dict)
    outputs: Dict[str, OutputDefinition] = Field(default_factory=dict)
    steps: List[ReplayStep] = Field(default_factory=list)
    checkpoint: Checkpoint
    business_outcomes: List[BusinessOutcome] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
