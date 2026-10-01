from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .dummy_data import MEMBERS

app = FastAPI(title="Banking App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/members/{member_id}")
def get_member(member_id: str):
    member = MEMBERS.get(member_id)

    if not member:
        return {
            "found": False,
            "message": "Member not found"
        }

    return {
        "found": True,
        "member": member
    }


from pydantic import BaseModel


class SubAccountRequest(BaseModel):
    account_type: str
    initial_deposit: float


@app.post("/api/members/{member_id}/sub-accounts")
def open_sub_account( member_id: str, request: SubAccountRequest):
    member = MEMBERS.get(member_id)

    if not member:
        return {
            "success": False,
            "code": "MEMBER_NOT_FOUND",
            "message": "Member not found"
        }


    if request.initial_deposit < 0:
        return {
            "success": False,
            "code": "INVALID_INITIAL_DEPOSIT",
            "message": "Initial deposit cannot be negative"
        }

    sub_account_number = len(member["sub_accounts"]) + 1

    sub_account = {
        "id": f"{member_id}-SUB-{sub_account_number:03d}",
        "type": "Savings Sub-Account",
        "balance": request.initial_deposit,
        "status": "Active",
    }

    member["sub_accounts"].append(sub_account)


    return {
        "success": True,
        "message": "Sub-account opened successfully",
        "sub_account": sub_account,
    }