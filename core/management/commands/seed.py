from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from jobs.models import Job, JobSkill
from applications.models import Application
from resumes.models import Resume, Skill, ResumeSkill
from matching.models import MatchResult
from datetime import timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Seeds the database with sample data for UI preview'

    def handle(self, *args, **kwargs):
        username = 'testuser'
        password = 'testpassword123'
        email = 'test@careerlens.dev'

        # 1. Clean up existing testuser to make script idempotent
        User.objects.filter(username=username).delete()

        # Create the test user
        user = User.objects.create_user(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"[*] Created User: {username} | Password: {password} | Email: {email}"))

        # 2. Create Base Skills
        skills_data = [
            ('Python', 'python', 'language'),
            ('Django', 'django', 'framework'),
            ('React', 'react', 'library'),
            ('JavaScript', 'javascript', 'language'),
            ('SQL', 'sql', 'language'),
            ('PostgreSQL', 'postgresql', 'database'),
            ('Docker', 'docker', 'tool'),
            ('AWS', 'aws', 'cloud'),
            ('Figma', 'figma', 'tool'),
            ('UI/UX Design', 'ui/ux design', 'concept'),
            ('Data Analysis', 'data analysis', 'concept'),
        ]
        db_skills = []
        for name, norm, cat in skills_data:
            skill, _ = Skill.objects.get_or_create(name=name, normalized_name=norm, defaults={'category': cat})
            db_skills.append(skill)

        # 3. Create Resumes
        self.stdout.write("[*] Creating Resumes...")
        resume_names = ["Software Engineer Resume.pdf", "Product Designer Resume.pdf", "Data Analyst Resume.pdf"]
        resumes = []
        for r_name in resume_names:
            r = Resume(
                user=user,
                original_filename=r_name,
                raw_text=f"This is a sample extracted text for {r_name}.\nI am highly skilled in various technologies.",
                is_processed=True
            )
            r.file.save(r_name, ContentFile(b"Dummy PDF content"))
            r.save()
            resumes.append(r)
            
            # Add random skills to resume
            sample_skills = random.sample(db_skills, k=random.randint(4, 7))
            for s in sample_skills:
                ResumeSkill.objects.create(resume=r, skill=s)

        # 4. Create Jobs & Applications
        self.stdout.write("[*] Creating Jobs & Applications...")
        companies = ["Stripe", "Notion", "Figma", "Airbnb", "Local Startup", "TechCorp", "Vercel", "Acme Corp", "GlobalNet", "Innovate LLC"]
        roles = ["Software Engineer", "Frontend Developer", "Backend Engineer", "Product Designer", "Data Analyst", "Full Stack Engineer"]
        
        jobs = []
        now = timezone.now()

        statuses = [
            Application.StatusChoices.APPLIED, Application.StatusChoices.APPLIED,
            Application.StatusChoices.INTERVIEW, Application.StatusChoices.INTERVIEW,
            Application.StatusChoices.OFFER, Application.StatusChoices.OFFER,
            Application.StatusChoices.REJECTED, Application.StatusChoices.REJECTED,
            Application.StatusChoices.SAVED, Application.StatusChoices.ASSESSMENT
        ]
        random.shuffle(statuses)

        for i in range(10):
            job = Job.objects.create(
                user=user,
                title=random.choice(roles) + f" {i+1}",
                company=companies[i],
                description=f"We are looking for a highly motivated individual to join {companies[i]} as a {random.choice(roles)}.",
                location=random.choice(["Remote", "New York, NY", "San Francisco, CA", "London, UK", "Austin, TX"]),
                salary=random.choice(["$100k - $120k", "$130k - $160k", "Competitive", "$90k - $110k", ""]),
                job_url=f"https://{companies[i].lower().replace(' ', '')}.com/careers"
            )
            # Override created_at
            job.created_at = now - timedelta(days=random.randint(1, 60))
            job.save()
            jobs.append(job)

            req_skills = random.sample(db_skills, k=random.randint(3, 5))
            for s in req_skills:
                JobSkill.objects.create(job=job, skill=s, is_required=True)
                
            opt_skills = random.sample([s for s in db_skills if s not in req_skills], k=random.randint(0, 2))
            for s in opt_skills:
                JobSkill.objects.create(job=job, skill=s, is_required=False)

            applied_date = (now - timedelta(days=random.randint(1, 60))).date()
            status = statuses[i]
            
            if status == Application.StatusChoices.SAVED:
                applied_date = None
                
            Application.objects.create(
                user=user,
                job=job,
                status=status,
                applied_date=applied_date,
                notes=f"Sample notes for {companies[i]} application." if random.choice([True, False]) else ""
            )

        # 5. Create Job Matches
        self.stdout.write("[*] Creating Job Matches...")
        for i in range(8):
            job = jobs[i]
            resume = random.choice(resumes)
            
            req_skill_names = list(job.job_skills.filter(is_required=True).values_list('skill__name', flat=True))
            resume_skill_names = list(resume.resume_skills.values_list('skill__name', flat=True))
            
            matched = [s for s in req_skill_names if s in resume_skill_names]
            missing = [s for s in req_skill_names if s not in resume_skill_names]
            
            skill_score = random.uniform(50.0, 95.0)
            text_score = random.uniform(40.0, 92.0)
            
            if len(req_skill_names) > 0:
                skill_score = (len(matched) / len(req_skill_names)) * 100
            
            MatchResult.objects.create(
                resume=resume,
                job=job,
                skill_coverage_score=skill_score,
                text_similarity_score=text_score,
                matched_skills=matched,
                missing_skills=missing
            )

        self.stdout.write(self.style.SUCCESS("\n--- Seed Data Summary ---"))
        self.stdout.write(f"Users: 1 (testuser)")
        self.stdout.write(f"Resumes: {Resume.objects.filter(user=user).count()}")
        self.stdout.write(f"Jobs: {Job.objects.filter(user=user).count()}")
        self.stdout.write(f"Applications: {Application.objects.filter(user=user).count()}")
        self.stdout.write(f"Match Results: {MatchResult.objects.filter(resume__user=user).count()}")
        self.stdout.write(self.style.SUCCESS("-------------------------\n"))
