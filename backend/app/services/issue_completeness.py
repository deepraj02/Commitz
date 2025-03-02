import logging
from typing import List, Dict, Set, Optional, Any
import re
import json
import asyncio
from collections import Counter

logger = logging.getLogger(__name__)

class IssueCompletenessService:
    """
    Service to ensure comprehensive coverage of all technical topics in a transcript,
    enhancing user trust by maximizing issue extraction.
    """
    
    def __init__(self):
        self.technical_indicators = {
            # Programming languages
            "javascript": ["js", "javascript", "node", "npm", "yarn", "react", "vue", "angular", "express"],
            "python": ["python", "pip", "django", "flask", "pandas", "numpy", "tensorflow", "pytorch"],
            "java": ["java", "spring", "maven", "gradle", "jvm", "kotlin"],
            "csharp": ["c#", "csharp", ".net", "asp.net", "entity framework", "xamarin"],
            
            # Web development
            "frontend": ["html", "css", "dom", "browser", "responsive", "sass", "scss", "ui", "ux", "figma", "design"],
            "backend": ["server", "api", "rest", "endpoint", "graphql", "database", "authentication", "authorization"],
            
            # DevOps & Infrastructure
            "devops": ["ci", "cd", "pipeline", "jenkins", "github actions", "gitlab", "travis"],
            "cloud": ["aws", "azure", "gcp", "s3", "ec2", "lambda", "serverless", "cloud"],
            "containers": ["docker", "kubernetes", "container", "k8s", "pod", "deployment"],
            
            # Data & Databases
            "database": ["sql", "nosql", "mongodb", "postgres", "mysql", "redis", "orm", "query"],
            "data_science": ["ml", "machine learning", "data science", "big data", "analytics"],
            
            # Mobile & Desktop
            "mobile": ["android", "ios", "flutter", "react native", "swift", "kotlin", "mobile"],
            "desktop": ["electron", "gtk", "qt", "desktop", "gui"],
            
            # Testing & Architecture
            "testing": ["test", "tdd", "unit", "integration", "e2e", "mockito", "jest", "cypress"],
            "architecture": ["architecture", "pattern", "mvc", "mvvm", "design pattern", "solid"]
        }
        
    def analyze_topic_coverage(self, transcript: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the transcript and issues to determine topic coverage
        
        Args:
            transcript: The video transcript
            issues: List of generated issues
            
        Returns:
            Dictionary with coverage analysis and suggested additional topics
        """
        # Identify technical topics in transcript
        transcript_topics = self._extract_technical_topics(transcript)
        
        # Identify topics covered in issues
        issues_topics = self._extract_issues_topics(issues)
        
        # Find gaps in coverage
        missing_topics = self._identify_missing_topics(transcript_topics, issues_topics)
        
        # Calculate coverage percentage
        coverage_score = self._calculate_coverage_score(transcript_topics, issues_topics)
        
        return {
            "coverage_score": coverage_score,
            "transcript_topics": list(transcript_topics),
            "issues_topics": list(issues_topics),
            "missing_topics": list(missing_topics),
            "topic_distribution": self._get_topic_distribution(transcript)
        }
    
    def enhance_issues_list(self, issues: List[Dict[str, Any]], missing_topics: List[str], transcript: str) -> List[Dict[str, Any]]:
        """
        Generate additional issues for missing topics to ensure comprehensive coverage
        
        Args:
            issues: Existing generated issues
            missing_topics: Topics that are missing from the current issues
            transcript: The video transcript
            
        Returns:
            Enhanced list of issues with additions for missing topics
        """
        enhanced_issues = issues.copy()
        
        # For each missing topic, try to create an issue
        for topic in missing_topics:
            issue = self._generate_issue_for_topic(topic, transcript)
            if issue:
                enhanced_issues.append(issue)
        
        return enhanced_issues
        
    def _extract_technical_topics(self, transcript: str) -> Set[str]:
        """Extract all technical topics mentioned in the transcript"""
        topics = set()
        
        # Lowercase the transcript for better matching
        transcript_lower = transcript.lower()
        
        # Check for each indicator in our list
        for category, terms in self.technical_indicators.items():
            for term in terms:
                # Use word boundary to avoid partial matches
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, transcript_lower):
                    topics.add(term)
                    topics.add(category)  # Add the category as well
                    
        # Look for file extensions (potential code files)
        file_extensions = ['.js', '.py', '.java', '.html', '.css', '.ts', '.jsx', '.cpp', '.c', '.go', '.rb']
        for ext in file_extensions:
            if ext in transcript_lower:
                topics.add(ext.strip('.'))
                
        # Look for common programming patterns
        patterns = {
            "function": r'\bfunction\s+\w+\s*\(',
            "class": r'\bclass\s+\w+',
            "import": r'\bimport\s+[\w\s,{}]+\s+from\s',
            "api_calls": r'\b(get|post|put|delete|fetch)\s*\(',
            "variables": r'\b(const|let|var|final)\s+\w+',
            "loops": r'\b(for|while|each|map|reduce|filter)\b'
        }
        
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, transcript_lower):
                topics.add(pattern_name)
                
        return topics
    
    def _extract_issues_topics(self, issues: List[Dict[str, Any]]) -> Set[str]:
        """Extract all technical topics covered by the issues"""
        topics = set()
        
        for issue in issues:
            # Check title
            title = issue.get('title', '').lower()
            self._add_topics_from_text(title, topics)
            
            # Check description
            description = issue.get('description', '').lower()
            self._add_topics_from_text(description, topics)
            
            # Check labels
            labels = issue.get('labels', [])
            for label in labels:
                self._add_topics_from_text(label.lower(), topics)
                
            # Check implementation steps if available
            implementation_steps = []
            if isinstance(issue.get('implementation_steps'), list):
                implementation_steps = issue.get('implementation_steps', [])
            elif isinstance(issue.get('body'), dict):
                implementation_steps = issue.get('body', {}).get('implementation_steps', [])
                
            for step in implementation_steps:
                self._add_topics_from_text(step.lower(), topics)
                
        return topics
    
    def _add_topics_from_text(self, text: str, topics_set: Set[str]) -> None:
        """Add technical topics found in text to the topics set"""
        for category, terms in self.technical_indicators.items():
            for term in terms:
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, text):
                    topics_set.add(term)
                    break  # Once we've added this category, no need to check other terms
    
    def _identify_missing_topics(self, transcript_topics: Set[str], issues_topics: Set[str]) -> Set[str]:
        """Identify topics that are in the transcript but not covered in issues"""
        return transcript_topics - issues_topics
    
    def _calculate_coverage_score(self, transcript_topics: Set[str], issues_topics: Set[str]) -> float:
        """Calculate a score for how well the issues cover the topics in the transcript"""
        if not transcript_topics:
            return 100.0  # No topics to cover
            
        covered = len(transcript_topics.intersection(issues_topics))
        total = len(transcript_topics)
        
        return (covered / total) * 100
    
    def _get_topic_distribution(self, transcript: str) -> Dict[str, int]:
        """Get the distribution of topics in the transcript"""
        distribution = {}
        transcript_lower = transcript.lower()
        
        for category, terms in self.technical_indicators.items():
            count = 0
            for term in terms:
                pattern = r'\b' + re.escape(term) + r'\b'
                count += len(re.findall(pattern, transcript_lower))
            
            if count > 0:
                distribution[category] = count
                
        return distribution
    
    def _generate_issue_for_topic(self, topic: str, transcript: str) -> Optional[Dict[str, Any]]:
        """Generate a new issue for a missing topic"""
        # Find relevant sections in the transcript that mention this topic
        topic_sections = self._extract_topic_sections(topic, transcript)
        
        if not topic_sections:
            return None
            
        # Create an issue based on the most significant section
        best_section = topic_sections[0] if topic_sections else ""
        
        # Determine the appropriate title based on the topic
        title = f"Implement the {topic} functionality shown in the tutorial"
        
        # For certain topics, use more specific titles
        if topic in ["function", "class", "component", "api"]:
            title = f"Create the {topic} as demonstrated in the video"
        elif topic in self.technical_indicators.get("database", []):
            title = f"Set up and use {topic} as shown in the tutorial"
        elif topic in self.technical_indicators.get("devops", []):
            title = f"Configure {topic} as demonstrated in the video"
            
        return {
            "title": title,
            "description": f"""## {topic.title()} Implementation

This issue covers the {topic} aspects shown in the tutorial:

> {best_section}

Implement this functionality by following the video instructions.""",
            "difficulty": "intermediate",
            "labels": ["implementation", topic],
            "learning_objectives": [f"Learn how to implement {topic} functionality", 
                                  f"Apply {topic} concepts from the tutorial"],
            "implementation_steps": [
                f"1. Watch the segments of the tutorial that cover {topic}",
                "2. Set up the necessary environment and dependencies",
                f"3. Implement the {topic} functionality as shown",
                "4. Test your implementation to ensure it works correctly"
            ]
        }
        
    def _extract_topic_sections(self, topic: str, transcript: str) -> List[str]:
        """Extract sections from the transcript that mention the specified topic"""
        sections = []
        transcript_lower = transcript.lower()
        topic_lower = topic.lower()
        
        # Split transcript into sentences
        sentences = re.split(r'[.!?]', transcript)
        
        # Find sentences containing the topic
        topic_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if topic_lower in sentence.lower() and len(sentence) > 10:
                topic_sentences.append(sentence)
        
        # If we have direct mentions, use them
        if topic_sentences:
            return topic_sentences[:3]  # Return up to 3 most relevant sentences
            
        # If the exact topic isn't mentioned, look for related terms
        for category, terms in self.technical_indicators.items():
            if topic in terms or topic == category:
                for term in terms:
                    if term != topic:  # Don't check the topic itself again
                        for sentence in sentences:
                            sentence = sentence.strip()
                            if term.lower() in sentence.lower() and len(sentence) > 10:
                                sections.append(sentence)
                                if len(sections) >= 3:
                                    return sections
        
        return sections

    def ensure_required_categories(self, issues: List[Dict[str, Any]], transcript: str) -> List[Dict[str, Any]]:
        """
        Ensure that issues cover all major technical categories found in the transcript
        
        Args:
            issues: Current list of issues
            transcript: Transcript to analyze
            
        Returns:
            Enhanced list with added issues for missing major categories
        """
        # Find major categories in the transcript
        found_categories = set()
        transcript_lower = transcript.lower()
        
        for category, terms in self.technical_indicators.items():
            for term in terms:
                if re.search(r'\b' + re.escape(term) + r'\b', transcript_lower):
                    found_categories.add(category)
                    break
        
        # Check which categories are already covered in issues
        covered_categories = set()
        for issue in issues:
            issue_text = json.dumps(issue).lower()
            for category in found_categories:
                if category in issue_text or any(term in issue_text for term in self.technical_indicators.get(category, [])):
                    covered_categories.add(category)
        
        # Generate issues for missing major categories
        enhanced_issues = issues.copy()
        for category in (found_categories - covered_categories):
            relevant_terms = [term for term in self.technical_indicators.get(category, []) 
                             if term in transcript_lower]
            
            if relevant_terms:
                # Use the most frequently mentioned term
                term_counts = {term: transcript_lower.count(term) for term in relevant_terms}
                most_common_term = max(term_counts.items(), key=lambda x: x[1])[0]
                
                new_issue = self._generate_issue_for_topic(most_common_term, transcript)
                if new_issue:
                    enhanced_issues.append(new_issue)
        
        return enhanced_issues
