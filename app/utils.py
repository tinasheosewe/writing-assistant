import logging
import json
import os
from fastapi import HTTPException
from openai import OpenAI
from pydantic import BaseModel
from fastapi.openapi.utils import get_openapi

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

def create_messages(system_prompt: str, data: dict = None, task: str = None, structured_payload: dict = None) -> list:
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

def send_openai_request(messages: list, creativity_level: float, response_format: BaseModel) -> dict:
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

def custom_openapi(app):
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