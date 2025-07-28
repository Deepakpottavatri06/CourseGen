from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from WebSearch.websearch import WebSearcher
from WebSearch.content_extractor import ContentExtractor
from WebSearch.summarizer import Summarizer
from datetime import datetime

from openai import OpenAI
from ddgs import DDGS

from profanity_detection import is_profane


app = FastAPI(title="Web Search Summarizer", version="1.0.0")

# Models
class SearchRequest(BaseModel):
    query: str
    max_results: int = 5
    summary_length: str = "medium"  # short, medium, long

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    content: Optional[str] = None
    content_length: Optional[int] = None

class SummaryResponse(BaseModel):
    query: str
    summary: str
    sources: List[SearchResult]
    processing_time: float
    total_content_chars: int


# Initialize services
searcher = WebSearcher()
extractor = ContentExtractor()
summarizer = Summarizer()

@app.post("/search-summarize", response_model=SummaryResponse)
async def search_and_summarize(request: SearchRequest):
    """Main endpoint: search web and generate summary"""
    start_time = datetime.now()
    
    try:
        # Step 0: Check if query is profane
        if is_profane(request.query):
            return JSONResponse(status_code=400 , content={"detail": "Inappropriate query detected. Please rephrase your query."})

        # Step 1: Search the web
        print(f"Searching for: {request.query}")
        # search_results = await searcher.search_serpapi(request.query, request.max_results)
        search_results = await searcher.search_duckduckgo(request.query, request.max_results)
        
        if not search_results:
            raise HTTPException(status_code=404, detail="No search results found")
        
        # Step 2: Extract content from URLs
        print("Extracting content from URLs...")
        urls = [result["url"] for result in search_results]
        contents = await extractor.extract_multiple_contents(urls)
        
        # Step 3: Prepare data for summarization
        valid_contents = []
        processed_results = []
        
        for result in search_results:
            url = result["url"]
            content = contents.get(url)
            
            search_result = SearchResult(
                title=result["title"],
                url=url,
                snippet=result["snippet"],
                content=content,
                content_length=len(content) if content else 0
            )
            processed_results.append(search_result)
            
            if content:
                valid_contents.append(content)
        
        # Step 4: Generate summary
        print("Generating summary...")
        summary = await summarizer.generate_summary(
            request.query, 
            valid_contents, 
            request.summary_length
        )
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        total_chars = sum(len(content) for content in valid_contents)
        # print(summary)
        return SummaryResponse(
            query=request.query,
            summary=summary,
            sources=processed_results,
            processing_time=processing_time,
            total_content_chars=total_chars
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/")
async def root():
    return {
        "message": "Web Search Summarizer API",
        "endpoints": {
            "search": "POST /search-summarize",
            "health": "GET /health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)