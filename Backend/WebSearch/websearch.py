from ddgs import DDGS

class WebSearcher:
    def __init__(self):
        self.ddgs = DDGS()

    async def search_duckduckgo(self, query: str, num_results: int = 5):
        results = []
        for result in self.ddgs.text(query, max_results=num_results):
            results.append({
                    "title": result["title"],
                    "url": result["href"],
                    "snippet": result["body"]
                })
        return results