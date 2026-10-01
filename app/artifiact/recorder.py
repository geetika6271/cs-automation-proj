import json
from pathlib import Path
from datetime import datetime, UTC

def redact(value):

    if isinstance(value, dict):
        return {key: redact(val) for key, val in value.items()}

    if isinstance(value, list):
        return [redact(item) for item in value]

    if isinstance(value, str):
        sensitive_terms = ["password","token","api_key","authorization","secret","bearer"]
        for term in sensitive_terms:
            if term.lower() in value.lower():
                return "[REDACTED]"

    return value

class ActionRecorder:

    def __init__(self):
        self.events=[]

    def record(self,step,action,result=None,state=None,status="completed",error=None):
        self.events.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "step": step,
            "action": action.model_dump()
                if hasattr(action, "model_dump")
                else action,
            "state": redact(state),
            "result": redact(result),
            "status": status,
            "error": error,
        })

    def record_event(self,event_type,data=None):
        self.events.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "data": data or {},
        })

    def save(self,path):
        path = Path(path)
        path.parent.mkdir(parents=True,exist_ok=True)

        with open(path,"w",encoding="utf-8") as f:
            json.dump(self.events,f,indent=2,ensure_ascii=False,default=str)