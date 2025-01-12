import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..models import ConvertSynopsisToOutlineRequest
from ..utils import create_messages, send_openai_request
import json_repair

router = APIRouter()

class Section(BaseModel):
    header: str = Field(..., description="The name of the section.")
    target_word_count: int = Field(..., description="The recommended word count for the section.")
    content: str = Field(..., description="The detailed content of the section.")

class OutlineMetadata(BaseModel):
    title: str = Field(..., description="The title of the document.")

class OutlineResponse(BaseModel):
    sections: List[Section] = Field(..., description="A list of sections representing the outline.")
    metadata: OutlineMetadata = Field(..., description="Metadata for the outline.")

@router.post("/synopsis_to_outline", summary="Convert a synopsis to a detailed document outline.")
async def synopsis_to_outline(data: ConvertSynopsisToOutlineRequest):
    logging.info("Received request with data: %s", data)
    
    if not (0 <= data.creativity_level <= 1):
        raise HTTPException(status_code=400, detail="Creativity level must be between 0 and 1.")

    if not data.document_type:
        raise HTTPException(status_code=400, detail="Document type is required.")

    system_prompt = (
       f"You are a helpful assistant tasked with converting synopses into detailed {data.document_type} outlines. "
        "Tailor the outline to the specified document type, audience, and key focus areas."
    )

    task = (
        "Structure the outline with multiple distinct sections, each represented as a separate object with its "
        "own heading, details, and target word count appropriate for the document length. "
        "Ensure that each section maintains clarity, logical flow, and aligns with the specified document type."
    )

    modified_data = data.model_dump(exclude='creativity_level')
    modified_data["target_word_count"] = data.document_length_in_pages * 500  # Assuming 500 words per page

    messages = create_messages( system_prompt, task=task, data=modified_data )

    return json_repair.loads(send_openai_request(messages, data.creativity_level, OutlineResponse))