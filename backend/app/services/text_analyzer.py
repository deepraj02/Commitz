import re
import logging
from collections import Counter
import hashlib
import random
from typing import List, Dict, Tuple, Set

logger = logging.getLogger(__name__)

class TextAnalyzer:
    """
    A utility class to quickly extract topics and patterns from 
    transcripts when the Gemini API is unavailable or too slow
    """
    
    def __init__(self):
        self.programming_terms = [
            "function", "class", "method", "variable", "const", "let", "var", "import", 
            "require", "from", "install", "npm", "pip", "setup", "configure", "API", 
            "REST", "database", "SQL", "query", "server", "client", "component", 
            "initialize", "deploy", "test", "debug", "event", "handler", "callback",
            "async", "await", "promise", "then", "catch", "try", "except", "error",
            "exception", "framework", "library", "package", "module", "dependency",
            "interface", "type", "model", "schema", "migration", "endpoint", "route",
            "controller", "view", "template", "render", "style", "css", "html", "jsx",
            "component", "hook", "state", "props", "effect", "lifecycle", "render"
        ]
        
        self.common_tools = [
            "React", "Angular", "Vue", "Node", "Express", "Django", "Flask", "Spring",
            "Laravel", "Rails", "Next.js", "Gatsby", "Webpack", "Babel", "TypeScript",
            "JavaScript", "Python", "Java", "C#", "Go", "Rust", "PHP", "Ruby", "Swift",
            "Kotlin", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Firebase",
            "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch", "GraphQL",
            "REST", "Swagger", "OpenAPI", "Jest", "Mocha", "Cypress", "Selenium",
            "Jenkins", "Travis", "CircleCI", "GitHub Actions", "Git", "npm", "yarn",
            "pip", "conda", "Maven", "Gradle", "Composer", "Homebrew", "apt", "yum"
        ]
        
    def extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from markdown-formatted text"""
        # Match code blocks with triple backticks
        triple_backtick_pattern = r'```(?:\w+)?\n([\s\S]*?)\n```'
        triple_backtick_blocks = re.findall(triple_backtick_pattern, text)
        
        # Match inline code with single backticks
        single_backtick_pattern = r'`([^`]+)`'
        single_backtick_blocks = re.findall(single_backtick_pattern, text)
        
        # Match indented code blocks (4 spaces or tab)
        indented_pattern = r'(?:^|\n)(?:    |\t)(.+)(?:\n|$)'
        indented_blocks = re.findall(indented_pattern, text)
        
        all_blocks = triple_backtick_blocks + single_backtick_blocks + indented_blocks
        return [block for block in all_blocks if len(block.strip()) > 10]  # Filter out tiny blocks
        
    def extract_tech_terms(self, text: str) -> List[Tuple[str, int]]:
        """Extract technology terms and their frequency"""
        words = re.findall(r'\b\w+\b', text.lower())
        tech_terms = []
        
        # Count occurrences of programming terms
        term_counter = Counter()
        for term in self.programming_terms:
            count = text.lower().count(term.lower())
            if count > 0:
                term_counter[term] = count
                
        # Count occurrences of tool names (case sensitive)
        for tool in self.common_tools:
            # Use word boundary for more accurate matching
            pattern = r'\b' + re.escape(tool) + r'\b'
            matches = re.findall(pattern, text)
            count = len(matches)
            if count > 0:
                term_counter[tool] = count
        
        # Return terms sorted by frequency
        return term_counter.most_common(20)
        
    def extract_potential_topics(self, text: str) -> List[str]:
        """Extract potential topics from text"""
        # Split into sentences
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        topics = []
        tech_terms = self.extract_tech_terms(text)
        term_list = [term[0] for term in tech_terms]
        
        # Find sentences containing tech terms
        for sentence in sentences:
            if any(term.lower() in sentence.lower() for term in term_list):
                # Clean up and shorten for title
                title = sentence[:50].strip() + "..." if len(sentence) > 50 else sentence
                topics.append(title)
                
                # Only take up to 10 topics
                if len(topics) >= 10:
                    break
        
        return topics
    
    def generate_emergency_issues(self, transcript: str, min_issues: int = 3) -> Dict[str, dict]:
        """Generate basic issues when the main API fails"""
        logger.info("Generating emergency issues from transcript")
        
        try:
            unique_issues = {}
            
            # Extract code examples
            code_blocks = self.extract_code_blocks(transcript)
            
            # Extract important tech terms
            tech_terms = self.extract_tech_terms(transcript)
            
            # Extract potential topics
            topics = self.extract_potential_topics(transcript)
            
            # Create issues from code examples
            for i, code in enumerate(code_blocks[:min(len(code_blocks), 2)]):
                title = f"Implement code example {i+1}"
                code_snippet = code[:200] + "..." if len(code) > 200 else code
                unique_issues[title] = {
                    "title": title,
                    "description": f"## Code Implementation\n```\n{code_snippet}\n```\n\nImplement this code example from the tutorial.",
                    "difficulty": "intermediate",
                    "labels": ["code-example", "implementation"],
                    "learning_objectives": ["Understand and implement this code pattern"],
                    "implementation_steps": ["1. Study the code structure", "2. Implement it in your project"]
                }
            
            # Create issues from tech terms
            for term, count in tech_terms[:min(len(tech_terms), 3)]:
                title = f"Learn about {term}"
                unique_issues[title] = {
                    "title": title,
                    "description": f"## Understanding {term}\nLearn how to use {term} as shown in the tutorial.",
                    "difficulty": "beginner",
                    "labels": ["concept", "learning"],
                    "learning_objectives": [f"Understand what {term} is", f"Learn how to use {term} effectively"],
                    "implementation_steps": [f"1. Research {term}", f"2. Practice using {term} in examples"]
                }
            
            # Create issues from topics
            for topic in topics[:min(len(topics), 3)]:
                # Get a stable hash for this topic to ensure consistent titles
                topic_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
                title = f"Implement: {topic[:30]}..." if len(topic) > 30 else f"Implement: {topic}"
                unique_issues[topic_hash] = {
                    "title": title,
                    "description": f"## Topic Implementation\n{topic}\n\nImplement this concept from the tutorial.",
                    "difficulty": "intermediate",
                    "labels": ["topic", "implementation"],
                    "learning_objectives": ["Understand this concept", "Implement it in practice"],
                    "implementation_steps": ["1. Study the concept", "2. Apply it in your project"]
                }
            
            # If we don't have enough issues, create generic ones
            if len(unique_issues) < min_issues:
                generic_topics = [
                    "Setup the development environment",
                    "Understand the project structure",
                    "Implement core functionality",
                    "Test your implementation",
                    "Deploy the application"
                ]
                
                for i, topic in enumerate(generic_topics):
                    if len(unique_issues) >= min_issues:
                        break
                    if topic not in unique_issues:
                        unique_issues[topic] = {
                            "title": topic,
                            "description": f"## {topic}\nFollow the tutorial to {topic.lower()}.",
                            "difficulty": "beginner",
                            "labels": ["setup", "implementation"],
                            "learning_objectives": [f"Learn how to {topic.lower()}"],
                            "implementation_steps": ["1. Follow the tutorial steps", "2. Apply to your project"]
                        }
            
            return unique_issues
            
        except Exception as e:
            logger.error(f"Error generating emergency issues: {str(e)}")
            # Return basic fallback issues
            return {
                "follow-tutorial": {
                    "title": "Follow the tutorial steps",
                    "description": "## Tutorial Implementation\nFollow along with the steps in the video tutorial.",
                    "difficulty": "beginner",
                    "labels": ["tutorial"],
                    "learning_objectives": ["Complete the tutorial successfully"],
                    "implementation_steps": ["1. Watch the complete tutorial", "2. Follow each step as shown"]
                },
                "practice-coding": {
                    "title": "Practice coding the examples",
                    "description": "## Practice\nRecreate the code examples shown in the tutorial for practice.",
                    "difficulty": "intermediate",
                    "labels": ["practice", "coding"],
                    "learning_objectives": ["Improve coding skills", "Master the concepts presented"],
                    "implementation_steps": ["1. Create a new project", "2. Try to code the examples without looking"]
                },
                "research-concepts": {
                    "title": "Research the main concepts",
                    "description": "## Research\nDeepen your understanding by researching the main concepts.",
                    "difficulty": "beginner",
                    "labels": ["research", "learning"],
                    "learning_objectives": ["Understand the theoretical foundations"],
                    "implementation_steps": ["1. Identify key concepts", "2. Research them further online"]
                }
            }

    def extract_implementation_steps(self, transcript: str) -> List[str]:
        """Extract potential implementation steps from transcript"""
        # Look for numbered steps or instructions
        step_patterns = [
            r'(?:^|\n)(?:\d+\.\s+)(.+?)(?=(?:\n\d+\.|$))',  # Numbered steps
            r'(?:^|\n)(?:Step \d+:?\s+)(.+?)(?=\n|$)',      # "Step X:" format
            r'(?:First|Second|Third|Fourth|Fifth|Next|Finally)[,:]?\s+(.+?)(?=\n|$)',  # Ordinal instructions
            r'(?:^|\n)(?:-\s+)(.+?)(?=(?:\n-\s+|$))',       # Bullet points
            r'(?:let\'s|we need to|we\'ll|you need to|you\'ll)\s+(\w+\s+.+?)(?=\.|$)'  # Action phrases
        ]
        
        all_steps = []
        for pattern in step_patterns:
            matches = re.findall(pattern, transcript, re.MULTILINE)
            all_steps.extend([m.strip() for m in matches if len(m.strip()) > 10])
            
        # Look specifically for code-related actions
        code_actions = [
            r'(?:create|write|add|define|implement|initialize|install|configure|set up|import)\s+(?:a|an|the)?\s+(.+?)(?=\.|$)',
            r'(?:run|execute|type)\s+(?:the|this|following)?\s+(?:command|code|script):\s*`?([^`\n]+)`?'
        ]
        
        for pattern in code_actions:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            clean_matches = []
            for m in matches:
                if isinstance(m, tuple):  # Some patterns might return tuples
                    clean_matches.extend(m)
                else:
                    clean_matches.append(m)
            all_steps.extend([m.strip() for m in clean_matches if len(m.strip()) > 5])
            
        # Deduplicate and limit to 15 steps
        unique_steps = []
        for step in all_steps:
            if step not in unique_steps:
                unique_steps.append(step)
                if len(unique_steps) >= 15:
                    break
                    
        return unique_steps

    def quick_analyze_transcript(self, transcript: str, min_issues: int = 5) -> Dict[str, dict]:
        """Do a quick analysis of the transcript and generate practical implementation issues"""
        logger.info("Performing quick transcript analysis for practical tasks")
        issues = {}
        
        # Extract code blocks
        code_blocks = self.extract_code_blocks(transcript)[:4]
        
        # Extract implementation steps
        implementation_steps = self.extract_implementation_steps(transcript)
        
        # Extract any file paths or file operations mentioned
        file_patterns = [
            r'(?:create|open|edit|modify|save)\s+(?:file|the file)?\s+[\'"`]?([\w\-./]+\.\w+)[\'"`]?',
            r'(?:in|to|from)\s+(?:file|the file)?\s+[\'"`]?([\w\-./]+\.\w+)[\'"`]?',
            r'[\'"`]([\w\-./]+\.\w+)[\'"`]'
        ]
        
        files_mentioned = []
        for pattern in file_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            files_mentioned.extend([m for m in matches if '.' in m and len(m) > 3])
            
        files_mentioned = list(set(files_mentioned))[:5]  # Deduplicate and limit
        
        # Create a "Project Setup" issue
        if implementation_steps:
            setup_steps = [step for step in implementation_steps if any(term in step.lower() for term in 
                          ["install", "setup", "create", "init", "start", "download", "clone", "config"])]
            
            if setup_steps:
                issues["project_setup"] = {
                    "title": "Set up the project environment",
                    "description": "## Project Setup\nPrepare your development environment as shown in the tutorial.\n\n## Implementation Steps\n" + 
                                "\n".join([f"1. {step}" for step in setup_steps[:5]]),
                    "difficulty": "beginner",
                    "labels": ["setup", "implementation"],
                    "learning_objectives": ["Set up a working development environment", "Prepare for implementation"]
                }
        
        # Create issues from code blocks
        for i, code in enumerate(code_blocks):
            # Try to determine what this code does
            code_purpose = "component" if "class" in code or "function" in code or "def " in code else "feature"
            code_lang = ""
            
            # Try to identify language
            if "import " in code and "from " in code and "def " in code:
                code_lang = "Python"
            elif "function" in code or "const " in code or "let " in code or "var " in code:
                code_lang = "JavaScript"
            elif "public class" in code or "void " in code:
                code_lang = "Java"
            
            title = f"Implement the {code_lang} {code_purpose} from the tutorial"
            if not code_lang:
                title = f"Implement code example {i+1} from the tutorial"
                
            issues[f"code_{i}"] = {
                "title": title,
                "description": f"## Implementation Task\nWrite the following code as shown in the tutorial:\n\n```\n{code[:250]}...\n```\n\n## Purpose\nThis code implements functionality demonstrated in the video.",
                "difficulty": "intermediate",
                "labels": ["coding", "implementation"],
                "learning_objectives": ["Implement this exact code as shown in the tutorial", "Understand how it works"],
                "implementation_steps": [
                    "1. Create the necessary file structure",
                    "2. Write the code exactly as shown in the video",
                    "3. Test the implementation as demonstrated"
                ]
            }

        # Create file-based issues
        for i, file in enumerate(files_mentioned):
            issues[f"file_{i}"] = {
                "title": f"Create and implement the {file} file",
                "description": f"## File Implementation\nCreate and implement the `{file}` file as shown in the tutorial.\n\n## File Purpose\nThis file is part of the project structure demonstrated in the video.",
                "difficulty": "intermediate",
                "labels": ["implementation", "file-structure"],
                "learning_objectives": ["Create this file with the correct implementation", "Understand its role in the project"],
                "implementation_steps": [
                    f"1. Create the {file} file in the correct location",
                    "2. Implement the content as shown in the video",
                    "3. Verify it works correctly within the project"
                ]
            }
            
        # Create implementation step-based issues
        remaining_steps = [s for s in implementation_steps if not any(term in s.lower() for term in 
                          ["install", "setup", "create", "init", "start", "download", "clone", "config"])]
        
        # Group similar steps
        grouped_steps = {}
        for step in remaining_steps:
            key_words = set()
            for word in step.lower().split():
                if len(word) > 4 and word not in ["should", "would", "could", "this", "that", "there", "these", "those"]:
                    key_words.add(word)
            
            key = frozenset(key_words)
            if key not in grouped_steps:
                grouped_steps[key] = []
            grouped_steps[key].append(step)
            
        # Create issues for each group
        for i, (key, steps) in enumerate(list(grouped_steps.items())[:3]):
            if steps:
                main_step = steps[0]
                action_words = ["implement", "create", "build", "develop", "write"]
                title_start = next((word for word in action_words if word in main_step.lower()), "Implement")
                title_words = main_step.split()
                title = f"{title_start.capitalize()} {' '.join(title_words[:5])}..."
                
                issues[f"task_{i}"] = {
                    "title": title,
                    "description": f"## Implementation Task\nComplete this specific task from the tutorial:\n\n> {main_step}\n\n## Details\nThis is a key implementation step shown in the video.",
                    "difficulty": "intermediate",
                    "labels": ["implementation", "task"],
                    "learning_objectives": ["Complete this specific implementation task", "Understand how it fits into the project"],
                    "implementation_steps": [f"1. {step}" for step in steps[:5]]
                }
        
        # Add a comprehensive project issue
        issues["complete_project"] = {
            "title": "Build the complete project from the tutorial",
            "description": "## Complete Project\nImplement the entire project as demonstrated in the tutorial, following all steps in sequence.\n\n## Project Overview\nThis is the culmination of all individual tasks from the video.",
            "difficulty": "advanced",
            "labels": ["project", "implementation"],
            "learning_objectives": ["Build a fully functioning version of the project", "Apply all concepts demonstrated in the tutorial"],
            "implementation_steps": ["1. Complete all prerequisite tasks in order", "2. Integrate all components", "3. Test the full implementation"]
        }
        
        return issues