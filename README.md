# Computer-Use Automation System

A computer-use automation system that uses an LLM to discover workflows through a real web UI, saves successful workflows as reusable capability artifacts, and replays them deterministically without the LLM.

## Overview

The system has two main phases:

- **Discovery** – The LLM observes the UI and selects the next action.
- **Replay** – A saved capability is executed deterministically without LLM decisions.

```text
```text
Natural Language Goal
        |
        v
+-------------------+
| LLM-Driven        |
| Discovery         |
+-------------------+
        |
        v
Observe UI -> Select Action -> Safety Check -> Execute
        ^                              |
        |                              v
        +-------- Updated UI <---------+
        |
        v
Capability Artifact
        |
        v
+-------------------+
| Deterministic     |
| Replay            |
+-------------------+
        |
        v
Checkpoint Verification
        |
        v
Success / Business Outcome / Recovery / Failure
```

## Demo Application

The project includes a small **Member Banking Demo** application used as the target UI for the automation system. The application has two functionalities: looking up a member, which displays information about the member's account, and opening a savings sub-account.

### Technology Stack

- **Frontend:** React
- **Backend:** FastAPI
- **Automation:** Python
- **Browser Automation:** Playwright
- **LLM:** OpenAI API
- **Artifact Format:** JSON
- **Testing:** pytest

### Main Workflow

The banking application allows the automation system to:

1. Enter a member ID.
2. Search for the member.
3. View member account information.
4. Retrieve the savings account balance.
5. Open a new sub-account through a human-approved workflow.

## Architecture

### Discovery

Discovery is LLM-driven. The system observes the current UI, sends the UI state and goal to the LLM,
receives a structured action, checks the action against the safety policy,and executes it through Playwright.
- After each action, the UI is observed again and the process continues until the goal is completed
``` 
Natural Language Goal
        |
        v
Discovery Agent --> Page Observer --> LLM / ChatGPT API --> Structured Action --> Safety Policy --> Playwright Surface --> Member Banking App  -->  Updated UI
                                                                                                                                                |
                                                                                                                                                |
                                                                                                                                                +----> Page Observer
```

After a successful discovery run, the recorded actions are converted into a reusable capability artifact.

### Replay

Replay is artifact-driven and does not use the LLM to decide the next action.

```text
Capability Artifact  -->  Replay Executor  -->  Validate Inputs  -->  Execute Recorded Steps  -->  Safety Policy  -->  Playwright Surface  -->  Checkpoint Verification  -->  Execution Result

```
This separation makes replay predictable and allows a discovered workflow to be reused without repeatedly asking the LLM to reason about the UI.
## Capability Artifacts

Capabilities are stored as versioned JSON files. Two capability artifacts are generate for this project

```text
artifacts/lookup_member_savings.json
artifacts/open_sub_account.json
```

A capability contains:
- Capability ID
- Version
- Target application
- Runtime inputs
- Outputs
- Recorded steps
- UI targets
- Checkpoints
- Metadata

Example workflow:

```text
Step 1 -> Fill Member ID
Step 2 -> Click Search Member
Step 3 -> Extract Savings Balance
Step 4 -> Finish
```

## Installation

Clone the repository:

```bash
git clone https://github.com/geetika6271/cs-automation-proj.git
cd cs-automation-proj
```

Create a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright:

```bash
playwright install chromium
```

Install frontend dependencies:

```bash
cd bank_app/frontend
npm install
```

## Configuration

Create a `.env` file in the project root adding the API keys and other secured data.

Do not commit the `.env` file or API key to GitHub.

## Running the Application

Start the FastAPI backend on the root directory of the project
```bash
uvicorn bank_app.backend.main:app --reload --port 8001
```
The backend runs on
```text
http://localhost:8001
```
Start the React frontend:
```bash
npm run dev
```

The frontend runs on:
```text
http://localhost:5173
```

## LLM-Driven Discovery

The discovery process is performed in two stages to capture both the successful execution path and the legitimate business outcome.

-The first discovery uses a valid member ID and records the successful case of the functionality.
This captures the steps required to successfully look up a member and retrieve the savings account balance.
- The successful discovery records the successful execution steps and evidence in success_discovery_lookup_log.json.

-The discovery process then runs a second discovery using the business outcome member ID provided through --outcome-member-id. 
This case is used to identify and capture the legitimate business outcome when the requested member does not exist, 
rather than treating the result as a technical failure.
- The business outcome discovery records the expected business outcome and evidence in business_outcome_discovery_log.json.

Run the discovery lookup savings process process with:
```bash
python -m app.cli discover-lookup --goal "Look up member 12345 and retrieve the savings account balance." --outcome-member-id 99999
```

After both discovery processes complete successfully, the system combines the information from both cases into a single capability artifact. The resulting artifact contains the deterministic replay steps from the successful case along with the captured business outcome, allowing the replay system to distinguish between a successful execution and a legitimate business outcome.


## Deterministic Replay

Replay a previously discovered capability:

```bash
python -m app.cli replay artifacts\lookup_member_savings.json --member-id 67890
```

Replay executes the recorded steps in order.The LLM is not used to decide the next action during replay.

## Business Outcomes

Expected application outcomes are represented separately from technical failures.

For example, an unknown member can produce:

```text
Member not found
```

This is represented as a structured business outcome:

```json
{
  "status": "business_outcome",
  "capability_id": "lookup_member_savings",
  "step": "step_2",
  "code": "MEMBER_NOT_FOUND",
  "message": "Member not found"
}
```

## Error Handling

The replay system distinguishes between three types of execution results:

- **Business Outcome** – An expected application result.
- **Recoverable Error** – A temporary failure that can be retried.
- **Hard Failure** – A failure that cannot be safely recovered automatically.

### Recoverable Errors

Transient failures such as the following can be retried:`temporarily unavailable`,`network error`,`connection reset`,`connection refused`, `connection closed`, `timeout`

The executor retries the failed operation up to the configured retry limit of 3 tries before deducing it as hard failure.

### Hard Failures

Examples include: Missing UI elements, Invalid selectors, Unexpected page structure, Unsupported actions, Failed checkpoints,Exhausted recovery attempts

Failure information and screenshots are recorded under:

```text
evidence/failures/
```

## Human-in-the-Loop

Risky actions require human approval before execution continues. 
The project uses a SafetyPolicy and HandoffManager to manage these situations.

For the Open Savings Sub-Account capability, run the discovery command below:
```bash
 python -m app.cli discover-open-sub-account --goal "Open a new savings sub-account for member 12345 with an initial deposit of 570 and reach the confirmation screen"
```

When the automation encounters an action marked safety = human_required, it pauses execution and 
creates a human intervention request containing the intervention ID, goal, current step, reason for stopping, screenshot, and status.
The human then takes control of the same live session, performs the required action, and signals completion. 
The HandoffManager records the human action and updates the request state from pending to approved and then resumed.

After the intervention is complete, control is returned to the automation. 
The page is observed again to verify the resulting UI state before execution continues.


## Safety

Actions are classified by the safety policy. Unknown or unsupported actions are rejected.

| Category | Behavior |
|---|---|
| Safe | Execute automatically |
| Risky | Require human approval |
| Blocked | Do not execute |

### Safe Actions
- navigate, click, fill, extract, finish

### Risky and Blocked Actions 
The risky and blocked actions are identified by adding a data-safety attribute to the relevant UI elements, using values such as data-safety="human_required" or data-safety="blocked".

- Risky actions are actions that require human intervention to complete, such as opening a sub-account. When the automation encounters a human_required action, it pauses and allows the human to take over the live session.
- Blocked actions are actions that the automation is not permitted to perform, such as transferring funds. When the automation encounters a blocked action, it does not execute the action.


## UI Targeting

The system supports multiple UI targeting strategies:
- ID
- Label
- Role
- Text
- data-safety

The banking application uses stable identifiers such as:

```text
member-id
search-member
savings-balance
member-details
```
These targets are stored in the capability artifact and used during replay.

## Checkpoints

Replay verifies that the expected final UI state was reached. Checkpoints can verify properties such as:

- Visibility
- Text content

If the expected checkpoint is not reached, replay reports a failure instead of incorrectly reporting success.

## Evidence and Observability

Execution evidence is stored under:

```text
evidence/
├── discovery/
├── replay/
├── failures/
└── handoff/
```

Evidence can include:
- Discovery logs
- Replay events
- Successful replay results
- Failure screenshots
- Failure information
- Human handoff information

## Testing

Run the complete test suite:
```bash
python -m pytest tests/ -v

```

The tests cover scenarios including:
- Successful replay
- Business outcomes
- Recoverable errors
- Retry behavior
- Hard failures
- Safety policy
- Human approval

## Project Structure

```text
cs-automation-proj/
|
├── app/
│   ├── agent/
│   ├── browser/
│   ├── artifiact/
│   ├── replay/
│   ├── safety/
│   └── escalation/
|
├── artifacts/
│   └── lookup_member_savings.json
│   └── open_sub_account.json
|
├── bank_app/
│   └── frontend/
│   └── backend/
|
├── evidence/
│   ├── discovery/
│   ├── replay/
│   ├── failures/
│   └── handoff/
|
├── tests/
|
├── REPORT.md
├── README.md
└── requirements.txt
```

## Heterogeneity and Multi-Tenant Support

The capability separates the workflow from runtime input values.

Runtime values such as `member_id` and `initial_deposit` are supplied during replay rather than being hard-coded into the workflow.

This allows the same capability structure to be reused with different input values and environments.

## Design Principle

```text
The model discovers.
        |
        v
The artifact becomes the capability.
        |
        v
Deterministic replay executes the capability.
```

The LLM is used for discovery, while replay relies on the saved capability artifact for predictable execution.

