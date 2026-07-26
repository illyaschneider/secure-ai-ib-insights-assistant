from pathlib import Path
from datetime import datetime, timezone
import json


CURRENT_PATH = Path(__file__).parent.resolve()
ROOT_FOLDER_PATH = CURRENT_PATH.parents[1]
AUDIT_PATH = ROOT_FOLDER_PATH / "data" / "audit_logs" / "audit_log.jsonl"

def write_audit_log(
    request_id: str,
    endpoint: str,
    role: str,
    status: str,
    question: str | None = None,
    matched_intent: str | None = None,
    tool_used: str | None = None,
    include_documents: bool = None,
    document_search_status: str | None = None,
    document_search_query: str | None = None,
    answer_mode: str | None = None,
    required_permission: str | None = None,
    message: str | None = None,
) -> dict:
    event = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "role": role,
        "question": question,
        "matched_intent": matched_intent,
        "tool_used": tool_used,
        "include_documents": include_documents,
        "document_search_status": document_search_status,
        "document_search_query": document_search_query,
        "answer_mode": answer_mode,
        "required_permission": required_permission,
        "status": status,
        "message": message,
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with AUDIT_PATH.open(mode="a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")

    return event


def main():
    #audit_logger()
    pass

if __name__ == "__main__":
    main()