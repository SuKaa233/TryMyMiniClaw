from pydantic import BaseModel
from typing import List, Optional

class ImageGenerationRequest(BaseModel):
    prompt: str
    resolution: str = "1024x1024"
    aspect_ratio: str = "1:1"
    variations: int = 1

class ImageGenerationResponse(BaseModel):
    status: str
    images: List[str]
    message: Optional[str] = None
