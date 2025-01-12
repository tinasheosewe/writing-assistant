from pydantic import BaseModel, Field
from .enums import Tone, WritingStyle, WritingLevel, CompletionLevel, OutlineGranularity

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
    word_count: int = 20
    completion_level: CompletionLevel = CompletionLevel.SENTENCE
    section_outline: OutlineSection = OutlineSection()

class GenerateSynopsisRequest(OutputText):
    genre: str = "" 
    target_audience: str = "" 
    setting: str = "" 
    main_characters: list[str] = [] 
    central_conflict_or_goal: str = "" 
    themes: list[str] = [] 
    plot_structure_or_key_events: list[str] = [] 
    tone: str = "" 
    perspective: str = "" 
    unique_elements: list[str] = [] 
    document_type: str = ''

class ConvertSynopsisToOutlineRequest(BaseModel): # This should NOT inherit from OutputText
    document_type: str = ""
    document_length_in_pages: float = 0.5 # The desired length of the document in pages
    outline_granularity: OutlineGranularity = OutlineGranularity.DETAILED
    audience: str = ""
    key_focus_areas: list[str] = []  # Key points to emphasize in the outline
    synopsis: str = ""
    creativity_level: float = 0.7

class ConvertOutlineToDocumentRequest(OutputText):
    document_type: str = ""
    genre: str = ""
    target_audience: str = ""
    outline: list[OutlineSection] = []
    previous_content: list[DocumentSection] = []