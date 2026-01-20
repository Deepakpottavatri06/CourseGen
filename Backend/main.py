from pydantic import Field
from fastapi import FastAPI, HTTPException , BackgroundTasks
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from WebSearch.websearch import WebSearcher
from WebSearch.content_extractor import ContentExtractor
from WebSearch.summarizer import Summarizer
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from middleware.auth import authorise
from profanity_detection import is_profane
from api.login_register import app as login_register_app
from LearningAssistant.models import LearningRequest
from LearningAssistant.content_generator import ContentGenerator
from LearningAssistant.learning_service import LearningService
from model.db_connect import db
from bson import ObjectId
# Global variables for services
learning_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global learning_service
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    # Initialize services
    content_generator = ContentGenerator()
    web_searcher = WebSearcher()  # Your existing class
    content_extractor = ContentExtractor()  # Your existing class
    
    learning_service = LearningService(
        content_generator=content_generator,
        web_searcher=web_searcher,
        content_extractor=content_extractor
    )
    
    yield
    
    # Shutdown
    learning_service = None


app = FastAPI(title="CourseGen , AI Assistant", version="1.0.0", lifespan=lifespan)

origins = [
   "*",  # Allow all origins for development; restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models



# Initialize services
# searcher = WebSearcher()
# extractor = ContentExtractor()
# summarizer = Summarizer()


app.include_router(login_register_app, prefix="/api", tags=["Authentication"])


def serialize_mongo_document(doc):
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc


@app.get("/api/course-content/{content_id}")
async def get_course_content(content_id: str, payload: dict = Depends(authorise)):
    """Get course content by ID"""
    try:
        content = await db['course_content'].find_one({"_id": ObjectId(content_id)})
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        return JSONResponse(content=serialize_mongo_document(content), status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def generate_learning_background(request: LearningRequest , payload:dict):
    """Background task to generate learning content"""
    try:
        if not learning_service:
            raise HTTPException(status_code=500, detail="Learning service not initialized")

        response = await learning_service.create_learning_content(request)
        content = db['course_content'].find_one_and_update({"_id": ObjectId(payload["content_id"])},{
            "$set": {
                "content_loaded": True,
                **response.model_dump(),
            }
        })
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MarkReadPayload(BaseModel):
    sub_topic: str = Field(..., description="The name of the sub-topic to mark as read")

@app.get("/api/course-content")
async def get_all_course_content(payload: dict = Depends(authorise)):
    """Get all course content for the authenticated user"""
    try:
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Could not validate user credentials")

        contents = await db['course_content'].find({"user_id": ObjectId(user_id)},
                                                   projection={"_id": 1, "topic": 1, "sub_topics": 1, "estimated_reading_time": 1, "difficulty": 1}).to_list(length=None)
        serialized_contents = [serialize_mongo_document(content) for content in contents]

        return JSONResponse(content=serialized_contents, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/course-content/{content_id}/read")
async def mark_course_content_as_read(req_body: MarkReadPayload, content_id: str, payload: dict = Depends(authorise)):
    """Mark course content as read"""
    try:
        sub_topic = req_body.sub_topic

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Could not validate user credentials")

        result = await db['course_content'].update_one(
            {
                "_id": ObjectId(content_id),
                "user_id": ObjectId(user_id)
            },
            {
                "$set": {"subtopic_contents.$[elem].read": True}
            },
            array_filters=[{"elem.subtopic": req_body.sub_topic}] # Access sub_topic from the validated payload
        )

        # if result.modified_count == 0:
        #     # This could mean the parent doc wasn't found OR the sub_topic wasn't found within it.
        #     # A good practice is to check if the document exists first for a more precise error.
        #     raise HTTPException(
        #         status_code=404,
        #         detail=f"Content with ID '{content_id}' and sub-topic '{req_body.sub_topic}' not found for this user."
        #     )

        return {"message": f"Sub-topic '{req_body.sub_topic}' marked as read."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-learning-content")
async def generate_learning_content(request:  LearningRequest, background_tasks: BackgroundTasks, payload: dict = Depends(authorise)):
    """
    Generate comprehensive learning content for a given topic and subtopics
    """
    try:
        if not learning_service:
            raise HTTPException(status_code=500, detail="Learning service not initialized")
        
        # Validate request
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        if not request.sub_topics or len(request.sub_topics) == 0:
            raise HTTPException(status_code=400, detail="At least one subtopic is required")
        
        if len(request.sub_topics) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 subtopics allowed")
        
        # Generate content
        # response = await learning_service.create_learning_content(request)
        content = await db['course_content'].insert_one({
            "user_id": ObjectId(payload.get("user_id")),
            "topic": request.topic,
            "sub_topics": request.sub_topics,
            "content_loaded":False,
        })
        payload["content_id"] = str(content.inserted_id)
        background_tasks.add_task(generate_learning_background, request, payload)
        return JSONResponse(
            content={"message": "Learning content generation started in the background. You can check the status later." , 
                     "content_id": payload["content_id"]},
            status_code=202
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Learning Assistant"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Learning Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "generate_content": "/generate-learning-content",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)