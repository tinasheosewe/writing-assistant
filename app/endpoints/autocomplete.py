import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..models import AutocompleteRequest
from ..utils import create_messages, send_openai_request
import json_repair

router = APIRouter()

class AutoCompleteResponse(BaseModel):
    completion: str = Field(..., description="The autocompleted text.")

@router.post("/autocomplete", summary="Autocomplete with OpenAI API")
async def autocomplete(data: AutocompleteRequest):
    logging.info("Received request with data: %s", data)
    
    if not (0 <= data.creativity_level <= 1):
        raise HTTPException(status_code=400, detail="Creativity level must be between 0 and 1.")

    if not data.partial_input and not data.context and not data.section_outline:
        raise HTTPException(status_code=400, detail="At least one of 'partial_input', 'context', or 'section_outline' is required.")

    system_prompt = (
        "You are a helpful assistant tasked with text completion. "
        "Use the given inputs, such as partial input, section outline outline, or context, to generate a coherent completion. "
        "Ensure the completion adheres to the specified level (e.g., sentence, paragraph, story) and targets the "
        "provided word count as a general guideline for length."
    )
    task = "Complete the text."
    structured_payload = {
        "task": "autocomplete",
        "user_input": {
            "task": task,
            "completion_level": data.completion_level,
            "partial_input": data.partial_input,
            "section_outline": data.section_outline.model_dump(exclude='target_word_count'),
            "tone": data.tone,
            "writing_style": data.writing_style,
            "writing_level": data.writing_level,
            "word_count": data.word_count
        },
        "retrieved_context": data.context
    }
    messages = create_messages( system_prompt, structured_payload=structured_payload )

    return json_repair.loads(send_openai_request(messages, data.creativity_level, AutoCompleteResponse))