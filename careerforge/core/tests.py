from datetime import timedelta
from tempfile import TemporaryDirectory
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient
from accounts.models import User
from jobs.models import Job
from applications.models import Application, CandidateProfile
from core.models import Notification, SavedJob

class CareerForgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate=User.objects.create_user(username='candidate',password='Test-pass-824!',role='CANDIDATE')
        cls.employer=User.objects.create_user(username='employer',password='Test-pass-824!',role='EMPLOYER',company_name='Example Team')
        cls.other=User.objects.create_user(username='other',password='Test-pass-824!',role='EMPLOYER')
        cls.job=Job.objects.create(employer=cls.employer,title='Python Engineer',description='Build useful software.',location='Hyderabad',job_type='FULL_TIME',salary_min=300000,salary_max=500000)
    def test_public_pages(self):
        for url in ['/',f'/jobs/{self.job.pk}/','/sign-in/','/join/']:
            with self.subTest(url=url):self.assertEqual(self.client.get(url).status_code,200)
    def test_search_and_filters(self):
        self.assertContains(self.client.get('/?q=Python&location=Hyderabad&type=FULL_TIME'),'Python Engineer')
        self.assertContains(self.client.get('/?q=missing'),'No opportunities found')
        self.assertContains(self.client.get('/?saved=1'),'No opportunities found')
    def test_registration_and_password_validation(self):
        data={'username':'newcandidate','email':'new@example.com','role':'CANDIDATE','password1':'Career-strong-942!','password2':'Career-strong-942!'}
        self.assertEqual(self.client.post('/join/',data).status_code,302)
        self.assertTrue(User.objects.filter(username='newcandidate').exists())
        response=APIClient().post('/api/auth/register/',{'username':'weak','email':'weak@example.com','password':'123','role':'CANDIDATE'})
        self.assertEqual(response.status_code,400)
    def test_candidate_workflow(self):
        self.client.force_login(self.candidate)
        self.client.post(f'/jobs/{self.job.pk}/save/')
        self.assertTrue(SavedJob.objects.filter(user=self.candidate,job=self.job).exists())
        self.assertContains(self.client.get('/?saved=1'),'Python Engineer')
        self.client.post(f'/jobs/{self.job.pk}/apply/',{'cover_note':'Interested in the role.'})
        self.client.post(f'/jobs/{self.job.pk}/apply/')
        self.assertEqual(Application.objects.count(),1)
        self.assertEqual(Notification.objects.filter(user=self.employer).count(),1)
        self.assertContains(self.client.get('/dashboard/'),'Python Engineer')
        for url in ['/profile/','/notifications/','/updates/']:
            self.assertEqual(self.client.get(url).status_code,200)
        app=Application.objects.get()
        self.client.post(f'/applications/{app.pk}/withdraw/')
        self.assertFalse(Application.objects.exists())
    def test_closed_job_excluded_and_not_applicable(self):
        self.job.deadline=timezone.localdate()-timedelta(days=1);self.job.save()
        self.assertNotContains(self.client.get('/'),'Python Engineer')
        self.client.force_login(self.candidate)
        self.assertEqual(self.client.post(f'/jobs/{self.job.pk}/apply/').status_code,404)
        api=APIClient();api.force_authenticate(self.candidate)
        self.assertEqual(api.post('/api/applications/',{'job':self.job.pk}).status_code,400)
    def test_employer_status_and_isolation(self):
        app=Application.objects.create(job=self.job,candidate=self.candidate)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f'/applications/{app.pk}/status/',{'status':'HIRED'}).status_code,404)
        self.assertEqual(self.client.get(f'/employer/{self.job.pk}/edit/').status_code,404)
        self.client.force_login(self.employer)
        self.assertEqual(self.client.get('/dashboard/').status_code,200)
        self.assertEqual(self.client.get('/employer/new/').status_code,200)
        self.client.post(f'/applications/{app.pk}/status/',{'status':'SHORTLISTED'})
        app.refresh_from_db();self.assertEqual(app.status,'SHORTLISTED')
        self.assertTrue(Notification.objects.filter(user=self.candidate).exists())
    def test_api_role_and_field_controls(self):
        api=APIClient();api.force_authenticate(self.candidate)
        self.assertEqual(api.post('/api/applications/',{'job':self.job.pk,'status':'HIRED'}).status_code,400)
        self.assertEqual(api.post('/api/applications/',{'job':self.job.pk}).status_code,201)
        self.assertEqual(api.post('/api/applications/',{'job':self.job.pk}).status_code,400)
        app=Application.objects.get()
        self.assertEqual(api.patch(f'/api/applications/{app.pk}/',{'status':'HIRED'}).status_code,400)
        api.force_authenticate(self.other)
        self.assertEqual(api.patch(f'/api/applications/{app.pk}/',{'status':'HIRED'}).status_code,404)
        api.force_authenticate(self.employer)
        self.assertEqual(api.patch(f'/api/applications/{app.pk}/',{'cover_note':'changed'}).status_code,400)
        self.assertEqual(api.patch(f'/api/applications/{app.pk}/',{'status':'HIRED'}).status_code,200)
        self.assertEqual(api.post('/api/applications/',{'job':self.job.pk}).status_code,400)
    def test_profile_resume_validation_and_access(self):
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            self.client.force_login(self.candidate)
            bad=SimpleUploadedFile('bad.pdf',b'not a pdf',content_type='application/pdf')
            self.assertContains(self.client.post('/profile/',{'bio':'Hello','experience_years':0,'resume':bad}),'valid PDF')
            pdf=SimpleUploadedFile('resume.pdf',b'%PDF-1.4\n%%EOF',content_type='application/pdf')
            self.assertEqual(self.client.post('/profile/',{'bio':'Hello','experience_years':0,'resume':pdf}).status_code,302)
            self.assertEqual(self.client.get(f'/resume/{self.candidate.pk}/').status_code,200)
            self.client.force_login(self.other)
            self.assertEqual(self.client.get(f'/resume/{self.candidate.pk}/').status_code,403)
            Application.objects.create(job=self.job,candidate=self.candidate)
            self.client.force_login(self.employer)
            self.assertEqual(self.client.get(f'/resume/{self.candidate.pk}/').status_code,200)
            self.assertEqual(self.client.get('/media/resumes/resume.pdf').status_code,404)
    def test_job_validation(self):
        self.client.force_login(self.employer)
        response=self.client.post('/employer/new/',{'title':'Test','description':'Description','location':'Remote','job_type':'FULL_TIME','salary_min':500000,'salary_max':100000,'is_active':True})
        self.assertContains(response,'Maximum salary must be at least the minimum')
    def test_csrf_and_post_only_mutations(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.candidate)
        self.assertEqual(client.post(f'/jobs/{self.job.pk}/apply/').status_code,403)
        self.assertEqual(client.get(f'/jobs/{self.job.pk}/apply/').status_code,405)
        self.assertEqual(client.get('/sign-out/').status_code,405)
    def test_demo_seed_is_repeatable(self):
        call_command('seed_demo',verbosity=0);count=Job.objects.count()
        call_command('seed_demo',verbosity=0);self.assertEqual(Job.objects.count(),count)
        self.assertEqual(Job.objects.filter(description__startswith='DEMONSTRATION LISTING').count(),6)
    def test_notifications_scoped(self):
        Notification.objects.create(user=self.candidate,message='Candidate update')
        Notification.objects.create(user=self.other,message='Other update')
        self.client.force_login(self.candidate)
        self.assertEqual(self.client.get('/updates/').json()['unread'],1)
        self.client.post('/notifications/read/')
        self.assertEqual(self.client.get('/updates/').json()['unread'],0)
        self.assertTrue(Notification.objects.filter(user=self.other,is_read=False).exists())
