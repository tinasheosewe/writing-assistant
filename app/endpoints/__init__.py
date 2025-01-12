from fastapi import APIRouter
from .autocomplete import router as autocomplete_router
from .generate_synopsis import router as generate_synopsis_router
from .synopsis_to_outline import router as synopsis_to_outline_router
from .outline_to_document import router as outline_to_document_router

router = APIRouter()

router.include_router(autocomplete_router, prefix="/autocomplete", tags=["autocomplete"])
router.include_router(generate_synopsis_router, prefix="/generate_synopsis", tags=["generate_synopsis"])
router.include_router(synopsis_to_outline_router, prefix="/synopsis_to_outline", tags=["synopsis_to_outline"])
router.include_router(outline_to_document_router, prefix="/outline_to_document", tags=["outline_to_document"])