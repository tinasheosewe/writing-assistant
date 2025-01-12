from enum import Enum
import json
import logging
import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
import json_repair
from pydantic import BaseModel, Field, RootModel
from openai import OpenAI
import random
from fastapi.openapi.utils import get_openapi

#  Test endpoints at the following URL
# http://127.0.0.1:8000/docs

# Load environment variables from .env
load_dotenv()

# FastAPI app initialization
app = FastAPI()

# OpenAI API Key
client = OpenAI( api_key = os.getenv("OPENAI_API_KEY") )
if not client.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Define an Enum for completion levels
class CompletionLevel(str, Enum):
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    DOCUMENT = "document"

class OutlineGranularity(str, Enum):
    PARAGRAPH = "paragraph"
    PAGE = "page"
    CHAPTER = "chapter"
    SECTION = "section"

    DETAILED = "detailed"
    HIGH_LEVEL = "high-level"

class Tone(str, Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    NEUTRAL = "neutral"

class WritingStyle(str, Enum):
    DESCRIPTIVE = "descriptive"
    NARRATIVE = "narrative"
    EXPOSITORY = "expository"
    PERSUASIVE = "persuasive"
    CREATIVE = "creative"

class WritingLevel(str, Enum):
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle school"
    HIGH_SCHOOL = "high school"
    COLLEGE = "college"
    GRADUATE = "graduate"
    PROFESSIONAL = "professional"

class DocumentSection(BaseModel):
    header: str = ""
    content: str = ""

class OutlineSection(BaseModel):
    header: str = ""
    target_word_count: int = 0
    content: str = ""

class OutputText(BaseModel):
    tone: Tone = Tone.NEUTRAL
    writing_style: WritingStyle = WritingStyle.DESCRIPTIVE
    writing_level: WritingLevel = WritingLevel.COLLEGE
    creativity_level: float = 0.7

# Models for request validation
class AutocompleteRequest(OutputText):
    context: list[str] = []
    partial_input: str = ""
    task: str = "Complete the text."
    word_count: int = 20
    completion_level: CompletionLevel = CompletionLevel.SENTENCE
    section_outline: OutlineSection = []

class GenerateSynopsisRequest(OutputText):
    genre: str = "" 
    target_audience: str = "" 
    setting: str = "" 
    main_characters: List[str] = [] 
    central_conflict_or_goal: str = "" 
    themes: List[str] = [] 
    plot_structure_or_key_events: List[str] = [] 
    tone: str = "" 
    perspective: str = "" 
    unique_elements: List[str] = [] 
    document_type: str = ''

class ConvertSynopsisToOutlineRequest(BaseModel): # This should NOT inherit from OutputText
    document_type: str = ""
    document_length_in_pages: int = 0.5 # The desired length of the document in pages
    outline_granularity: OutlineGranularity = OutlineGranularity.DETAILED
    audience: str = ""
    key_focus_areas: List[str] = []  # Key points to emphasize in the outline
    synopsis: str = ""
    creativity_level: float = 0.7

class ConvertOutlineToDocumentRequest(OutputText):
    document_type: str = ""
    genre: str = ""
    target_audience: str = ""
    outline: List[OutlineSection] = []
    previous_content: List[DocumentSection] = []

def create_messages( system_prompt: str, data: Dict[str, Any] = None, task: str = None, structured_payload: Dict[str, Any] = None) -> list:
    if (task is None or data is None) and structured_payload is None:
        raise ValueError("Either 'structured_payload' or both 'task' and 'system_prompt' must be provided.")
    
    if structured_payload is None:
        structured_payload = {
            "task": task,
            "user_input": {k: v for k, v in data.items()},
        }

    logging.debug("Structured payload: %s", structured_payload)

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {"role": "user", "content": json.dumps(structured_payload)}
    ]

    return messages

def send_openai_request(messages: list, creativity_level: float, response_format: Dict[str, Any]) -> dict:
    try:
        logging.debug("Sending request to OpenAI API")
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            temperature=creativity_level,
            response_format=response_format,
        )
        logging.debug("Received response from OpenAI API: %s", response)
        output = response.choices[0].message.content.strip()
        return output
    except Exception as e:
        logging.error("Error during OpenAI API request: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Autocomplete endpoint
@app.post("/autocomplete", summary="Autocomplete with OpenAI API")
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
    structured_payload = {
        "task": "autocomplete",
        "user_input": {
            "task": data.task,
            "completion_level": data.completion_level,
            "partial_input": data.partial_input,
            "section_outline": data.section_outline,
            "tone": data.tone,
            "writing_style": data.writing_style,
            "writing_level": data.writing_level,
            "word_count": data.word_count
        },
        "retrieved_context": data.context
    }
    messages = create_messages( system_prompt, structured_payload=structured_payload )


    class AutoCompleteFormat(BaseModel):
        completion: str = Field(..., description="The autcompleted text.")

    return json_repair.loads(send_openai_request(messages, data.creativity_level, AutoCompleteFormat))["synopsis"]

# Generate Story endpoint
@app.post("/generate_synopsis", summary="Generate Synopsis with OpenAI API")
async def generate_synopsis(data: GenerateSynopsisRequest):
    logging.info("Received request with data: %s", data)
    
    if not (0 <= data.creativity_level <= 1):
        raise HTTPException(status_code=400, detail="Creativity level must be between 0 and 1.")

    task = "generate a synopsis for a coherent document given inputs"
    system_prompt = "You are a helpful assistant tasked with generating a synopsis using the given inputs."
    messages = create_messages( system_prompt, task=task, data=data.model_dump(exclude='creativity_level') )

    class SynopsisFormat(BaseModel):
        synopsis: str = Field(..., description="The generated synopsis.")

    return json_repair.loads(send_openai_request(messages, data.creativity_level, SynopsisFormat))["synopsis"]
    
# Convert Synopsis To Outline endpoint
@app.post("/synopsis_to_outline", summary="Convert Synopsis to Outline with OpenAI API")
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
        "Include a title in the metadata for the outline."
    )

    messages = create_messages( system_prompt, task=task, data=data.model_dump(exclude='creativity_level') )

    class Section(BaseModel):
        header: str = Field(..., description="The name of the section.")
        target_word_count: int = Field(..., description="The recommended word count for the section.")
        content: str = Field(..., description="The detailed content of the section.")

    class OutlineMetadata(BaseModel):
        title: str = Field(..., description="The title of the document.")

    class OutlineResponse(BaseModel):
        sections: List[Section] = Field(..., description="A list of sections representing the outline.")
        metadata: OutlineMetadata = Field(..., description="Metadata for the outline.")

    return json_repair.loads(send_openai_request(messages, data.creativity_level, OutlineResponse))["sections"]

@app.post("/outline_to_document", summary="Convert Outline to Document with OpenAI API")
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

    class DocumentResponse(BaseModel):
        header: str = Field(..., description="The name of the section.")
        content: str = Field(..., description="The detailed content of the section.")

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

# Custom OpenAPI schema (if needed)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My FastAPI API",
        version="1.0.0",
        description="An example API converted from Flask to FastAPI",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
