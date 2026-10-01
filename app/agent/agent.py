from app.browser.observer import PageObserver
from pprint import pprint
from app.safety.policy import BLOCKED_ACTIONS,RISKY_ACTIONS,HumanApprovalRequired
from app.artifiact.recorder import ActionRecorder
from app.escalation.handoff import HandoffManager

class DiscoverytAgent:

    def __init__(self, surface, llm,safety_policy,handoff_manager):
        self.surface = surface
        self.llm = llm
        self.safety_policy = safety_policy
        self.handoff_manager = handoff_manager

    def run(self, goal: str, evidence_path: str, max_steps: int = 10):

        observer = PageObserver(self.surface.page)
        history = []
        extracted_data={}
        recorder = ActionRecorder()

        for step_number in range(1, max_steps + 1):

            state = observer.observe()
            recorder.record_event("observation",{"step":step_number,"state":state})

            action = self.llm.decide(goal=goal,
                                    page_state={"page": state,"extracted_data": extracted_data})
            
            recorder.record_event("decision",{"step": step_number,"action": action.model_dump()})

            print(f"\n{'=' * 60}")
            print(f"STEP {step_number}")
            print(f"{'=' * 60}")

            print("\nOBSERVED STATE:")
            pprint(state, sort_dicts=False, width=100)

            print("\nLLM ACTION:")
            print(f"  Action : {action.action}")
            print(f"  Target : {action.target}")
            print(f"  Value  : {action.value}")
            print(f"  Reason : {action.reason}")

            history.append({ "step": step_number,"state": state,"action": action.model_dump()})

            if action.action == "business_outcome":
                outcome = action.business_outcome

                print("\nBusiness outcome detected:")
                print(f"  Code: {outcome.code}")
                print(f"  Message: {outcome.message}")
                print(f" Target: {outcome.target.model_dump()}")

                recorder.save(evidence_path)

                return {
                        "status": "business_outcome",
                        "outcome": {
                            "code": outcome.code,
                            "type": "business_outcome",
                            "message": outcome.message,
                            "target": outcome.target.model_dump(),
                        },
                        "history": history,
                    }


            ## Safety check of the action to be made
            try:
                self.safety_policy.check(action.action,action.target)

            except HumanApprovalRequired as exc:

                intervention_id = f"INT-{step_number:03d}"
                screenshot_path = f"evidence/handoff/discovery/intervention_{step_number}.png"
                try:
                    self.surface.screenshot(screenshot_path)
                except Exception:
                    screenshot_path = ""

                request = self.handoff_manager.create_request(
                    intervention_id=intervention_id,
                    goal=goal,
                    current_step=f"step_{step_number}",
                    reason=str(exc),
                    screenshot=screenshot_path,
                )

                self.handoff_manager.save_request(request,f"evidence/handoff/discovery/intervention_{step_number}.json" )
                recorder.record_event("human_handoff_requested",
                    {
                        "intervention_id": intervention_id,
                        "step": f"step_{step_number}",
                        "action": action.action,
                        "reason": str(exc),
                        "screenshot": screenshot_path,
                    },
                )

                self.handoff_manager.wait_for_human(request)
                self.handoff_manager.save_request(request,f"evidence/handoff/discovery/intervention_{step_number}.json")
                recorder.record_event("human_intervention_completed",
                    {
                        "intervention_id": intervention_id,
                        "step": f"step_{step_number}",
                        "human_action": request.human_action,
                        "status": request.status,
                    },
                )

                recorder.record_event("replay_resumed",{
                        "intervention_id": intervention_id,
                        "step": f"step_{step_number}",
                    },
                )

                continue

            except PermissionError as exc:
                return {
                    "status": "hard_failure",
                    "reason": str(exc),
                    "history": history
                }

            # succesfull safety check perform the action on test UI
            if action.action == "fill":

                self.surface.fill(
                    action.target.model_dump(),
                    action.value
                )
                recorder.record(step=step_number,action=action,state=state,result={"filled": True},status="completed" )

            elif action.action == "click":

                self.surface.click(action.target.model_dump())

                recorder.record(step=step_number,action=action, state=state,result={ "clicked": True},status="completed")

            elif action.action == "extract":

                value = self.surface.extract(action.target.model_dump())

                if action.output_name:
                    extracted_data[action.output_name] = value

                # Store it in history
                history[-1]["result"] = value

                recorder.record(step=step_number, action=action,state=state,result={"output_name": action.output_name,"value": value},status="completed")
                print("\nRESULT:")
                print(f"  Extracted: {value}")

                if action.output_name:
                    print(f"  Stored as: {action.output_name}")

            elif action.action == "finish":

                if not action.checkpoint:
                    return {
                        "status": "hard_failure",
                        "reason": (
                            "LLM finished successfully but did not provide "
                            "a success checkpoint."
                        ),
                        "history": history,
                    }

                checkpoint = action.checkpoint.model_dump()

                history[-1]["checkpoint"] = checkpoint

                recorder.record_event(
                    "checkpoint_discovered",
                    {
                        "step": step_number,
                        "checkpoint": checkpoint,
                    },
                )

                recorder.save(evidence_path)

                return {
                    "status": "success",
                    "result": extracted_data,
                    "checkpoint": checkpoint,
                    "history": history,
                }
            else:

                print("\nRESULT:")
                print(f"  Unsupported action: {action.action}")

                return {
                    "status": "hard_failure",
                    "reason": f"Unsupported action: {action.action}",
                    "history": history
                }
  
        return {
            "status": "hard_failure",
            "reason": "Maximum number of steps exceeded",
            "history": history
        }
