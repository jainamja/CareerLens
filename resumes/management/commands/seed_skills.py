from django.core.management.base import BaseCommand
from resumes.models import Skill

class Command(BaseCommand):
    help = 'Seeds the database with a technical Skill taxonomy'

    def handle(self, *args, **options):
        skills_data = [
            # Languages
            {'name': 'Python', 'category': 'language'},
            {'name': 'Java', 'category': 'language'},
            {'name': 'JavaScript', 'category': 'language'},
            {'name': 'TypeScript', 'category': 'language'},
            {'name': 'C', 'category': 'language'},
            {'name': 'C++', 'category': 'language'},
            {'name': 'C#', 'category': 'language'},
            {'name': 'Go', 'category': 'language'},
            {'name': 'R', 'category': 'language'},
            {'name': 'SQL', 'category': 'language'},
            {'name': 'HTML', 'category': 'language'},
            {'name': 'CSS', 'category': 'language'},

            # Frameworks
            {'name': 'Django', 'category': 'framework'},
            {'name': 'Flask', 'category': 'framework'},
            {'name': 'FastAPI', 'category': 'framework'},
            {'name': 'Django REST Framework', 'category': 'framework'},
            {'name': 'React', 'category': 'framework'},
            {'name': 'Angular', 'category': 'framework'},
            {'name': 'Vue', 'category': 'framework'},
            {'name': 'Node.js', 'category': 'framework'},
            
            # Libraries
            {'name': 'Pandas', 'category': 'library'},
            {'name': 'NumPy', 'category': 'library'},
            {'name': 'Scikit-learn', 'category': 'library'},
            {'name': 'Matplotlib', 'category': 'library'},
            {'name': 'PyTorch', 'category': 'library'},
            {'name': 'TensorFlow', 'category': 'library'},
            
            # Databases
            {'name': 'PostgreSQL', 'category': 'database'},
            {'name': 'MySQL', 'category': 'database'},
            {'name': 'MongoDB', 'category': 'database'},
            {'name': 'SQLite', 'category': 'database'},
            {'name': 'Redis', 'category': 'database'},
            
            # Tools
            {'name': 'Git', 'category': 'tool'},
            {'name': 'GitHub', 'category': 'tool'},
            {'name': 'Docker', 'category': 'tool'},
            {'name': 'Postman', 'category': 'tool'},
            {'name': 'VS Code', 'category': 'tool'},
            
            # Cloud
            {'name': 'AWS', 'category': 'cloud'},
            {'name': 'Azure', 'category': 'cloud'},
            {'name': 'Google Cloud', 'category': 'cloud'},
            
            # Concepts
            {'name': 'REST API', 'category': 'concept'},
            {'name': 'Machine Learning', 'category': 'concept'},
            {'name': 'Deep Learning', 'category': 'concept'},
            {'name': 'Natural Language Processing', 'category': 'concept'},
            {'name': 'Data Structures', 'category': 'concept'},
            {'name': 'Algorithms', 'category': 'concept'},
            {'name': 'Object-Oriented Programming', 'category': 'concept'},
            {'name': 'Database Management', 'category': 'concept'},
            {'name': 'Data Analysis', 'category': 'concept'},
            {'name': 'Data Visualization', 'category': 'concept'},
        ]

        created_count = 0
        for skill in skills_data:
            normalized_name = skill['name'].lower()
            obj, created = Skill.objects.get_or_create(
                normalized_name=normalized_name,
                defaults={'name': skill['name'], 'category': skill['category']}
            )
            if created:
                created_count += 1
            else:
                # Update category or original name if it differs but normalized is same
                if obj.category != skill['category'] or obj.name != skill['name']:
                    obj.category = skill['category']
                    obj.name = skill['name']
                    obj.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} new skills. Total skills: {Skill.objects.count()}'))
