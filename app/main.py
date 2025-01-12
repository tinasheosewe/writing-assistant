import os
from dotenv import load_dotenv

#  Test endpoints at the following URL
# http://127.0.0.1:8000/docs

# Load environment variables from .env
load_dotenv()

# Verify that the environment variable is loaded
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

from fastapi import FastAPI
from .endpoints import autocomplete, generate_synopsis, synopsis_to_outline, outline_to_document
from .utils import custom_openapi

# FastAPI app initialization
app = FastAPI()

# Include endpoints
app.include_router(autocomplete.router)
app.include_router(generate_synopsis.router)
app.include_router(synopsis_to_outline.router)
app.include_router(outline_to_document.router)

# Custom OpenAPI schema (if needed)
app.openapi = lambda: custom_openapi(app)

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)