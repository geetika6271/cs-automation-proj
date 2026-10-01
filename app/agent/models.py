from typing import Literal, Optional
from pydantic import BaseModel


class Target(BaseModel):
    strategy: str
    role: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None
    safety: Optional[str] = None


class Checkpoint(BaseModel):
    type: Literal["visible", "text"]
    target: Target
    description: Optional[str] = None


class BusinessOutcome(BaseModel):
    code: str
    message: str
    target: Target

class ActionParameter(BaseModel):
    name: str
    type: str = "string"
    description: Optional[str] = None

class AgentAction(BaseModel):
    action: Literal[
        "click",
        "fill",
        "extract",
        "finish",
        "human_required",
        "business_outcome",
    ]

    target: Optional[Target] = None
    value: Optional[str] = None
    output_name: Optional[str] = None
    parameter: Optional[ActionParameter] = None
    reason: Optional[str] = None
    business_outcome: Optional[BusinessOutcome] = None
    checkpoint: Optional[Checkpoint] = None