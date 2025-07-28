import asyncio
from typing import List, Dict, Optional
from trafilatura import extract, fetch_url
class ContentExtractor:
    def __init__(self):
        # self.client = httpx.AsyncClient(timeout=30.0)
        pass

    async def extract_content(self, url: str) -> Optional[str]:
        """Extract clean content from URL using trafilatura"""
        try:
            response = fetch_url(url)
            if not response:
                return ""
            # Use trafilatura to extract clean content
            content = extract(
                response,
                include_comments=False,
                include_tables=True,
                include_images=False,
                fast=True,
            )
            
            return content
        except Exception as e:
            print(f"Error extracting content from {url}: {str(e)}")
            return None
    
    async def extract_multiple_contents(self, urls: List[str]) -> Dict[str, str]:
        """Extract content from multiple URLs concurrently"""
        tasks = [self.extract_content(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        results = [result[:1000] if isinstance(result, str) else None for result in results]
        content_dict = {}
        for url, result in zip(urls, results):
            if isinstance(result, str) and result:
                content_dict[url] = result
            elif not isinstance(result, Exception):
                content_dict[url] = None
                
        return content_dict