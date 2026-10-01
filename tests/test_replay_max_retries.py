import json

from app.replay.executor import ReplayExecutor
from app.replay.checkpoints import CheckpointVerifier
from app.safety.policy import SafetyPolicy
from app.artifiact.schema import Capability
from app.browser.playwright_surface import PlaywrightSurface


def test_real_app_max_retries_exceeded():

    with open( "artifacts/lookup_member_savings.json", "r",  encoding="utf-8") as f:
        capability_data = json.load(f)

    capability = Capability.model_validate(capability_data)
    capability.capability_id = "test_max_retries"

    surface = PlaywrightSurface( base_url="http://localhost:5173", fail_click_once=False )


    surface.open()

    # Make EVERY backend request fail
    request_count = {"count": 0}

    def fail_member_request(route):
        request_count["count"] += 1

        print(f"Simulating persistent server failure (request #{request_count['count']}): "
            f"{route.request.url}" )

        route.fulfill(status=503, content_type="application/json",
                 body=json.dumps({"error": "Service temporarily unavailable" }) )

    surface.page.route("**/api/members/**", fail_member_request)

    # Create replay executor
    executor = ReplayExecutor( surface=surface, checkpoint_verifier=CheckpointVerifier(surface),
        safety_policy=SafetyPolicy(), max_retries=2)

   
    # Execute against the REAL application
    result = executor.execute( capability, {"member_id": "67890" })

    print("\n=== Real Application Max Retry Result ===")
    print(result)

    print(f"\nTotal failed backend requests: {request_count['count']}" )

    # Assertions
    assert result["status"] == "hard_failure"
    assert result["step"] == "step_2"
    # Initial click + 2 retries = 3 backend requests
    assert request_count["count"] == 3

    assert "Recoverable error persisted after 2 retries" in ( result["message"] )