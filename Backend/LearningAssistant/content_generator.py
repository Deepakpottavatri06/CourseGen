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
    
    async def design_course_structure(
        self,
        topic: str,
        user_subtopics: List[str],
        difficulty: DifficultyLevel,
        language: str = "english"
    ) -> List[str]:
        """Design optimal course structure using Gemini"""
        
        difficulty_context = self._get_difficulty_context(difficulty)
        
        prompt = f"""
        You are an expert course designer. Design an optimal learning course structure for the topic "{topic}" at {difficulty.value} level in {language}.
        
        User provided these subtopics: {', '.join(user_subtopics)}
        
        Difficulty Context:
        - Level: {difficulty.value}
        - Tone: {difficulty_context['tone']}
        - Depth: {difficulty_context['depth']}
        
        Your task:
        1. Analyze the user's subtopics
        2. Design a logical, progressive course structure
        3. Ensure subtopics build upon each other
        4. Make them appropriate for {difficulty.value} level learners
        5. Keep the number of subtopics between 3-7 for optimal learning
        
        Requirements:
        - Use clear, descriptive subtopic names
        - Ensure logical learning progression
        - Cover essential concepts for the topic
        - Consider the difficulty level
        - Make subtopics comprehensive but focused
        
        Provide ONLY the subtopic names, one per line, in the optimal learning order.
        Do not include numbers, bullets, or explanations - just the subtopic names.
        
        Example format:
        Introduction to Machine Learning
        Supervised Learning Fundamentals  
        Unsupervised Learning Methods
        Model Evaluation and Validation
        """
        
        try:
            response = await asyncio.to_thread(
                self.model.models.generate_content,
                 model="gemini-2.5-flash",
                contents = prompt
            )
            
            content = response.text if response.text else ""
            
            # Parse subtopics from response
            designed_subtopics = []
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 3:
                    # Remove any numbering or bullets that might have been added
                    clean_line = re.sub(r'^\d+\.?\s*', '', line)
                    clean_line = re.sub(r'^[-•*]\s*', '', clean_line)
                    if clean_line:
                        designed_subtopics.append(clean_line.strip())
            
            # Fallback to user subtopics if design fails
            if not designed_subtopics:
                print("Course design failed, using user provided subtopics")
                return user_subtopics
            
            # Limit to reasonable number
            if len(designed_subtopics) > 8:
                designed_subtopics = designed_subtopics[:8]
            
            print(f"Course designed: {len(designed_subtopics)} subtopics")
            return designed_subtopics
            
        except Exception as e:
            print(f"Error in course design: {str(e)}, falling back to user subtopics")
            return user_subtopics
        
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
            
            print(f"Introduction generated successfully for topic '{topic}'")
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
        learning_objectives: List[str] | None,
        language: str = "english",
    ) -> SubTopicContent:
        """Generate comprehensive content for a subtopic with learning objectives context"""
        
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
        
        # Add learning objectives context
        objectives_context = ""
        if learning_objectives:
            objectives_context = f"""
        
        Course Learning Objectives (ensure your content aligns with these):
        {chr(10).join([f"• {obj}" for obj in learning_objectives])}
        """
        
        prompt = f"""
        Create comprehensive educational content about "{subtopic}" as part of the main topic "{topic}" 
        at {difficulty.value} level in {language}.
        
        Difficulty Context:
        - Tone: {difficulty_context['tone']}
        - Depth: {difficulty_context['depth']}
        - Examples: {difficulty_context['examples']}
        - Length: {difficulty_context['length']}
        {objectives_context}
        
        Research Context (use as reference):
        {relevant_content}
        
        IMPORTANT FORMATTING REQUIREMENTS:
        - Use proper Markdown formatting throughout
        - Include clear headings (# ## ###) to structure content
        - Add proper line breaks between sections and paragraphs
        - Use bullet points (-) or numbered lists (1.) where appropriate
        - Format code examples using ```language code blocks
        - Create tables using Markdown table syntax (| | |)
        - Use **bold** and *italic* text for emphasis
        - Ensure proper spacing and readability
        - Structure content with clear sections and subsections
        
        Create well-structured content that includes:
        1. Clear explanation of the subtopic (use headings)
        2. Key concepts and definitions (use subheadings and formatting)
        3. Practical examples and applications (use code blocks if applicable)
        4. Step-by-step explanations where applicable (use numbered lists)
        5. Common misconceptions or pitfalls (use bullet points)
        6. Connection to the main topic and other subtopics
        7. How this subtopic contributes to achieving the overall learning objectives
        
        Content Structure Example:
        # Subtopic Title
        
        Brief introduction paragraph.
        
        ## Key Concepts
        
        Explanation with proper paragraphs.
        
        ### Important Definition
        
        **Term**: Definition here.
        
        ## Practical Examples
        
        Example explanation.
        
        ```python
        # Code example if applicable
        example_code = "formatted properly"
        ```
        
        ## Applications
        
        - Application 1
        - Application 2
        
        | Feature | Description |
        |---------|-------------|
        | Item 1  | Details     |
        
        Requirements:
        - Minimum 600-700 words (approximately 1 page)
        - Educational and engaging writing style
        - Appropriate for {difficulty.value} level
        - Include practical examples with proper formatting
        - Use clear Markdown headings and structure
        - Make it comprehensive yet accessible
        - Align content with the course learning objectives
        - MUST include proper line breaks and formatting for frontend display
        
        Focus on providing value and deep understanding of "{subtopic}" within the context of "{topic}".
        Ensure the content helps learners progress toward the overall course objectives.
        Use proper Markdown formatting to ensure excellent readability and frontend compatibility.
        """
        
        try:
            response = await asyncio.to_thread(
                self.model.models.generate_content,
                 model="gemini-2.5-flash",
                contents = prompt
            )

            content = response.text if response.text else ""
            sources = list(subtopic_content.keys()) if subtopic_content else []
            print(f"Subtopic content generated successfully for subtopic '{subtopic}'")
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
        
        # Step 1: Generate topic introduction first
        introduction = await self.generate_topic_introduction(
            topic, subtopics, difficulty, topic_extracted_content, subtopic_content_map, language
        )
        
        # Step 2: Generate subtopic contents with learning objectives context
        # Note: Making this sequential to use learning objectives from introduction
        subtopic_contents = []
        for subtopic in subtopics:
            subtopic_content = await self.generate_subtopic_content(
                topic, 
                subtopic, 
                difficulty, 
                topic_extracted_content, 
                subtopic_content_map, 
                introduction.learning_objectives,  # Pass learning objectives
                language
            )
            subtopic_contents.append(subtopic_content)
        
        # Return both introduction and subtopic contents
        print(f"Subtopic contents generated successfully for topic '{topic}'")
        return introduction, subtopic_contents