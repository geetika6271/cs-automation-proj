
import json
from pathlib import Path
from app.artifiact.schema import Capability
from app.browser.playwright_surface import PlaywrightSurface
from app.replay.checkpoints import CheckpointVerifier
from app.replay.executor import ReplayExecutor
from app.safety.policy import SafetyPolicy


def test_lookup_member_success_real_app():
    with open( "artifacts/lookup_member_savings.json", "r",  encoding="utf-8") as f:
        data = json.load(f)

    capability = Capability.model_validate(data)
    capability.capability_id="test_n"
    surface = PlaywrightSurface(capability.target.base_url)

    try:
        executor = ReplayExecutor(
            surface=surface,
            checkpoint_verifier=CheckpointVerifier(surface),
            safety_policy=SafetyPolicy(),
            max_retries=2,
        )
        result = executor.execute(capability, {"member_id": "12345"})

        assert result["status"] == "success"
        assert result["outputs"]["savings_account_balance"]
        assert result["executed_steps"] == ["step_1", "step_2", "step_3", "step_4"]

    finally:
        surface.close()


def test_lookup_member_business_outcome_real_app():
    with open( "artifacts/lookup_member_savings.json", "r",  encoding="utf-8") as f:
        data = json.load(f)

    capability = Capability.model_validate(data)
    capability.capability_id="test_bo"
    surface = PlaywrightSurface(capability.target.base_url)

    try:
        executor = ReplayExecutor(
            surface=surface,
            checkpoint_verifier=CheckpointVerifier(surface),
            safety_policy=SafetyPolicy(),
            max_retries=2,
        )
        result = executor.execute(capability, {"member_id": "99999"})

        assert result["status"] == "business_outcome"
        assert result["step"] == "step_2"
        assert result["code"] == "member_not_found"
    finally:
        surface.close()
