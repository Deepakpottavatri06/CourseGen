from google import genai
import asyncio
from typing import List, Dict, Optional
import re
from .models import DifficultyLevel, TopicIntroduction, SubTopicContent
from dotenv import load_dotenv
load_dotenv()
class ContentGenerator:
    def __init__(self):

        self.model = genai.Client()
        
    def _get_difficulty_context(self, difficulty: DifficultyLevel) -> dict[str,str]:
        """Get context based on difficulty level"""
        contexts = {
            DifficultyLevel.BEGINNER: {
                "tone": "simple, clear, and accessible",
                "depth": "fundamental concepts with basic explanations",
                "examples": "real-world, relatable examples",
                "length": "detailed but not overwhelming"
            },
            DifficultyLevel.INTERMEDIATE: {
                "tone": "moderately technical with balanced explanations",
                "depth": "comprehensive coverage with some technical details",
                "examples": "practical applications and case studies",
                "length": "thorough and well-structured"
            },
            DifficultyLevel.ADVANCED: {
                "tone": "technical and in-depth",
                "depth": "complex concepts with detailed analysis",
                "examples": "sophisticated examples and research findings",
                "length": "comprehensive and detailed"
            }
        }
        return contexts[difficulty]

    async def generate_topic_introduction(
        self, 
        topic: str, 
        subtopics: List[str], 
        difficulty: DifficultyLevel,
        topic_extracted_content: Dict[str, str],
        subtopic_content_map: Dict[str, Dict[str, str]],
        language: str = "english"
    ) -> TopicIntroduction:
        """Generate comprehensive introduction for the main topic"""
        
        difficulty_context = self._get_difficulty_context(difficulty)
        
        # Combine extracted content for context
        research_context = "\n".join([
            f"Source content: {content[:1000]}..." 
            for content in topic_extracted_content.values() if content
        ])
        
        # provide some context related to subtopics as well
        all_subtopic_content = []
        for subtopic_content in subtopic_content_map.values():
            all_subtopic_content.extend(subtopic_content.values())
        
        if all_subtopic_content:
            research_context += "\nSubtopic source content:\n" + "\n".join([
                f"Source content: {content[:400]}..." 
                for content in all_subtopic_content if content
            ])
        
        prompt = f"""
        Create a comprehensive introduction for the topic "{topic}" at {difficulty.value} level in {language}.
        
        Difficulty Context:
        - Tone: {difficulty_context['tone']}
        - Depth: {difficulty_context['depth']}
        - Examples: {difficulty_context['examples']}
        
        Subtopics to be covered: {', '.join(subtopics)}
        
        Research Context (use as reference):
        {research_context}
        
        Generate content with the following structure:
        1. INTRODUCTION (300-400 words): Engaging introduction explaining what the topic is and why it's important
        2. OVERVIEW (400-500 words): Comprehensive overview covering key concepts and scope
        3. LEARNING_OBJECTIVES (5-7 bullet points): What learners will achieve
        4. PREREQUISITES (3-5 bullet points): What learners should know beforehand
        
        Format your response as:
        INTRODUCTION:
        [introduction content]
        
        OVERVIEW:
        [overview content]
        
        LEARNING_OBJECTIVES:
        • [objective 1]
        • [objective 2]
        ...
        
        PREREQUISITES:
        • [prerequisite 1]
        • [prerequisite 2]
        ...
        
        Make the content educational, engaging, and appropriate for {difficulty.value} level learners.
        Target total length: 800-1000 words.
        For any table creation, use markdown format.
        """
        
        try:
            response = await asyncio.to_thread(
                self.model.models.generate_content,
                 model="gemini-2.5-flash",
                contents = prompt
            )

            content = response.text if response.text else ""

            # Parse the structured response
            sections = self._parse_introduction_sections(content)
            
            # Handle learning objectives with type safety
            value = sections.get('learning_objectives')
            if isinstance(value, list) and all(isinstance(i, str) for i in value):
                learning_objectives = value
            elif isinstance(value, str):
                learning_objectives = [value]
            else:
                learning_objectives = []

            # Handle prerequisites with type safety
            value = sections.get('prerequisites')
            if isinstance(value, list) and all(isinstance(i, str) for i in value):
                prerequisites = value
            elif isinstance(value, str):
                prerequisites = [value]
            else:
                prerequisites = []
            
            return TopicIntroduction(
                topic=topic,
                introduction=sections.get('introduction', ''),
                overview=sections.get('overview', ''),
                learning_objectives=learning_objectives,
                prerequisites=prerequisites,
                word_count=len(content.split())
            )
            
        except Exception as e:
            raise Exception(f"Error generating topic introduction: {str(e)}")


    async def generate_subtopic_content(
        self,
        topic: str,
        subtopic: str,
        difficulty: DifficultyLevel,
        topic_extracted_content: Dict[str, str],
        subtopic_content_map: Dict[str, Dict[str, str]],
        language: str = "english",
    ) -> SubTopicContent:
        """Generate comprehensive content for a subtopic"""
        
        difficulty_context = self._get_difficulty_context(difficulty)
        
        # Get topic context
        relevant_content = "Topic Source Content:\n" + "\n".join([
            f"Source: {content[:500]}..." 
            for content in topic_extracted_content.values() if content
        ])
        
        # Get subtopic-specific content
        subtopic_content = subtopic_content_map.get(subtopic, {})
        if subtopic_content:
            relevant_content += "\nSubtopic Specific Content:\n" + "\n".join([
                f"Source: {content[:1500]}..." 
                for content in subtopic_content.values() if content
            ])
        
        prompt = f"""
        Create comprehensive educational content about "{subtopic}" as part of the main topic "{topic}" 
        at {difficulty.value} level in {language}.
        
        Difficulty Context:
        - Tone: {difficulty_context['tone']}
        - Depth: {difficulty_context['depth']}
        - Examples: {difficulty_context['examples']}
        - Length: {difficulty_context['length']}
        
        Research Context (use as reference):
        {relevant_content}
        
        Create well-structured content that includes:
        1. Clear explanation of the subtopic
        2. Key concepts and definitions
        3. Practical examples and applications
        4. Step-by-step explanations where applicable
        5. Common misconceptions or pitfalls (if relevant)
        6. Connection to the main topic and other subtopics
        
        Requirements:
        - Minimum 800-1200 words (approximately 1 page)
        - Educational and engaging writing style
        - Appropriate for {difficulty.value} level
        - Include practical examples
        - Use clear headings and structure
        - Make it comprehensive yet accessible
        
        Focus on providing value and deep understanding of "{subtopic}" within the context of "{topic}".
        """
        
        try:
            response = await asyncio.to_thread(
                self.model.models.generate_content,
                 model="gemini-2.5-flash",
                contents = prompt
            )

            content = response.text if response.text else ""
            sources = list(subtopic_content.keys()) if subtopic_content else []
            
            return SubTopicContent(
                subtopic=subtopic,
                content=content,
                sources=sources,
                word_count=len(content.split())
            )
            
        except Exception as e:
            raise Exception(f"Error generating content for subtopic '{subtopic}': {str(e)}")

    def _parse_introduction_sections(self, content: str) -> Dict[str, str]:
        """Parse structured introduction content"""
        sections = {}
        
        # Extract introduction
        intro_match = re.search(r'INTRODUCTION:\s*(.*?)(?=OVERVIEW:|$)', content, re.DOTALL | re.IGNORECASE)
        if intro_match:
            sections['introduction'] = intro_match.group(1).strip()
        
        # Extract overview
        overview_match = re.search(r'OVERVIEW:\s*(.*?)(?=LEARNING_OBJECTIVES:|$)', content, re.DOTALL | re.IGNORECASE)
        if overview_match:
            sections['overview'] = overview_match.group(1).strip()
        
        # Extract learning objectives
        objectives_match = re.search(r'LEARNING_OBJECTIVES:\s*(.*?)(?=PREREQUISITES:|$)', content, re.DOTALL | re.IGNORECASE)
        if objectives_match:
            objectives_text = objectives_match.group(1).strip()
            objectives = [
                obj.strip().lstrip('•').lstrip('-').strip() 
                for obj in objectives_text.split('\n') 
                if obj.strip() and not obj.strip().startswith('PREREQUISITES')
            ]
            sections['learning_objectives'] = [obj for obj in objectives if obj]
        
        # Extract prerequisites
        prereq_match = re.search(r'PREREQUISITES:\s*(.*?)$', content, re.DOTALL | re.IGNORECASE)
        if prereq_match:
            prereq_text = prereq_match.group(1).strip()
            prerequisites = [
                prereq.strip().lstrip('•').lstrip('-').strip() 
                for prereq in prereq_text.split('\n') 
                if prereq.strip()
            ]
            sections['prerequisites'] = [prereq for prereq in prerequisites if prereq]
        
        return sections

    async def generate_complete_learning_content(
        self,
        topic: str,
        subtopics: List[str],
        difficulty: DifficultyLevel,
        topic_extracted_content: Dict[str, str],
        subtopic_content_map: Dict[str, Dict[str, str]],
        language: str = "english"
    ) -> tuple[TopicIntroduction, List[SubTopicContent]]:
        """Generate complete learning content for topic and all subtopics"""
        
        # Generate topic introduction
        introduction = await self.generate_topic_introduction(
            topic, subtopics, difficulty, topic_extracted_content, subtopic_content_map, language
        )
        
        # Generate subtopic contents concurrently
        subtopic_tasks = [
            self.generate_subtopic_content(
                topic, subtopic, difficulty, topic_extracted_content, subtopic_content_map, language
            )
            for subtopic in subtopics
        ]
        
        subtopic_contents = await asyncio.gather(*subtopic_tasks)
        
        return introduction, subtopic_contents