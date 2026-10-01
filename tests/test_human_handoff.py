from app.artifiact.schema import Capability
from app.replay.executor import ReplayExecutor
from app.replay.checkpoints import CheckpointVerifier
from app.safety.policy import SafetyPolicy
from app.browser.playwright_surface import PlaywrightSurface


def test_real_app_human_handoff():

    capability_data = {
    "schema_version": "1.0",
    "capability_id": "test_human_handoff",
    "version": "1.0.0",

    "description": "Open a new savings sub-account with human approval.",

    "target": {
        "application": "Member Banking Demo",
        "base_url": "http://localhost:5173"
    },

    "inputs": {
        "member_id": {
            "type": "string",
            "required": True,
            "description": "Member ID"
        },
        "initial_deposit": {
            "type": "number",
            "required": True,
            "description": "Initial deposit amount"
        }
    },

    "outputs": {},

    "steps": [
        {
            "id": "step_1",
            "action": "fill",
            "target": {
                "strategy": "id",
                "value": "member-id"
            },
            "value": "{{member_id}}"
        },

        {
            "id": "step_2",
            "action": "click",
            "target": {
                "strategy": "id",
                "name": "Search Member",
                "role": "button",
                "value": "search-member"
            }
        },

        {
            "id": "step_3",
            "action": "click",
            "target": {
                "strategy": "id",
                "name": "Open Sub-Account",
                "role": "button",
                "value": "open-sub-account"
            }
        },

        {
            "id": "step_4",
            "action": "fill",
            "target": {
                "strategy": "id",
                "value": "initial-deposit"
            },
            "value": "{{initial_deposit}}"
        },

        {
            "id": "step_5",
            "action": "click",
            "target": {
                "strategy": "role",
                "name": "Approve & Continue",
                "role": "button",
                "safety": "human_required"
            }
        },

        {
            "id": "step_6",
            "action": "finish"
        }
    ],

    "checkpoint": {
        "type": "visible",
        "target": {
            "strategy": "id",
            "value": "sub-account-confirmation"
        },
        "description": "Sub-account confirmation is visible."
    },

    "business_outcomes": []
}
    
    capability = Capability.model_validate(capability_data)

    surface = PlaywrightSurface(base_url="http://localhost:5173", fail_click_once=False)

    executor = ReplayExecutor(surface=surface,
        checkpoint_verifier=CheckpointVerifier(surface),
        safety_policy=SafetyPolicy(),
        max_retries=2
    )

    print("\n" + "=" * 70)
    print("STARTING REAL APPLICATION HUMAN HANDOFF TEST")
    print("=" * 70)

    result = executor.execute(capability, { "member_id": "13141","initial_deposit": 1000 })

    print("\n=== Human Handoff Result ===")
    print(result)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    assert result["status"] == "success"
    assert result["capability_id"] == "test_human_handoff"

    print("\nHuman handoff test PASSED.")