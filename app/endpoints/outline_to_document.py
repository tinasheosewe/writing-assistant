import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.models import ConvertOutlineToDocumentRequest
from app.utils import create_messages, send_openai_request
import json_repair

router = APIRouter()

class DocumentResponse(BaseModel):
    header: str = Field(..., description="The name of the section.")
    content: str = Field(..., description="The detailed content of the section.")

@router.post("/outline_to_document", summary="Convert an outline to a detailed document.")
async def outline_to_document(data: ConvertOutlineToDocumentRequest):
    logging.info("Received request with data: %s", data)

    if not (0 <= data.creativity_level <= 1):
        raise HTTPException(status_code=400, detail="Creativity level must be between 0 and 1.")
    
    if not data.document_type:
        raise HTTPException(status_code=400, detail="Document type is required.")

    system_prompt = (
        f"You are a skilled writer tasked with generating sections of a {data.document_type}. "
        "Write each section in detail, based on its header and outline content. "
        "Ensure clarity, logical flow, and alignment with the specified document type."
    )
    task_template = (
        "Write the content for the section titled '{header}' based on the outline provided. "
        "Ensure the content is approximately {target_word_count} words and aligns with the {document_type} format. "
        "Use the content of the previous sections for context and maintain logical flow."
    )

    # Process each section sequentially
    for section in data.outline:
        system_prompt
        task = task_template.format(header=section.header, target_word_count=section.target_word_count, document_type=data.document_type)
        
        structured_payload = {
            "task": task,
            "user_input": {
                "task": task,
                "genre": data.genre,
                "target_audience": data.target_audience,
                "outline": section.model_dump(),
            },
            "previous_content": [ x.model_dump() for x in data.previous_content]
        }
        messages = create_messages( system_prompt, structured_payload=structured_payload )

        try:
            # Sequentially send requests and wait for the response
            logging.info("Processing section: %s", section.header)
            response = json_repair.loads(send_openai_request(messages, data.creativity_level, DocumentResponse))
            
            # Append the processed section to the final document
            data.previous_content.append(DocumentResponse(header=response["header"], content=response["content"]))

        except Exception as e:
            logging.error("Error generating section '%s': %s", section.header, str(e))
            raise HTTPException(status_code=500, detail=f"Failed to generate section '{section.header}': {str(e)}")

    # Return the final document response
    return data.previous_content