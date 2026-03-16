from pydantic import BaseModel, Field
from typing import List, Optional

class SlideContent(BaseModel):
    title: str = Field(description="The main title of the slide")
    subtitle: Optional[str] = Field(None, description="The subtitle of the slide")
    points: List[str] = Field(description="Key points or bullet points for the slide content")
    layout: str = Field("bullet_points", description="Suggested layout for the slide (e.g., 'title_only', 'bullet_points', 'two_column')")
    theme_color: Optional[str] = Field(None, description="Suggested accent color hex code for this slide")

class PPTGenerationRequest(BaseModel):
    topic: str = Field(description="The topic or short description for the presentation")
    slide_count: int = Field(5, description="Number of slides to generate")

class PPTGenerationResponse(BaseModel):
    status: str
    ppt_url: Optional[str] = None
    message: Optional[str] = None
    slides: Optional[List[SlideContent]] = None
