import pytest

from app.safety.policy import (SafetyPolicy,HumanApprovalRequired)

policy = SafetyPolicy()

def test_safe_search_member():

    result = policy.check(
        "click",
        {
            "strategy": "id",
            "value": "search-member",
            "safety": "safe",
        },
    )

    assert result is True



def test_safe_fill_member_id():
    result = policy.check(
        "fill",
        {
            "strategy": "id",
            "value": "member-id",
            "safety": "safe",
        },
    )

    assert result is True


def test_safe_fill_initial_deposit():
    result = policy.check(
        "fill",
        {
            "strategy": "id",
            "value": "initial-deposit",
            "safety": "safe",
        },
    )

    assert result is True


def test_approve_sub_account_requires_human():
    with pytest.raises(HumanApprovalRequired):
        policy.check(
            "click",
            {
                "strategy": "id",
                "value": "approve-sub-account",
                "safety": "human_required",
            },
        )


def test_transfer_funds_is_blocked():
    with pytest.raises(PermissionError):
        policy.check(
            "click",
            {
                "strategy": "id",
                "value": "transfer-funds",
                "safety": "blocked",
            },
        )


def test_unknown_action_is_rejected():

    with pytest.raises(PermissionError):
        policy.check( "unknown_action", None)