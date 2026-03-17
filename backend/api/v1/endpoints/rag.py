from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import StreamingResponse
from backend.services.rag_service import rag_service
from backend.schemas.rag import RagQuery
import json

from fastapi.concurrency import run_in_threadpool

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename or "unknown"
        # Run synchronous CPU/IO bound process_file in a threadpool
        result = await run_in_threadpool(rag_service.process_file, content, filename)
        return {"message": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_rag(query: RagQuery):
    return StreamingResponse(
        rag_service.answer_stream(query.question),
        media_type="text/event-stream"
    )

@router.get("/documents")
async def get_documents():
    return rag_service.vector_store.get_documents_metadata()

@router.delete("/documents")
async def clear_documents():
    success = rag_service.vector_store.clear_database()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear database")
    return {"message": "Knowledge base cleared successfully"}
