from fastapi import FastAPI, HTTPException
from uuid import uuid4
from backend.app.tools.revenue_summary_tool import revenue_by_year
from backend.app.tools.pipeline_comparison_tool import pipeline_comparison
from backend.app.tools.sector_evidence_tool import get_sector_evidence
from backend.app.tools.document_retrieval_tool import retrieve_document_evidence
from backend.app.tools.analyst_response_tool import generate_summary_paragraph
from backend.app.tools.question_router_tool import route_question
from backend.app.tools.ai_response_tool import polish_analyst_answer
from backend.app.security import require_permission, PermissionDeniedError
from backend.app.audit_logger import write_audit_log

app = FastAPI()

@app.get("/api/revenue/{year}")
def get_revenue_by_year(year: int, role: str):
    try:
        require_permission(role, permission="revenue_ranking")
        return revenue_by_year(year)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PermissionDeniedError as error:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "permission_denied",
                "role": error.role,
                "required_permission": error.permission,
                "message": error.message,
            },
        ) from error

@app.get("/api/pipeline/compare")
def get_pipeline_comparison(sector_a: str, sector_b: str, role: str):
    try:
        require_permission(role, permission="pipeline_comparison")
        return pipeline_comparison(sector_a, sector_b)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PermissionDeniedError as error:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "permission_denied",
                "role": error.role,
                "required_permission": error.permission,
                "message": error.message,
            },
        ) from error

@app.get("/api/sectors/evidence")
def get_sector_summary_evidence(sector: str, quarter: str, role: str):
    try:
        require_permission(role, permission="sector_analysis")
        return get_sector_evidence(sector, quarter)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PermissionDeniedError as error:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "permission_denied",
                "role": error.role,
                "required_permission": error.permission,
                "message": error.message,
            },
        ) from error

@app.get("/api/documents/search")
def get_documents_search(query: str, role: str):
    request_id = str(uuid4())
    try:
        require_permission(role, "document_search")
        search_result = retrieve_document_evidence(query)
        search_result["request_id"] = request_id
        return search_result
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PermissionDeniedError as error:
        raise HTTPException(
            status_code=403,
            detail={
                "request_id": request_id,
                "error": "permission_denied",
                "role": error.role,
                "required_permission": error.permission,
                "message": error.message,
            },
        ) from error

@app.get("/api/analyst/sector-analysis")
def get_analyst_sector_analysis(sector: str, quarter: str, role: str):
    try:
        require_permission(role, permission="sector_analysis")
        return generate_summary_paragraph(sector, quarter)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PermissionDeniedError as error:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "permission_denied",
                "role": error.role,
                "required_permission": error.permission,
                "message": error.message,
            },
        ) from error

@app.get("/api/assistant/ask")
def ask_assistant(question: str, role: str):
    request_id = str(uuid4())
    try:
        router_result = route_question(question)
        require_permission(role, router_result["matched_intent"])
        router_result["request_id"] = request_id
        write_audit_log(
            request_id=request_id,
            endpoint="/api/assistant/ask",
            role=role,
            question=question,
            matched_intent=router_result["matched_intent"],
            tool_used=router_result["tool_used"],
            answer_mode="deterministic",
            status = "success"
        )
        return router_result
    except ValueError as error:
        write_audit_log(
            request_id=request_id,
            endpoint="/api/assistant/ask",
            role=role,
            question=question,
            status="validation_error",
            message=str(error),
        )
        raise HTTPException(
            status_code=400,
            detail={
                "request_id": request_id,
                "error": "bad_request",
                "message": str(error),
            },
        )
    except PermissionDeniedError as error:
        write_audit_log(
            request_id=request_id,
            endpoint="/api/assistant/ask",
            role=error.role,
            required_permission=error.permission,
            question=question,
            status="permission_denied",
            message=error.message)
        raise HTTPException(
            status_code=403,
            detail={
                "request_id": request_id,
                "error": "permission_denied",
                "role": error.role,
                "required_permission": error.permission,
                "message": error.message,
            },
        ) from error

@app.get("/api/assistant/ask-ai")
def ask_assistant_ai(question: str, role: str, include_documents: bool = False):
    request_id = str(uuid4())
    try:
        router_result = route_question(question)
        require_permission(role, router_result["matched_intent"])
        tool_used = router_result["tool_used"]
        if include_documents:
            require_permission(role, permission="document_search")
            tool_used += ", get_documents_search"
        require_permission(role, permission="ai_polishing")
        ai_result = polish_analyst_answer(router_result, include_documents=include_documents)
        ai_result["request_id"] = request_id
        ai_result["include_documents"] = include_documents

        write_audit_log(
            request_id=request_id,
            endpoint="/api/assistant/ask-ai",
            role=role,
            question=question,
            matched_intent=router_result["matched_intent"],
            tool_used=tool_used,
            include_documents=include_documents,
            document_search_status=ai_result["document_search"].get("status", "disabled"),
            document_search_query=ai_result["document_search"].get("query"),
            answer_mode=ai_result["answer_mode"],
            status="success"
        )
        return ai_result
    except ValueError as error:
        write_audit_log(
            request_id=request_id,
            endpoint="/api/assistant/ask-ai",
            role=role,
            question=question,
            status="validation_error",
            message=str(error),
        )
        raise HTTPException(
            status_code=400,
            detail={
                "request_id": request_id,
                "error": "bad_request",
                "message": str(error),
            },
        )
    except PermissionDeniedError as error:
        write_audit_log(
            request_id=request_id,
            endpoint="/api/assistant/ask-ai",
            role=error.role,
            required_permission=error.permission,
            question=question,
            status="permission_denied",
            message=error.message)
        raise HTTPException(
            status_code=403,
            detail={
                "request_id": request_id,
                "error": "permission_denied",
                "role": error.role,
                "required_permission": error.permission,
                "message": error.message,
            },
        ) from error



#fastapi dev --entrypoint backend.app.main:app - running FastAPI in terminal
#http://127.0.0.1:8000/docs - FastAPI docs
