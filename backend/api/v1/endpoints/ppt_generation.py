from fastapi import APIRouter, HTTPException
from backend.schemas.ppt_generation import PPTGenerationRequest, PPTGenerationResponse, SlideContent
from backend.services.ppt_generator import PPTGeneratorService
from typing import List
import os

router = APIRouter()
ppt_service = PPTGeneratorService()

@router.post("/generate_ppt", response_model=PPTGenerationResponse)
async def generate_ppt(request: PPTGenerationRequest):
    try:
        if not request.topic:
            raise HTTPException(status_code=400, detail="Topic is required")
            
        result = ppt_service.generate_ppt(request)
        
        return PPTGenerationResponse(
            status="success",
            ppt_url=result["ppt_url"],
            slides=result["slides"],
            message="Presentation generated successfully"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
