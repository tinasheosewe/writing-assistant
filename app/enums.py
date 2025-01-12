from enum import Enum

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