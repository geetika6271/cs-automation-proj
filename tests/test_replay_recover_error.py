import json

from app.artifiact.schema import Capability
from app.replay.executor import ReplayExecutor
from app.replay.checkpoints import CheckpointVerifier
from app.safety.policy import SafetyPolicy
from app.browser.playwright_surface import PlaywrightSurface


def test_recoverable_error_real_app():

    # Load the real capability artifact
    with open("artifacts/lookup_member_savings.json", "r") as f:
        data = json.load(f)

    capability = Capability.model_validate(data)
    capability.capability_id = "test_recoverable_error"

    # Create the REAL Playwright browser surface
    surface = PlaywrightSurface( base_url="http://localhost:5173")

    failed_once = False

    def intercept_request(route):
        nonlocal failed_once

        url = route.request.url

        if "/api/members/" in url and not failed_once:
            failed_once = True
            print("\n>>> Simulating transient server failure:", url)

            route.fulfill(
                status=503,
                content_type="application/json",
                body='{"error": "Service temporarily unavailable"}'
            )

        else:
            print("\n>>> Allowing request to succeed:", url)
            route.continue_()

    # Intercept requests from the REAL browser
    surface.page.route("**/api/members/**", intercept_request)

    checkpoint_verifier = CheckpointVerifier(surface)
    safety_policy = SafetyPolicy()

    executor = ReplayExecutor(
        surface=surface,
        checkpoint_verifier=checkpoint_verifier,
        safety_policy=safety_policy,
        max_retries=2
    )

    try:
        result = executor.execute( capability, {"member_id": "12345"} )

        print("\n=== Real Application Recovery Result ===")
        print(result)

        assert failed_once is True
        assert result["status"] == "success"

    finally:
        surface.close()