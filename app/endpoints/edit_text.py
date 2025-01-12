from fastapi import APIRouter
import json_repair
from pydantic import BaseModel, Field

from app.models import EditSubstringRequest
from app.utils import create_messages, send_openai_request

router = APIRouter()

class EditSubstringResponse(BaseModel):
    updated_text: str = Field(..., description="The updated version of 'text_to_edit' after applying the changes.")

# Helper function for integrating the inputs and sending them to the LLM
@router.post("/edit_text", summary="Edit a specific substring in text based on context and instructions.")
async def edit_text(data: EditSubstringRequest):
    # Prepare the prompt for the LLM
    system_prompt = (
        "You are a highly skilled text editor. Your task is to apply specific changes to a substring within a larger text. "
        "Take into account the given outline for context, and ensure the edits align with the preceding and subsequent text."
    )
    
    task = (
        f"Modify the indicated text as explained in the instructions while keeping the surrounding text coherent. "
        "Ensure the output aligns with the given outline and retains logical flow."
    )
    messages = create_messages( system_prompt, task=task, data=data.model_dump(exclude='creativity_level') )
    
    return json_repair.loads(send_openai_request(messages, data.creativity_level, EditSubstringResponse))["updated_text"]