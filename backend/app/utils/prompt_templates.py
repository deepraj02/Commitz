"""
Collection of specialized prompts to generate practical, learning-focused issues
from video transcripts.
"""

def get_practical_implementation_prompt() -> str:
    """
    Returns a prompt focused on generating practical, hands-on implementation tasks
    that directly follow what is shown in the video.
    """
    return """
    As a software development mentor, create PRACTICAL GitHub issues from this tutorial transcript.
    Focus on concrete tasks that implement exactly what is shown in the video.

    For each implementation task shown in the video:
    1. Create a separate issue focused on a specific PRACTICAL skill or component
    2. Include EXACT code snippets, commands, and file paths demonstrated
    3. List SPECIFIC implementation steps in the same order as the video
    4. Focus on HANDS-ON skills that produce working code/components
    5. Include any troubleshooting tips mentioned in the video

    Format each issue like this JSON:
    {
        "issues": [
            {
                "title": "[Specific Implementation Task]",
                "body": {
                    "description": "What you will build and why it's useful",
                    "implementation_steps": [
                        "1. Exact command: `npm install xyz`",
                        "2. Create file at exact path: src/components/...",
                        "3. Add this exact code: function xyz() {...}",
                        "4. Run this exact command to test: `npm test`"
                    ],
                    "expected_outcome": "Working component/feature that does X",
                    "prerequisites": [
                        "Must complete [previous task] first",
                        "Required tools: exact versions mentioned in video"
                    ]
                },
                "difficulty": "beginner/intermediate/advanced",
                "labels": ["implementation", "hands-on"],
                "sequence": 1 (order in which task appears in video)
            }
        ]
    }

    CRITICAL GUIDELINES:
    - Focus ONLY on practical implementation tasks shown in the video
    - Include EXACT code, commands and file paths from the video
    - Make sure steps are in the SAME ORDER as shown in the video
    - Each issue should result in a WORKING piece of functionality
    - Use ACTIONABLE titles: "Implement X" not "Learn about X"

    Analyze this transcript and create practical implementation issues:
    """

def get_project_building_prompt() -> str:
    """
    Returns a prompt focused on generating issues that collectively build
    a complete project as shown in the tutorial.
    """
    return """
    You are a project manager creating GitHub issues to build the exact project shown in this tutorial.
    Create issues that follow the video's implementation sequence precisely.

    For each component or feature shown in the video:
    1. Create a separate issue that results in working code
    2. Include the exact code, commands, and configuration shown
    3. Make sure steps follow the same sequence as the video
    4. Focus on practical implementation, not theory
    5. Include any troubleshooting or testing shown

    Format each issue like this:
    {
        "issues": [
            {
                "title": "Implement [specific component/feature]",
                "body": {
                    "description": "This component does X as part of the project",
                    "implementation_steps": [
                        "1. Create these exact files: X, Y, Z",
                        "2. Add this exact code: [code from video]",
                        "3. Run these commands: [commands from video]"
                    ],
                    "testing_steps": [
                        "1. Verify it works by checking X",
                        "2. Fix any errors as shown in video"
                    ]
                },
                "difficulty": "beginner/intermediate/advanced",
                "labels": ["implementation"],
                "project_sequence": 1 (position in project build sequence)
            }
        ]
    }

    IMPORTANT:
    - Issues should collectively build the COMPLETE project shown
    - Each issue should implement something that WORKS
    - Follow the EXACT implementation order from the video
    - Focus on CODING and BUILDING, not just understanding

    Analyze this transcript and create practical project-building issues:
    """

def get_tutorial_checkpoint_prompt() -> str:
    """
    Returns a prompt focused on creating practical checkpoint issues that verify
    progress through a tutorial's implemention steps.
    """
    return """
    As a coding instructor, create GitHub issues that represent practical checkpoints from this tutorial.
    Each issue should be a verifiable implementation milestone shown in the video.

    For each implementation milestone in the video:
    1. Create an issue that represents a complete, testable step
    2. Include the exact code and commands needed to reach this checkpoint
    3. Include verification steps to confirm it's working correctly
    4. Reference the exact tools, versions and setup needed

    Format each issue like this:
    {
        "issues": [
            {
                "title": "Checkpoint: [specific working implementation]",
                "body": {
                    "description": "In this checkpoint, you'll have implemented X that does Y",
                    "implementation_steps": [
                        "1. Exact steps from video to reach this point",
                        "2. Code: [exact code shown in video]"
                    ],
                    "verification": [
                        "1. Run this command: [test command]",
                        "2. Verify you see this output: [expected result]",
                        "3. Troubleshoot with these steps if needed: [fixes shown in video]"
                    ]
                },
                "difficulty": "beginner/intermediate/advanced",
                "labels": ["checkpoint", "implementation"],
                "tutorial_timestamp": "12:34" (approximate time in video)
            }
        ]
    }

    RULES:
    - Each checkpoint must be VERIFIABLE with a working result
    - Include EXACT code and commands from the video
    - Focus on PRACTICAL implementation, not concepts
    - Each checkpoint should build toward the complete project
    - Include troubleshooting for common issues shown in the video

    Analyze this transcript and create practical checkpoint issues:
    """
