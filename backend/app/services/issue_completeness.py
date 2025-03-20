import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class IssueCompletenessService:
    def __init__(self):
        self.key_terms = {
            "programming": ["function", "class", "variable", "import", "api"],
            "tools": ["react", "docker", "aws", "python", "javascript"],
            "concepts": ["async", "rest", "database", "authentication"]
        }

    def ensure_completeness(self, issues: List[Dict], transcript: str) -> List[Dict]:
        covered_topics = {term for issue in issues for term in self._extract_terms(issue["title"] + issue["description"])}
        transcript_terms = self._extract_terms(transcript.lower())

        missing_terms = transcript_terms - covered_topics
        if not missing_terms:
            return issues

        enhanced_issues = issues.copy()
        for term in missing_terms:
            description = f"""Add functionality related to {term} as mentioned in the transcript.

## Steps
1. Identify where {term} is referenced in the video.
2. Implement the {term}-related feature based on the video's instructions.
3. Test the implementation to ensure it works as expected.

**Difficulty**: intermediate
**Labels**: [implementation]"""
            enhanced_issues.append({
                "title": f"Implement {term.capitalize()} Feature",
                "description": description.strip()
            })
        logger.info(f"Added {len(missing_terms)} issues for completeness")
        return enhanced_issues

    def _extract_terms(self, text: str) -> set:
        terms = set()
        for category, keywords in self.key_terms.items():
            for keyword in keywords:
                if keyword in text:
                    terms.add(keyword)
        return terms