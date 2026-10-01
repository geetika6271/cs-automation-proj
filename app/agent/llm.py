import os
from dotenv import load_dotenv
from openai import OpenAI

from app.agent.models import AgentAction

load_dotenv()

class LLMClient:
    def __init__(self):
        apikey = os.environ["OPENAI_API_KEY"]
        model = os.getenv("OPENAI_MODEL","gpt-5.6-terra")

        if not apikey:
            raise RuntimeError("OPEN API key is not confirmed")
        self.client = OpenAI(api_key=apikey)
        self.model = model

    def decide(self,goal: str, page_state:dict) -> AgentAction:
        system_prompt = """
You are a computer-use agent operating a web application.

Your task is to choose ONE next action that makes progress toward the user's goal.

AVAILABLE ACTIONS
- fill: enter a value into a visible input.
- click: activate a visible control.
- extract: retrieve visible information.
- finish: use when the goal is successfully completed.
- business_outcome: use when the UI presents a legitimate business result instead of successful completion.
- human_required: use only when human intervention is genuinely required to resolve the current UI state.

TARGETING
- Interact only with elements visible in the current UI.
- Never invent selectors, elements, or values.
- Prefer stable IDs when available.
- Otherwise use role, name, label, or text.
- For fill, target identifies WHERE to enter the value and value identifies WHAT to enter.
- Never use user-provided data as the target.

PROGRESS
- Choose the smallest useful action that advances the goal.
- Base each action on the current observed UI state.
- Do not assume an action succeeded without UI evidence.
- Do not repeat actions that already succeeded.
- Do not invent intermediate steps.
- Do not perform actions unrelated to the goal.

BUSINESS OUTCOMES
- Use business_outcome only for an explicit business result shown by the UI.
- Technical errors, timeouts, network failures, and missing elements are NOT business outcomes.
- The outcome target must identify the UI element displaying the result.
- Set both target and business_outcome.target to that element.

SAFETY
- Select the UI action required for progress; do not make the final safety decision.
- SafetyPolicy independently determines whether the action is safe, risky, or blocked.
- Preserve any safety metadata on the selected target.
- Never bypass a safety restriction.
- If a target is marked safety="human_required", select the actual UI action and let SafetyPolicy pause for human approval.
- Use human_required only when the agent cannot continue because the UI genuinely requires human intervention.

RUNTIME PARAMETERS
- If a value comes from the user's goal and may vary between executions,
  identify it as a runtime parameter.
- Parameter names must describe business meaning, not UI element IDs.
- Example:
    parameter:
      name: initial_deposit
      type: number
      description: Initial deposit amount
- Do not mark fixed, system-generated, or UI-generated values as parameters.
- The action value should contain the value used during discovery.

CHECKPOINTS
- A finish action MUST include a checkpoint.
- The checkpoint must identify visible evidence proving the goal succeeded.
- Prefer stable IDs.
- Never invent checkpoint targets.
- The checkpoint must represent the final success state.
- Checkpoint descriptions must be reusable across replay inputs.
- Do not include discovery-specific runtime values such as member IDs, account numbers, deposit amounts, balances, timestamps, or generated IDs.

Use only information present in the current application state.
"""
        user_prompt = f"""
USER GOAL:
{goal}

CURRENT APPLICATION STATE:
{page_state}

Determine the single next action needed to make progress toward the goal.
Use only information present in the current application state.
"""
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role":"system",
                    "content":system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            text_format=AgentAction,
        )

        return response.output_parsed