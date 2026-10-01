from app.artifiact.schema import Capability
from app.replay.executor import ReplayExecutor
from app.replay.checkpoints import CheckpointVerifier
from app.safety.policy import SafetyPolicy
from app.browser.playwright_surface import PlaywrightSurface


def test_replay_hard_failure_invalid_selector():
    """
    Verify that ReplayExecutor reports a hard failure when
    a required UI element cannot be located.
    Expected flow:
        step_1 -> fill member ID -> success
        step_2 -> invalid search button -> hard failure

    The actual application contains:  #search-member
    but this test intentionally uses: #wrong-id-search-member
    """

    capability_data = {
        "schema_version": "1.0",
        "capability_id": "test_lookup_hard_failure",
        "version": "1.0.0",
        "description": ("Test replay hard failure using an invalid UI selector."),
        "target": {
            "application": "Member Banking Demo",
            "base_url": "http://localhost:5173"
        },
        "inputs": {
            "member_id": {
                "type": "string",
                "required": True,
                "description": "Member ID"
            }
        },
        "outputs": {
            "savings_account_balance": {
                "type": "string",
                "description": "Savings account balance."
            }
        },

        "steps": [
            {
                "id": "step_1",
                "action": "fill",
                "target": {
                    "strategy": "id",
                    "value": "member-id"
                },
                "value": "{{member_id}}",
                "description": "Fill the member ID."
            },

            {
                "id": "step_2",
                "action": "click",
                "target": {
                    "strategy": "id",
                    "name": "Search Member",
                    "role": "button",
                    "value": "wrong-id-search-member"
                },
                "description": (
                    "Intentionally use an invalid selector."
                )
            },

            {
                "id": "step_3",
                "action": "extract",
                "target": {
                    "strategy": "id",
                    "value": "savings-balance"
                },
                "output": "savings_account_balance",
                "description": "Extract the savings balance."
            },

            {
                "id": "step_4",
                "action": "finish",
                "description": "Complete the capability."
            }
        ],

        "checkpoint": {
            "type": "visible",
            "target": {
                "strategy": "id",
                "value": "member-details"
            },
            "description": "Member details should be visible."
        },

        "business_outcomes": [
            {
                "code": "MEMBER_NOT_FOUND",
                "type": "business_outcome",
                "message": "Member not found",
                "target": {
                    "strategy": "id",
                    "value": "member-search-error"
                }
            }
        ],

        "metadata": {
            "source": "test",
            "goal": (
                "Test hard failure caused by an invalid search selector."
            )
        }
    }

    capability = Capability.model_validate(capability_data)
    capability.capability_id = "test_hard_failure"
    surface = PlaywrightSurface(
        base_url="http://localhost:5173",
        fail_click_once=False
    )

    executor = ReplayExecutor(
        surface=surface,
        checkpoint_verifier=CheckpointVerifier(surface),
        safety_policy=SafetyPolicy(),
        max_retries=2
    )

    result = executor.execute(capability,{"member_id": "67890" })

    print("\n=== Hard Failure Result ===")
    print(result)

    assert result["status"] == "hard_failure"
    assert result["capability_id"] == "test_hard_failure"
    assert result["step"] == "step_2"
    assert "Timeout" in result["message"] or ("locator" in result["message"].lower() )

    print("\nHard failure test PASSED.")