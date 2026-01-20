from typing import List, Dict, Tuple
import asyncio
from .content_generator import ContentGenerator
from WebSearch.content_extractor import ContentExtractor
from WebSearch.websearch import WebSearcher
from .models import LearningRequest, LearningResponse, TopicIntroduction, SubTopicContent

class LearningService:
    def __init__(self, content_generator: ContentGenerator, web_searcher:WebSearcher, content_extractor:ContentExtractor):
        self.content_generator = content_generator
        self.web_searcher = web_searcher
        self.content_extractor = content_extractor

    async def create_learning_content(self, request: LearningRequest) -> LearningResponse:
        """Main service method to create comprehensive learning content"""
        
        
        try:
            # Step 0: course design logic
            # If subtopics are less than or equal to 6, design course structure
            final_subtopics = request.sub_topics
            course_designed = False
            # if len(request.sub_topics) <= 6: # 
            print(f"Designing course structure for {len(request.sub_topics)} subtopics...")
            try:
                designed_subtopics = await self.content_generator.design_course_structure(
                    topic=request.topic,
                    user_subtopics=request.sub_topics,
                    difficulty=request.difficulty,
                    language=request.language if request.language else "english"
                )
                final_subtopics = designed_subtopics
                print(f"Designed subtopics: {final_subtopics}")
                course_designed = True
                print(f"Course design completed. Using {len(final_subtopics)} designed subtopics.")
            except Exception as e:
                print(f"Course design failed: {str(e)}. Using original subtopics.")
                final_subtopics = request.sub_topics
            # else:
            #     print(f"Skipping course design for {len(request.sub_topics)} subtopics (>6) to reduce costs.")
            
            # Step 1: Search for relevant content
            topic_queries, subtopic_queries_map = self._generate_search_queries(request.topic, final_subtopics)
            topic_extracted_content, subtopic_content_map = await self._search_and_extract_content(topic_queries, subtopic_queries_map)

            print(f"Topic content extracted successfully for topic '{request.topic}'")


            # Step 2: Generate learning content
            introduction, subtopic_contents = await self.content_generator.generate_complete_learning_content(
                topic=request.topic,
                subtopics=final_subtopics,
                difficulty=request.difficulty,
                topic_extracted_content=topic_extracted_content,
                subtopic_content_map=subtopic_content_map,
                language= request.language if request.language else "english"
            )
            
            # Step 3: Calculate metrics
            total_word_count = introduction.word_count + sum(sc.word_count for sc in subtopic_contents)
            estimated_reading_time = max(1, total_word_count // 200)  # ~200 words per minute
            
            print(f"Successfully generated learning content for topic '{request.topic}'")
            return LearningResponse(
                topic=request.topic,
                sub_topics=final_subtopics,
                difficulty=request.difficulty,
                introduction=introduction,
                subtopic_contents=subtopic_contents,
                total_word_count=total_word_count,
                estimated_reading_time=estimated_reading_time,
                course_designed=course_designed
            )
            
        except Exception as e:
            raise Exception(f"Error creating learning content: {str(e)}")

    def _generate_search_queries(self, topic: str, subtopics: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
        """Generate comprehensive search queries with proper subtopic mapping"""
        
        # Main topic queries
        topic_queries = [
            f"{topic} comprehensive guide",
            f"{topic} explanation ",
            f"what is {topic} definition"
        ]
        
        # Subtopic queries mapped by subtopic name
        subtopic_queries_map = {}
        for subtopic in subtopics:
            subtopic_queries_map[subtopic] = [
                f"{topic} {subtopic} explanation ",
                f"learn {subtopic} {topic}",
                f"{topic} {subtopic} guide"
            ]
        
        return topic_queries, subtopic_queries_map

    async def _search_and_extract_content(
        self, 
        topic_queries: List[str], 
        subtopic_queries_map: Dict[str, List[str]]
    ) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
        """Search web and extract content with robust subtopic mapping"""
        
        # Step 1: Extract topic content
        topic_urls = set()
        for query in topic_queries:
            try:
                search_results = await self.web_searcher.search_duckduckgo(query, num_results=3)
                for result in search_results:
                    topic_urls.add(result['url'])
            except Exception as e:
                print(f"Search error for topic query '{query}': {str(e)}")
                continue
        
        # Extract topic content
        topic_extracted_content = await self.content_extractor.extract_multiple_contents(list(topic_urls))
        topic_dict = {url: content for url, content in topic_extracted_content.items() if content}
        
        # Step 2: Extract subtopic content with proper mapping
        subtopic_content_map = {}
        
        # Process each subtopic separately to maintain mapping
        for subtopic, queries in subtopic_queries_map.items():
            subtopic_urls = set()
            
            # Search for this specific subtopic
            for query in queries:
                try:
                    search_results = await self.web_searcher.search_duckduckgo(query, num_results=3)
                    for result in search_results:
                        subtopic_urls.add(result['url'])
                except Exception as e:
                    print(f"Search error for subtopic '{subtopic}' query '{query}': {str(e)}")
                    continue
            
            # Extract content for this subtopic
            if subtopic_urls:
                # Limit URLs per subtopic to prevent overload
                limited_urls = list(subtopic_urls)[:12]  # Max 12 URLs per subtopic
                subtopic_extracted = await self.content_extractor.extract_multiple_contents(limited_urls)
                
                # Store only non-empty content for this subtopic
                subtopic_content_map[subtopic] = {
                    url: content for url, content in subtopic_extracted.items() if content
                }
            else:
                # Ensure every subtopic has an entry (even if empty)
                subtopic_content_map[subtopic] = {}
        
        return topic_dict, subtopic_content_map
    
    