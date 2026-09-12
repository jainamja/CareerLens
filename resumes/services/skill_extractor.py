import re
from resumes.models import Skill

# Aliases mapped to their normalized canonical name
SKILL_ALIASES = {
    'drf': 'django rest framework',
    'django rest framework': 'django rest framework',
    'js': 'javascript',
    'ts': 'typescript',
    'postgres': 'postgresql',
    'postgre sql': 'postgresql',
    'node': 'node.js',
    'nodejs': 'node.js',
    'reactjs': 'react',
    'vuejs': 'vue',
    'cpp': 'c++',
    'c plus plus': 'c++',
    'c sharp': 'c#',
    'golang': 'go',
    'aws': 'aws',
    'gcp': 'google cloud',
    'google cloud platform': 'google cloud',
    'rest': 'rest api',
    'restful api': 'rest api',
    'ml': 'machine learning',
    'oop': 'object-oriented programming',
}

def extract_skills(raw_text):
    """
    Extracts canonical Skill objects from raw_text.
    Uses regex word boundaries to avoid substring matching.
    """
    if not raw_text:
        return []

    # Get all canonical skills
    all_skills = Skill.objects.all()
    detected_skills = set()
    
    # We will search case-insensitively, so we lower the text.
    # Note: re.IGNORECASE is used in regex matching.
    text = raw_text

    for skill in all_skills:
        # Check canonical name
        pattern = r'\b' + re.escape(skill.name) + r'\b'
        
        # Special cases for C, R, C++, C# which might be tricky with word boundaries
        # For C and R, we want to be very strict to avoid matching 'c' in lists or 'r'
        # e.g. "A, B, C" or "R&D". 
        if skill.name in ['C', 'R', 'C++', 'C#', 'Go']:
            # More strict pattern: look for whitespace/punctuation around it
            pattern = r'(?<!\w)' + re.escape(skill.name) + r'(?!\w)'

        if re.search(pattern, text, re.IGNORECASE):
            detected_skills.add(skill)
            continue
            
    # Check aliases
    for alias, canonical_normalized in SKILL_ALIASES.items():
        pattern = r'\b' + re.escape(alias) + r'\b'
        if alias in ['cpp', 'c sharp', 'aws', 'gcp', 'rest', 'ml', 'oop', 'js', 'ts']:
            pattern = r'(?<!\w)' + re.escape(alias) + r'(?!\w)'
            
        if re.search(pattern, text, re.IGNORECASE):
            # Find the canonical skill in our db
            canonical_skill = next((s for s in all_skills if s.normalized_name == canonical_normalized), None)
            if canonical_skill:
                detected_skills.add(canonical_skill)

    return list(detected_skills)
