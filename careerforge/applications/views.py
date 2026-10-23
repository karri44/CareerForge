from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from .models import CandidateProfile, Application
from .serializers import CandidateProfileSerializer, ApplicationSerializer
from .permissions import IsCandidateOwnerOrEmployerReadOnly
from core.models import Notification
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

class CandidateProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = CandidateProfile.objects.get_or_create(user=self.request.user)
        return profile

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsCandidateOwnerOrEmployerReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'EMPLOYER':
            return Application.objects.filter(job__employer=user)
        return Application.objects.filter(candidate=user)

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                application = serializer.save(candidate=self.request.user)
                Notification.objects.create(user=application.job.employer, message=f'New application for {application.job.title}.')
        except IntegrityError:
            raise ValidationError('You have already applied to this job.')

    def perform_update(self, serializer):
        previous = serializer.instance.status
        application = serializer.save()
        if application.status != previous:
            Notification.objects.create(user=application.candidate, message=f'{application.job.title}: your application is now {application.get_status_display().lower()}.')