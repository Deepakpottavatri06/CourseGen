# models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class LearningRequest(BaseModel):
    topic: str = Field(..., description="Main topic to learn about")
    sub_topics: List[str] = Field(..., description="List of subtopics to cover")
    difficulty: DifficultyLevel = Field(..., description="Learning difficulty level")
    language: Optional[str] = Field(default="english", description="Content language")

class SubTopicContent(BaseModel):
    subtopic: str
    content: str
    sources: List[str] = Field(default_factory=list)
    word_count: int
    read : bool = Field(default=False, description="Whether the subtopic content has been read")

class TopicIntroduction(BaseModel):
    topic: str
    introduction: str
    overview: str
    learning_objectives: List[str]
    prerequisites: List[str]
    word_count: int

class LearningResponse(BaseModel):
    topic: str
    difficulty: DifficultyLevel
    introduction: TopicIntroduction
    subtopic_contents: List[SubTopicContent]
    total_word_count: int
    estimated_reading_time: int  # in minutes
    course_designed: bool = Field(default=False, description="Whether course structure was designed by AI")


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

