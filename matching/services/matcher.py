import decimal
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from matching.models import MatchResult
from resumes.models import Resume
from jobs.models import Job

def calculate_skill_coverage(resume: Resume, job: Job):
    """
    Calculates the skill coverage score based ONLY on required skills of the job.
    Returns:
        score: float between 0 and 100
        matched: list of canonical skill names that were matched
        missing: list of canonical skill names that were required but missing
    """
    required_job_skills = job.job_skills.filter(is_required=True).select_related('skill')
    if not required_job_skills.exists():
        return 0.0, [], []
        
    required_skill_ids = set(js.skill.id for js in required_job_skills)
    resume_skill_ids = set(rs.skill.id for rs in resume.resume_skills.all())
    
    matched_ids = required_skill_ids.intersection(resume_skill_ids)
    
    score = (len(matched_ids) / len(required_skill_ids)) * 100.0
    
    # Get names for the lists
    skill_dict = {js.skill.id: js.skill.name for js in required_job_skills}
    matched_names = sorted([skill_dict[sid] for sid in matched_ids])
    missing_names = sorted([skill_dict[sid] for sid in required_skill_ids - matched_ids])
    
    return round(score, 2), matched_names, missing_names

def calculate_text_similarity(resume: Resume, job: Job):
    """
    Calculates TF-IDF cosine similarity between resume raw text and job description.
    Returns: float between 0 and 100
    """
    resume_text = (resume.raw_text or "").strip()
    job_text = (job.description or "").strip()
    
    if not resume_text or not job_text:
        return 0.0
        
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        # tfidf_matrix[0] is resume, tfidf_matrix[1] is job
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        score = similarity * 100.0
        return round(score, 2)
    except ValueError:
        # Happens if there's no shared vocabulary or documents only contain stop words
        return 0.0

def calculate_match(resume: Resume, job: Job):
    """
    Orchestrates the matching logic and creates/updates a MatchResult.
    Assume ownership validation is done at the caller level.
    """
    # 1. Skill Coverage
    skill_score, matched_skills, missing_skills = calculate_skill_coverage(resume, job)
    
    # 2. Text Similarity
    text_score = calculate_text_similarity(resume, job)
    
    # 3. Create or update MatchResult
    match_result, created = MatchResult.objects.update_or_create(
        resume=resume,
        job=job,
        defaults={
            'skill_coverage_score': decimal.Decimal(str(skill_score)),
            'text_similarity_score': decimal.Decimal(str(text_score)),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
        }
    )
    
    return match_result
