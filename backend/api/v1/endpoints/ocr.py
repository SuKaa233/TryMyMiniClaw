from fastapi import APIRouter, HTTPException, UploadFile, File
import httpx
import base64
import os

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from backend.services.session import load_session_messages, save_session_messages, serialize_message

router = APIRouter()

# Kimi Vision API URL (Moonshot)
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"
# Using the provided Kimi API key
KIMI_API_KEY = "sk-WUtN5BBO9J8FtpGheG9vzwk5QDgXPQ67DaqGMNDTJ2hTWw5p"

@router.post("/recognize")
async def recognize_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        mime_type = file.content_type or "image/jpeg"
        image_url = f"data:{mime_type};base64,{base64_image}"

        # Moonshot Vision API format (Standard OpenAI compatible)
        payload = {
            "model": "moonshot-v1-8k-vision-preview", # Kimi's vision model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请精确提取这张图片中的所有文字内容，保持原有的段落格式。如果包含表格，请用Markdown表格表示。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KIMI_API_KEY}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                KIMI_API_URL, 
                json=payload, 
                headers=headers,
                timeout=60.0
            )
            
            if response.status_code != 200:
                print(f"Kimi API Error: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="OCR Service Error")
                
            data = response.json()
            
            try:
                extracted_text = data['choices'][0]['message']['content']
                return {"text": extracted_text}
            except (KeyError, IndexError) as e:
                print(f"Unexpected response format: {data}")
                raise HTTPException(status_code=500, detail="Unexpected response format from OCR service")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class OCRChatRequest(BaseModel):
    message: str
    context: str
    session_id: str

@router.post("/chat")
async def ocr_chat(request: OCRChatRequest):
    messages = load_session_messages(request.session_id)
    initial_len = len(messages)
    
    if initial_len == 0:
        # First message, inject OCR context
        system_prompt = (
            "You are an AI assistant analyzing an image that has been OCR'd (Optical Character Recognition). "
            "Here is the exact text extracted from the image. Use ONLY this text to answer the user's questions about the image.\n\n"
            f"--- EXTRACTED TEXT ---\n{request.context}\n----------------------"
        )
        messages.append(SystemMessage(content=system_prompt))
        
    messages.append(HumanMessage(content=request.message))
    
    try:
        # Use Moonshot/Kimi for chat as well since we are using their key
        llm = ChatOpenAI(
            model_name="moonshot-v1-8k",
            openai_api_key=KIMI_API_KEY,
            openai_api_base="https://api.moonshot.cn/v1",
            temperature=0.3
        )
        
        response = await llm.ainvoke(messages)
        messages.append(response)
        
        save_session_messages(request.session_id, messages)
        
        return {"reply": response.content}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
