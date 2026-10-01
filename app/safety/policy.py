SAFE_ACTIONS = {
    "navigate",
    "click",
    "fill",
    "extract",
    "finish",
}

RISKY_ACTIONS = {
    "open_sub_account",
    "submit_transaction",
}

BLOCKED_ACTIONS = {
    "transfer_money",
    "delete_account",
}


class HumanApprovalRequired(PermissionError):
    pass


class SafetyPolicy:

    def check(self, action_type, target=None):

        # Explicitly blocked action types
        if action_type in BLOCKED_ACTIONS:
            raise PermissionError(
                f"Action blocked by safety policy: {action_type}"
            )

        # Explicitly risky action types
        if action_type in RISKY_ACTIONS:
            raise HumanApprovalRequired(
                f"Human approval required for action: {action_type}"
            )

        # Inspect UI-provided safety metadata
        safety = self._get_safety(target)

        if safety == "blocked":
            raise PermissionError("Action blocked by safety policy")

        if safety == "human_required":
            raise HumanApprovalRequired("Human approval required for this UI action")

        # Only explicitly safe action types are allowed
        if action_type not in SAFE_ACTIONS:
            raise PermissionError(f"Unknown action: {action_type}" )

        return True

    @staticmethod
    def _get_safety(target):
        if target is None:
            return None

        if isinstance(target, dict):
            return target.get("safety")

        return getattr(target, "safety", None)