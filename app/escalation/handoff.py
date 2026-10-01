from dataclasses import dataclass, asdict
import json
from pathlib import Path
from datetime import datetime, UTC


@dataclass
class InterventionRequest:
    intervention_id: str
    goal: str
    current_step: str
    reason: str
    screenshot: str
    status: str = "pending"
    created_at: str = ""
    completed_at: str = ""
    human_action: str = ""


class HandoffManager:

    def create_request(self,intervention_id: str, goal: str, 
                       current_step: str, reason: str, screenshot: str):

        
        request = InterventionRequest(
            intervention_id=intervention_id,
            goal=goal,
            current_step=current_step,
            reason=reason,
            screenshot=screenshot,
            status="pending",
            created_at=datetime.now(UTC).isoformat()
        )

        return request

    def save_request(self,request: InterventionRequest,path: str):

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(request), f, indent=2)

    def approve(self,request: InterventionRequest, human_action: str = "approved"):

        request.status = "approved"
        request.human_action = human_action
        request.completed_at = datetime.now(UTC).isoformat()
        return request

    def resume(self, request: InterventionRequest):

        if request.status != "approved":
            raise RuntimeError("Cannot resume without human approval")

        request.status = "resumed"
        return request

    def wait_for_human(self, request: InterventionRequest):

        print("\n" + "=" * 60)
        print("HUMAN INTERVENTION REQUIRED")
        print("=" * 60)

        print(f"Goal: {request.goal}")
        print(f"Step: {request.current_step}")
        print(f"Reason: {request.reason}")
        print()

        print("The browser session is still open.")
        print()
        print("Human actions:")
        print("1. Review the current UI and the reason for escalation.")
        print("2. Complete the required human intervention in the browser.")
        print("3. Verify that the UI has reached the expected state.")
        print("4. Return to this terminal and press ENTER to resume.")
        print()

        input("Press ENTER after completing the human intervention...")

        self.approve(request,human_action="human completed required intervention")

        return self.resume(request)