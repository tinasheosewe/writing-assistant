import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.models import GenerateSynopsisRequest
from app.utils import create_messages, send_openai_request
import json_repair

router = APIRouter()

class SynopsisResponse(BaseModel):
    synopsis: str = Field(..., description="The generated synopsis.")

@router.post("/generate_synopsis", summary="Generate a synopsis for a hypothetical document based on the provided inputs.")
async def generate_synopsis(data: GenerateSynopsisRequest):
    logging.info("Received request with data: %s", data)
    
    if not (0 <= data.creativity_level <= 1):
        raise HTTPException(status_code=400, detail="Creativity level must be between 0 and 1.")

    task = "generate a synopsis for a coherent document given inputs"
    system_prompt = "You are a helpful assistant tasked with generating a synopsis using the given inputs."
    messages = create_messages( system_prompt, task=task, data=data.model_dump(exclude='creativity_level') )

    return json_repair.loads(send_openai_request(messages, data.creativity_level, SynopsisResponse))["synopsis"]