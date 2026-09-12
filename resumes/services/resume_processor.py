from .pdf_extractor import process_resume_pdf, PDFExtractionError
from .skill_extractor import extract_skills
from resumes.models import ResumeSkill
import logging

logger = logging.getLogger(__name__)

def process_resume(resume):
    """
    Takes a saved Resume instance, extracts text, extracts skills, and updates status.
    """
    try:
        if not resume.file:
            return
            
        file_path = resume.file.path
        raw_text = process_resume_pdf(file_path)
        
        resume.raw_text = raw_text
        resume.is_processed = True
        resume.processing_error = None
        
        # Skill Extraction
        try:
            detected_skills = extract_skills(raw_text)
            # Clear old skills in case of reprocessing
            ResumeSkill.objects.filter(resume=resume).delete()
            # Bulk create new relationships
            resume_skills = [ResumeSkill(resume=resume, skill=skill) for skill in detected_skills]
            ResumeSkill.objects.bulk_create(resume_skills)
        except Exception as e:
            logger.error(f"Failed to extract skills for resume {resume.id}: {str(e)}", exc_info=True)
            # Requirements say: "If PDF extraction succeeds but skill extraction fails... The system should not leave misleading data"
            resume.is_processed = False
            resume.processing_error = "An error occurred while detecting skills in your resume."
        
    except PDFExtractionError as e:
        resume.is_processed = False
        resume.processing_error = str(e)
    except Exception as e:
        logger.error(f"Failed to process resume {resume.id}: {str(e)}", exc_info=True)
        resume.is_processed = False
        resume.processing_error = "An unexpected error occurred while processing your resume."
    
    resume.save(update_fields=['raw_text', 'is_processed', 'processing_error', 'updated_at'])
