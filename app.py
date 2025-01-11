from enum import Enum
import json
import logging
import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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

# Models for request validation
class AutocompleteRequest(BaseModel):
    context: list[str] = []
    partial_input: str = ""
    task: str = "Complete the text."
    word_count: int = 20
    completion_level: CompletionLevel = CompletionLevel.SENTENCE
    story_outline: list[str] = []
    creativity_level: float = 0.7

class GenerateSynopsisRequest(BaseModel):
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
    creativity_level: float = 0.7

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

# Autocomplete endpoint
@app.post("/autocomplete", summary="Autocomplete with OpenAI API")
async def autocomplete(data: AutocompleteRequest):
    logging.info("Received request with data: %s", data)
    
    if not data.partial_input and not data.context and not data.story_outline:
        raise HTTPException(status_code=400, detail="At least one of 'partial_input', 'context', or 'story_outline' is required.")
    
    if not (0 <= data.creativity_level <= 1):
        raise HTTPException(status_code=400, detail="Creativity level must be between 0 and 1.")

    system_prompt = (
        "You are a helpful assistant tasked with text completion. "
        "Use the given inputs, such as partial input, story outline, or context, to generate a coherent completion. "
        "Ensure the completion adheres to the specified level (e.g., sentence, paragraph, story) and targets the "
        "provided word count as a general guideline for length."
    )
    structured_payload = {
        "task": "autocomplete",
        "user_input": {
            "task": data.task,
            "completion_level": data.completion_level,
            "partial_input": data.partial_input,
            "story_outline": data.story_outline,
            "word_count": data.word_count
        },
        "retrieved_context": data.context
    }
    messages = create_messages( system_prompt, structured_payload=structured_payload )

    try:
        logging.debug("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=data.creativity_level
        )
        logging.debug("Received response from OpenAI API: %s", response)
        completion = response.choices[0].message.content.strip()
        return {"completion": completion}
    except Exception as e:
        logging.error("Error during OpenAI API request: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Generate Random Story endpoint
@app.post("/generate_synopsis", summary="Generate Synopsis with OpenAI API")
async def generate_synopsis(data: GenerateSynopsisRequest):
    logging.info("Received request with data: %s", data)
    
    if not (0 <= data.creativity_level <= 1):
        raise HTTPException(status_code=400, detail="Creativity level must be between 0 and 1.")

    task = "generate a synopsis for a coherent document given inputs"
    system_prompt = "You are a helpful assistant tasked with generating a synopsis using the given inputs."
    messages = create_messages( system_prompt, task=task, data=data.model_dump(),  )

    try:
        logging.debug("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=data.creativity_level
        )
        logging.debug("Received response from OpenAI API: %s", response)
        completion = response.choices[0].message.content.strip()
        return {"completion": completion}
    except Exception as e:
        logging.error("Error during OpenAI API request: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

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
