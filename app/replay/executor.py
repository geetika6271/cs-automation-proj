from typing import Any, Dict
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from app.artifiact.schema import Capability, ReplayStep
from app.replay.checkpoints import CheckpointVerifier
from app.replay.errors import ( ReplayError,BusinessOutcomeError,RecoverableReplayError)
from app.safety.policy import (SafetyPolicy,HumanApprovalRequired)
from app.escalation.handoff import HandoffManager
from app.safety.policy import SafetyPolicy
from app.artifiact.recorder import ActionRecorder
from datetime import datetime, UTC

class ReplayExecutor:

    def __init__(self, surface,checkpoint_verifier: CheckpointVerifier,safety_policy: SafetyPolicy, max_retries: int = 3):
        self.surface = surface
        self.checkpoint_verifier = checkpoint_verifier
        self.safety_policy = safety_policy
        self.recorder = ActionRecorder()
        self.max_retries = max_retries
        self.handoff_manager = HandoffManager()

    def execute(self,capability: Capability,inputs: Dict[str, Any]) -> Dict[str, Any]:

        self._validate_inputs(capability, inputs)
        outputs = {}
        executed_steps = []

        try:
            # Make sure browser is on the application
            self.surface.open()

            for step in capability.steps:

                attempt = 0
                while True:

                    try:
                        result = self._execute_step(step,inputs,capability)

                        executed_steps.append(step.id)
        
                        # Store declared outputs from extract steps
                        if step.action == "extract" and step.output:
                            outputs[step.output] = result

                        self.recorder.record_event("replay_step", {
                            "step_id": step.id,
                            "action": step.action,
                            "target": (step.target.model_dump() if step.target else None ),
                            "result": result,
                            "attempt": attempt + 1,
                        })

                        break

                    except HumanApprovalRequired as exc:

                        self._handle_human_handoff(capability,step,exc)
                        executed_steps.append(step.id)
                        self.recorder.record_event("replay_step", {
                                "step_id": step.id,
                                "action": step.action,
                                "result": "completed_by_human",
                                "attempt": attempt + 1,
                            }
                        )
                        break

                    except RecoverableReplayError as exc:

                        attempt += 1
                        self.recorder.record_event( "recovery_attempt", {
                                "step": exc.step_id,
                                "attempt": attempt,
                                "max_retries": self.max_retries,
                                "message": str(exc),
                            }
                        )

                        if attempt > self.max_retries:
                            self.recorder.record_event( "recovery_exhausted",
                                {
                                    "step": exc.step_id,
                                    "attempts": attempt,
                                    "message": str(exc),
                                }
                            )

                            raise ReplayError( step_id=exc.step_id,
                                message=(
                                    f"Recoverable error persisted "
                                    f"after {self.max_retries} retries: "
                                    f"{str(exc)}"
                                ),
                                expected="Successful replay after retry",
                                observed="Recovery attempts exhausted",
                            )

            # Verify final checkpoint
            checkpoint_result = (self.checkpoint_verifier.verify(capability.checkpoint))

            if not checkpoint_result:
                raise ReplayError(
                    step_id="checkpoint",
                    message="Final checkpoint verification failed.",
                    expected=capability.checkpoint.model_dump(),
                    observed="Checkpoint condition was not satisfied.")

            self.recorder.record_event("checkpoint_verified", {
                    "checkpoint": capability.checkpoint.model_dump(),
                    "verified": True,
                }
            )
            # Take screenshot after successful replay/checkpoint verification
            success_screenshot_path = (f"evidence/replay/replay_{capability.capability_id}_success.png" )

            try:
                self.surface.screenshot(success_screenshot_path)
            except Exception as exc:
                success_screenshot_path = None
                self.recorder.record_event("success_screenshot_failed", {"error": str(exc)})

            self.recorder.record_event( "replay_completed", {
                    "capability_id": capability.capability_id,
                    "version": capability.version,
                    "outputs": outputs,
                }
            )

            self.recorder.save(f"evidence/replay/replay_{capability.capability_id}_success.json")
            return {
                "status": "success",
                "capability_id": capability.capability_id,
                "version": capability.version,
                "outputs": outputs,
                "executed_steps": executed_steps
            }

        except BusinessOutcomeError as exc:
                result = {
                "status": "business_outcome",
                "capability_id": capability.capability_id,
                "step": exc.step_id,
                "code": exc.code,
                "message": str(exc)
            }
                self.recorder.record_event("replay_business_outcome",result)
                # Take screenshot after successful replay/checkpoint verification
                success_screenshot_path = (f"evidence/replay/replay_{capability.capability_id}_businessOutcome.png")
                try:
                    self.surface.screenshot(success_screenshot_path)
                except Exception as exc:
                    success_screenshot_path = None
                    self.recorder.record_event("success_screenshot_failed", {
                        "error": str(exc),
                    })
                self.recorder.save(f"evidence/replay/replay_{capability.capability_id}_businessOutcome.json")

                return result


        except RecoverableReplayError as exc:

            return {
                "status": "recoverable_error",
                "capability_id": capability.capability_id,
                "step": exc.step_id,
                "message": str(exc)
            }

        except ReplayError as exc:
                self.recorder.record_event("replay_failure", {
                        "status": "hard_failure",
                        "step": exc.step_id,
                        "message": str(exc),
                        "expected": exc.expected,
                        "observed": exc.observed,
                    }
                )

                screenshot_path = (f"evidence/failures/replay_failure_{capability.capability_id}_{exc.step_id}.png" )

                try:
                    self.surface.screenshot(screenshot_path)
                except Exception:
                    screenshot_path = None

                self.recorder.record_event("failure_evidence",{"screenshot": screenshot_path} )

                self.recorder.save(f"evidence/failures/replay_failure_{capability.capability_id}_{exc.step_id}.json")
                return {
                    "status": "hard_failure",
                    "capability_id": capability.capability_id,
                    "step": exc.step_id,
                    "message": str(exc),
                    "expected": exc.expected,
                    "observed": exc.observed
                }

        except Exception as exc:

            screenshot_path = ("evidence/failures/replay_unexpected_failure.png")
            try:
                self.surface.screenshot(screenshot_path)
            except Exception:
                screenshot_path = None

            self.recorder.record_event("unexpected_failure",
                {
                    "error": str(exc),
                    "screenshot": screenshot_path,
                }
            )

            self.recorder.save("evidence/failures/replay_unexpected_failure.json")

            return {
                "status": "hard_failure",
                "capability_id": capability.capability_id,
                "message": str(exc),
                "screenshot": screenshot_path,
            }

    def _execute_step(self,step: ReplayStep,inputs: Dict[str, Any], capability ):

        action = step.action
        target = (step.target.model_dump() if step.target else None)

        # Safety check
        self.safety_policy.check(action,target)

        if action == "navigate":
            try:
                return self.surface.navigate(step.value)
            except Exception as exc:
                self._raise_classified_error(step, exc)

        if action == "fill":
            value = self._substitute(step.value, inputs)
            try:
                return self.surface.fill(target,value)

            except Exception as exc:
                self._raise_classified_error(step,exc)

        elif action == "click":

            try:
                    result = self.surface.click(target)
                    self._raise_if_business_outcome(capability,step)
                    ui_error = self._detect_recoverable_ui_error()

                    if ui_error:
                        raise RecoverableReplayError(
                            step_id=step.id,
                            message=f"network error: {ui_error}"
                        )

                    return result
   

            except BusinessOutcomeError:
                self.recorder.record_event("replay_step", {
                "step_id": step.id,
                "action": step.action,
                "target": (
                    step.target.model_dump()
                    if step.target
                    else None
                ),
                "result": result,
            })
                raise

            except Exception as exc:
                self._raise_classified_error(step,exc)

        elif action == "extract":

            try:
                return self.surface.extract(target)

            except Exception as exc:
                ui_error = self._detect_recoverable_ui_error()

                if ui_error:
                    raise RecoverableReplayError(
                        step_id=step.id,
                        message=f"network error: {ui_error}"
                    )
                
                self._raise_classified_error(step,exc)

        elif action == "finish":
            return None

        else:
            raise ReplayError(
                step_id=step.id,
                message=f"Unsupported replay action: {action}",
                expected="Supported replay action",
                observed=action
            )

    def _substitute(self, value, inputs):

        if not isinstance(value, str):
            return value
        for key, input_value in inputs.items():
            placeholder = "{{" + key + "}}"
            value = value.replace(placeholder,str(input_value))
        return value

    def _validate_inputs(self,capability,inputs):

        for name, definition in capability.inputs.items():
            if definition.required and name not in inputs:
                raise ReplayError(step_id="input_validation", 
                                  message=f"Missing required input: {name}",
                                  expected=name,
                                   observed=None)

    def _raise_if_business_outcome( self,capability: Capability,step: ReplayStep):

        for outcome in capability.business_outcomes:
            if self.surface.wait_for_visible(outcome.target.model_dump(),timeout=2000):

                raise BusinessOutcomeError(step_id=step.id,code=outcome.code,message=outcome.message)

    def _detect_recoverable_ui_error(self):
        try:
            page_text = self.surface.get_page_text().lower()

            print("\n=== CURRENT PAGE TEXT ===")
            print(page_text)
            print("=== END PAGE TEXT ===")

            recoverable_patterns = [
                "temporarily unavailable",
                "network error",
                "connection reset",
                "connection refused",
                "connection closed",
            ]

            for pattern in recoverable_patterns:
                if pattern in page_text:
                    print(f">>> Detected recoverable UI error: {pattern}")
                    return pattern

            print(">>> No recoverable UI error detected")
            return None

        except Exception as exc:
            print(f">>> Could not inspect UI: {exc}")
            return None
    
    def _raise_classified_error(self, step, exc):

        message = str(exc).lower()
        recoverable_patterns = ["temporarily unavailable","connection reset","network error",
                                "connection refused","connection closed","timeout",]

        if any(pattern in message for pattern in recoverable_patterns):
            raise RecoverableReplayError(step_id=step.id,message=str(exc))

        raise ReplayError(step_id=step.id, message=str(exc),
                        expected=f"Successful {step.action}", observed=type(exc).__name__)

    def _handle_human_handoff(self, capability, step, exc):

        intervention_id = (
            f"{capability.capability_id}_"
            f"{step.id}_"
            f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        )

        screenshot_path = (f"evidence/handoff/replay/intervention_{step.id}.png")

        try:
            self.surface.screenshot(screenshot_path)
        except Exception:
            screenshot_path = ""

        goal = (
            capability.metadata.get("goal")
            if isinstance(capability.metadata, dict)
            else getattr(capability.metadata, "goal", None)
        )

        if not goal:
            goal = capability.description

        request = self.handoff_manager.create_request(
            intervention_id=intervention_id,
            goal=goal,
            current_step=step.id,
            reason=str(exc),
            screenshot=screenshot_path
        )

        handoff_path = (f"evidence/handoff/replay/intervention_{step.id}.json")

        self.recorder.record_event("human_handoff_requested",
            {
                "intervention_id": intervention_id,
                "step": step.id,
                "action": step.action,
                "reason": str(exc),
                "screenshot": screenshot_path,
            }
        )

        self.recorder.record_event("human_intervention_started",{
                "intervention_id": intervention_id,
                "step": step.id,
            }
        )

        # Wait for the human.
        # pending -> approved -> resumed
        self.handoff_manager.wait_for_human(request)
        self.handoff_manager.save_request(request,handoff_path)

        self.recorder.record_event("human_intervention_completed",{
                "intervention_id": intervention_id,
                "step": step.id,
                "human_action": request.human_action,
                "status": request.status,
            })

        self.recorder.record_event("replay_resumed", {
                "intervention_id": intervention_id,
                "step": step.id,
            })