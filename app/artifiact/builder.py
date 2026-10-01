import re
from typing import Any, Dict, List
from app.artifiact.schema import (Capability,CapabilityTarget,Checkpoint,InputDefinition,OutputDefinition,ReplayStep,BusinessOutcome,Target)

class ArtifactBuilder:

    def __init__(self, capability_id: str,version: str = "1.0.0",):
        self.capability_id = capability_id
        self.version = version

    def build(self,goal: str,application: str,base_url: str,
              history: List[Dict[str, Any]],outcomes: List[Dict[str, Any]] = None,) -> Capability:
 
        steps = []
        inputs = {}
        outputs = {}
        if outcomes is None:
            outcomes = []
        for index, event in enumerate(history, start=1):
            action = event.get("action")

            if not action:
                continue

            replay_step = self._convert_action(
                action=action,
                step_number=index,
                inputs=inputs,
                outputs=outputs,
            )

            if replay_step:
                steps.append(replay_step)

        checkpoint = self._build_checkpoint(history)
  
        business_outcomes = self._build_business_outcomes(outcomes)

        return Capability(
            schema_version="1.0",
            capability_id=self.capability_id,
            version=self.version,
            description=goal,
            target=CapabilityTarget(
                application=application,
                base_url=base_url,
            ),
            inputs=inputs,
            outputs=outputs,
            steps=steps,
            checkpoint=checkpoint,
            business_outcomes=business_outcomes,
            metadata={
                "source": "llm_discovery",
                "goal": goal,
            },
        )

    def _build_business_outcomes(self,outcomes: List[Dict[str, Any]]) -> List[BusinessOutcome]:

        result = []

        for outcome in outcomes:

            target = self._build_target(outcome["target"])

            result.append( BusinessOutcome(
                    code=outcome["code"],
                    type=outcome.get("type", "business_outcome"),
                    message=outcome["message"],
                    target=target,
                )
            )

        return result


    def _convert_action( self, action: Dict[str, Any],step_number: int,inputs: Dict[str, InputDefinition],outputs: Dict[str, OutputDefinition]):

        action_type = action.get("action")

        if action_type == "fill":
            return self._build_fill_step(action,step_number,inputs)

        if action_type == "click":
            return self._build_click_step(action,step_number)

        if action_type == "extract":
            return self._build_extract_step( action, step_number, outputs)

        if action_type == "navigate":
            return self._build_navigate_step(action,step_number)


        if action_type == "finish":
            return ReplayStep(id=f"step_{step_number}", action="finish",description="Complete the capability." )

        return None

    def _build_fill_step(self,action: Dict[str, Any],step_number: int,inputs: Dict[str, InputDefinition]):

        target = self._build_target(action.get("target"))
        value = action.get("value")
        parameter = action.get("parameter")

        if parameter:
            parameter_name = parameter["name"]

            inputs[parameter_name] = InputDefinition(
                type=parameter.get("type", "string"),
                required=True,
                description=parameter.get("description"),
            )

            value = f"{{{{{parameter_name}}}}}"

        return ReplayStep( id=f"step_{step_number}",
            action="fill",
            target=target,
            value=value,
            description=f"Fill {target.name or 'input field'}.",
        )

    def _build_click_step(self,action: Dict[str, Any],step_number: int):
        return ReplayStep(
            id=f"step_{step_number}",
            action="click",
             target=self._build_target(action.get("target")),
            description="Click the target control.",
        )

    def _build_extract_step(self,action: Dict[str, Any],step_number: int,outputs: Dict[str, OutputDefinition]):
        target = self._build_target(action.get("target"))

        output_name = (
            action.get("output_name")
            or action.get("output")
            or action.get("name")
            or f"output_{len(outputs) + 1}"
        )

        outputs[output_name] = OutputDefinition(
            type="string",
            description=f"Value extracted from {target.name or 'page element'}.",
        )

        return ReplayStep(
            id=f"step_{step_number}",
            action="extract",
            target=target,
            output=output_name,
            description=f"Extract {output_name}.",
        )

    def _build_navigate_step(self,action: Dict[str, Any],step_number: int):
        return ReplayStep(
            id=f"step_{step_number}",
            action="navigate",
            target=self._build_target(action.get("target")),
            value=action.get("url"),
            description="Navigate to the target page.",
        )

    def _build_target(self, action: Dict[str, Any]) -> Target:
  
        target = action or {}

        if isinstance(target, str):
            return Target(strategy="text",value=target)

        return Target(
            strategy=target.get("strategy", "text"),
            name=target.get("name"),
            role=target.get("role"),
            value=target.get("value"),
            safety=target.get("safety"),
        )

    def _detect_parameter(self,target: Target, value: Any):

        target_name = (target.name or "").lower()

        if "member" in target_name and "id" in target_name:
            return "member_id"

        if isinstance(value, str):
            if re.fullmatch(r"\d{4,}", value):
                return "member_id"

        return None

    def _build_checkpoint( self,history: List[Dict[str, Any]]) -> Checkpoint:

        for event in reversed(history):
            checkpoint = event.get("checkpoint")

            if checkpoint:
                return Checkpoint(
                    type=checkpoint.get("type", "visible"),
                    target=self._build_target(
                        checkpoint.get("target", {})
                    ),
                    description=checkpoint.get(
                        "description",
                        "Verify the expected final state.",
                    ),
                )

        raise ValueError(
            "Successful discovery did not provide a checkpoint."
        )

