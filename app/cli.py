import argparse
import json
from pprint import pprint
from app.agent.agent import DiscoverytAgent
from app.agent.llm import LLMClient
from app.browser.playwright_surface import PlaywrightSurface
from app.escalation.handoff import HandoffManager
from app.safety.policy import SafetyPolicy
from app.replay.executor import ReplayExecutor
from app.replay.checkpoints import CheckpointVerifier
from app.artifiact.storage import ArtifactStorage
from app.artifiact.builder import ArtifactBuilder

def replay(artifact_path, inputs):

    # Load saved capability
    storage = ArtifactStorage()
    capability = storage.load(artifact_path)

    # Create browser surface
    surface = PlaywrightSurface(base_url=capability.target.base_url)

    try:
        # Create replay components
        checkpoint_verifier = CheckpointVerifier(surface)
        safety_policy = SafetyPolicy()
        executor = ReplayExecutor(surface=surface, checkpoint_verifier=checkpoint_verifier,
                                   safety_policy=safety_policy )

        # Execute deterministic replay
        result = executor.execute(capability=capability,inputs=inputs)

        print("\n=== Replay Result ===")
        print(json.dumps(result,indent=2))

    finally:
        surface.close()


def discover_lookup(goal: str, outcome_member_id: str):

    surface = PlaywrightSurface("http://localhost:5173")
    result = None

    try:

        # DISCOVERY #1 — SUCCESSFUL CASE
        surface.open()

        llm = LLMClient()
        safety_policy = SafetyPolicy()
        handoff_manager = HandoffManager()

        agent = DiscoverytAgent(
            surface=surface,
            llm=llm,
            safety_policy=safety_policy,
            handoff_manager=handoff_manager,
        )

        print("\n==============================")
        print("DISCOVERY #1 — SUCCESS CASE")

        result = agent.run(goal, evidence_path="evidence/discovery/success_discovery_lookup_log.json" )

        if result.get("status") != "success":
            print("\nSuccessful discovery did not complete.")
            return

        history = result.get("history", [])


        # DISCOVERY #2 — BUSINESS OUTCOME CASE
        print("\n======================================")
        print("DISCOVERY #2 — BUSINESS OUTCOME CASE")

        # Reset browser/application state before second discovery.
        surface.close()

        surface = PlaywrightSurface("http://localhost:5173")
        surface.open()

        outcome_agent = DiscoverytAgent(
            surface=surface,
            llm=llm,
            safety_policy=safety_policy,
            handoff_manager=handoff_manager,
        )

        outcome_goal = (
            f"Look up member {outcome_member_id}. "
            "If the member does not exist, identify and report "
            "the legitimate business outcome instead of treating "
            "it as a technical failure."
        )

        outcome_result = outcome_agent.run(goal=outcome_goal,
            evidence_path="evidence/discovery/business_outcome_discovery_log.json",
        )

        outcomes = []

        if outcome_result.get("status") == "business_outcome":
            outcomes.append(outcome_result["outcome"])
        else:
            print("\nExpected business outcome was not discovered.")
            print("Artifact will not be created because the business outcome was not captured.")
            return

  
        # BUILD ONE ARTIFACT FROM BOTH DISCOVERIES
        print("\n======================================")
        print("BUILDING CAPABILITY ARTIFACT")
        builder = ArtifactBuilder(capability_id="lookup_member_savings",version="1.0.0")
        capability = builder.build(
            goal=goal,
            application="Member Banking Demo",
            base_url="http://localhost:5173",
            history=history,
            outcomes=outcomes,
        )

        # SAVE ARTIFACT
        storage = ArtifactStorage()
        artifact_path = storage.save(capability)

        print("\nArtifact saved to:")
        print(artifact_path)

        print("\nGenerated capability:")
        print(json.dumps( capability.model_dump(),indent=2))

    finally:

        if (not result or result.get("status") != "human_required"):
            print("[DEBUG] Closing browser")
            surface.close()

        else:
            print("[DEBUG] Keeping browser open.")

def discover_open_sub_account(goal: str):
    surface = PlaywrightSurface("http://localhost:5173")
    result = None

    try:
        surface.open()

        llm = LLMClient()
        safety_policy = SafetyPolicy()
        handoff_manager = HandoffManager()

        agent = DiscoverytAgent(
            surface=surface,
            llm=llm,
            safety_policy=safety_policy,
            handoff_manager=handoff_manager,
        )

        print("\n======================================")
        print("DISCOVERY — OPEN SUB-ACCOUNT")
        print("======================================")

        result = agent.run(goal,
                         evidence_path="evidence/discovery/open_sub_account_discovery_log.json" )

        # print("\nOPEN SUB-ACCOUNT DISCOVERY RESULT")
        # pprint(result)

        if result.get("status") != "success":
            print("\nOpen sub-account discovery did not complete.")
            return

        history = result.get("history", [])

        # ---------------------------------------------
        # BUILD ARTIFACT
        # ---------------------------------------------

        print("\n======================================")
        print("BUILDING OPEN SUB-ACCOUNT ARTIFACT")
        print("======================================")

        builder = ArtifactBuilder(
            capability_id="open_sub_account",
            version="1.0.0"
        )

        capability = builder.build(
            goal=goal,
            application="Member Banking Demo",
            base_url="http://localhost:5173",
            history=history,
            outcomes=[]
        )

        # ---------------------------------------------
        # SAVE ARTIFACT
        # ---------------------------------------------

        storage = ArtifactStorage()

        artifact_path = storage.save(capability)

        print("\nArtifact saved to:")
        print(artifact_path)

        print("\nGenerated capability:")
        print(
            json.dumps(
                capability.model_dump(),
                indent=2
            )
        )

    finally:
        if not result or result.get("status") != "human_required":
            print("[DEBUG] Closing browser")
            surface.close()
        else:
            print("[DEBUG] Keeping browser open.")

def main():

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")

    discover_parser = subparsers.add_parser("discover-lookup")
    discover_parser.add_argument("--goal",required=True)
    discover_parser.add_argument("--outcome-member-id",required=True,help="Known member ID that produces a legitimate business outcome.")


    subaccount_parser = subparsers.add_parser("discover-open-sub-account")
    subaccount_parser.add_argument("--goal",required=True)
   
    replay_parser = subparsers.add_parser("replay",help="Replay a saved capability deterministically")
    replay_parser.add_argument("artifact", help="Path to capability artifact JSON" )
    replay_parser.add_argument("--input",action="append", default=[], help="Capability input in key=value format. Can be specified multiple times.")

    args = parser.parse_args()

    if args.command == "discover-lookup":
        discover_lookup(args.goal, args.outcome_member_id)

    elif args.command == "discover-open-sub-account":
        discover_open_sub_account( args.goal)

    elif args.command == "replay":
        inputs = {}
        for item in args.input:
            if "=" not in item:
                parser.error(f"Invalid --input '{item}'. Expected key=value.")
            key, value = item.split("=", 1)
            inputs[key] = value
        replay(args.artifact, inputs)

    else:
        parser.print_help


if __name__ == "__main__":
    main()