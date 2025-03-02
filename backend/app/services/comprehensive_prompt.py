"""
Specialized prompts designed to maximize comprehensive topic coverage
in the generated GitHub issues.
"""

def get_comprehensive_topics_prompt() -> str:
    """
    Returns a prompt designed to extract ALL technical topics from a video,
    focused on generating a comprehensive coverage of topics.
    """
    return """
    As an expert technical content analyzer, your task is to COMPREHENSIVELY identify and list ALL technical topics covered in this tutorial transcript.
    
    Analyze the transcript and:
    1. Identify EVERY technical concept, tool, framework, language, or technique mentioned
    2. Pay special attention to ALL implementation details, code examples, and technical steps
    3. Look for specific functions, methods, techniques, and patterns demonstrated
    4. Note ALL technologies, libraries, frameworks, and tools used
    
    For each identified topic, create a separate issue that follows this format:
    {
        "issues": [
            {
                "title": "Implement the [Specific Technical Topic]",
                "body": {
                    "description": "Technical explanation of what this topic is and how it's used in the video",
                    "implementation_steps": [
                        "Exact steps from the video to implement this specific topic"
                    ]
                },
                "difficulty": "beginner/intermediate/advanced",
                "labels": ["technical-topic", "implementation"],
                "topic_category": "language/framework/concept/tool/etc."
            }
        ]
    }
    
    CRITICAL GUIDELINES:
    - Be COMPREHENSIVE - don't miss ANY technical topics, no matter how small
    - Focus on TECHNICAL content only - not theoretical explanations
    - Create SEPARATE issues for each distinct technical aspect
    - Include EXACT implementation details from the video
    - Make sure each issue is PRACTICAL and implementable
    - Issues should collectively cover EVERY technical aspect mentioned
    
    Your performance will be judged on how COMPLETELY you cover ALL technical topics in the transcript.
    
    Analyze this transcript and create comprehensive technical issues:
    """

def get_topic_extraction_prompt() -> str:
    """
    Returns a prompt specifically designed to extract a comprehensive list
    of technical topics from a transcript.
    """
    return """
    You are a technical topic analyzer. Extract ALL technical topics mentioned in this transcript.
    
    Focus ONLY on listing the technical topics, not creating full issues.
    Include:
    1. Programming languages (e.g., JavaScript, Python)
    2. Frameworks and libraries (e.g., React, Django)
    3. Tools and technologies (e.g., Docker, AWS)
    4. Programming concepts (e.g., closures, dependency injection)
    5. Specific functions, methods or APIs mentioned
    6. File types and formats discussed
    7. Configuration options explained
    8. Command line tools and commands shown
    
    Format your response as a JSON array of topics:
    {
        "topics": [
            {
                "name": "React Hooks",
                "category": "framework_feature",
                "confidence": 0.95
            },
            {
                "name": "useState",
                "category": "function",
                "confidence": 0.98
            }
        ]
    }
    
    The confidence score (0.0-1.0) should indicate how certain you are that this topic is actually covered in the transcript.
    
    BE THOROUGH. Missing technical topics is considered a major error.
    
    Analyze this transcript and list ALL technical topics:
    """

def get_completeness_verification_prompt(topics_list: list, issues_list: list) -> str:
    """
    Returns a prompt that verifies whether the generated issues cover all identified topics.
    
    Args:
        topics_list: List of extracted technical topics
        issues_list: List of generated GitHub issues
        
    Returns:
        A prompt to verify coverage completeness
    """
    topics_json = json.dumps(topics_list, indent=2)
    issues_json = json.dumps(issues_list, indent=2)
    
    return f"""
    As a technical content auditor, verify whether the generated GitHub issues comprehensively cover all the identified technical topics from the transcript.
    
    Here are the technical topics identified in the transcript:
    ```json
    {topics_json}
    ```
    
    And here are the GitHub issues that have been generated:
    ```json
    {issues_json}
    ```
    
    Your task:
    1. For each technical topic, determine if it's adequately covered in the GitHub issues
    2. Identify any topics that are missing or insufficiently covered
    3. Suggest additional issues that should be created to ensure complete coverage
    
    Format your response as:
    ```json
    {{
        "completeness_score": 0.85, // 0.0-1.0 score of how completely the issues cover the topics
        "missing_topics": [
            {{
                "name": "Topic Name",
                "importance": "high/medium/low",
                "suggested_issue": {{
                    "title": "Implement [Topic]",
                    "description": "Suggested description",
                    "implementation_steps": ["Step 1", "Step 2"]
                }}
            }}
        ],
        "feedback": "Overall assessment of coverage"
    }}
    ```
    
    Prioritize technical accuracy and comprehensive coverage in your assessment.
    """

import json
