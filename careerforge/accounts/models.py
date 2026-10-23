from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYER = 'EMPLOYER', 'Employer'
        CANDIDATE = 'CANDIDATE', 'Candidate'

    role = models.CharField(max_length=10, choices=Role.choices)
    phone = models.CharField(max_length=15, blank=True)
    company_name = models.CharField(max_length=100, blank=True)  # only for employers