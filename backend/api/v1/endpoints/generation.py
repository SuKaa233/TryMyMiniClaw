from fastapi import APIRouter, HTTPException
from backend.schemas.image_generation import ImageGenerationRequest, ImageGenerationResponse
from backend.services.image_generator import ImageGeneratorService
from typing import List
import os

router = APIRouter()
image_service = ImageGeneratorService()

@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_images(request: ImageGenerationRequest):
    try:
        # 1. 验证参数
        if not request.prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
            
        # 2. 调用服务生成图片
        generated_urls = image_service.generate_images(request)
        
        if not generated_urls:
             return ImageGenerationResponse(
                status="error",
                images=[],
                message="No images generated"
            )
        
        # 3. 返回成功响应
        return ImageGenerationResponse(
            status="success",
            images=generated_urls,
            message="Images generated successfully"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
