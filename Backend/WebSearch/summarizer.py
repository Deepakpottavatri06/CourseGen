import os
from typing import List
from fastapi import HTTPException
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
class Summarizer:
    def __init__(self):
        self.client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    
    def get_summary_prompt(self, query: str, contents: List[str], length: str = "medium") -> str:
        """Generate prompt for summarization"""
        length_instructions = {
            "short": "Provide a concise summary in 1 paragraph.",
            "medium": "Provide a comprehensive summary in 1-2 paragraphs.",
            "long": "Provide a detailed summary with key points and examples in 3-4 paragraphs."
        }
        
        combined_content = "\n\n---\n\n".join(contents)
        
        prompt = f"""
        Based on the following web content, provide a {length} summary answering the query: "{query}"

            {length_instructions.get(length, length_instructions["medium"])}

            Requirements:
            - Focus on information directly relevant to the query
            - Synthesize information from multiple sources
            - Highlight key facts, statistics, and important points
            - Maintain accuracy and avoid speculation
            - If sources conflict, mention the different viewpoints

            Content from web sources:
            {combined_content}

            Summary:
            """
        return prompt
    
    async def generate_summary(self, query: str, contents: List[str], length: str = "medium") -> str:
        """Generate summary using OpenAI using gemini model"""
        if not contents:
            return "No content available for summarization."
        
        prompt = self.get_summary_prompt(query, contents, length)
        
        try:
            response =  self.client.chat.completions.create(
                model="gemini-2.0-flash-lite",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates accurate summaries from web content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500 if length == "long" else 800,
                temperature=0.3
            )

            return str(response.choices[0].message.content).strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Summarization error: {str(e)}")
