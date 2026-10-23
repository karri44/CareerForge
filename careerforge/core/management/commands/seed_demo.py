from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from jobs.models import Job, Skill
class Command(BaseCommand):
    help = 'Add clearly labelled fictional demonstration jobs. Safe to run repeatedly.'
    def handle(self, *args, **kwargs):
        companies = ['Northstar Demo', 'Orbit Demo', 'Bloom Demo', 'Canvas Demo', 'Waypoint Demo', 'Sprout Demo']
        titles = ['Junior Python Developer', 'Frontend Developer', 'Software Test Engineer', 'Django Developer', 'Customer Support · Non-voice', 'Data Operations Associate']
        places = ['Hyderabad', 'Remote', 'Bengaluru', 'Hyderabad', 'Remote', 'Pune']
        stacks = [['Python','Django','SQL'],['JavaScript','HTML','CSS'],['Testing','SQL','Postman'],['Django','Python','REST APIs'],['Communication','Email','Support'],['Excel','SQL','Analysis']]
        for i, company in enumerate(companies):
            user, created = User.objects.get_or_create(username=f'demo_company_{i}', defaults={'role':'EMPLOYER','company_name':company})
            if created: user.set_unusable_password(); user.save()
            job, created = Job.objects.get_or_create(employer=user,title=titles[i],defaults={'description':'DEMONSTRATION LISTING — fictional company and opportunity, for testing CareerForge only. This is not a real vacancy.\n\nAbout the role\nWork with a supportive team, solve practical problems, and build useful skills.\n\nWhat you will do\n• Collaborate on day-to-day projects and document your work.\n• Learn from feedback and contribute to improvements.\n• Communicate progress clearly with the team.\n\nWhat you will bring\nFoundational skills, attention to detail, and a willingness to learn. Fresh graduates are welcome.','location':places[i],'job_type':'FULL_TIME','salary_min':300000+i*25000,'salary_max':500000+i*30000,'deadline':timezone.localdate()+timedelta(days=60)})
            if created:
                job.skills_required.set([Skill.objects.get_or_create(name=name)[0] for name in stacks[i]])
        self.stdout.write(self.style.SUCCESS('Demo jobs added. These are fictional listings, not real vacancies. No login credentials were created.'))
