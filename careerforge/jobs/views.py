from django.shortcuts import render

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Job, Skill
from django.db.models import Q
from django.utils import timezone
from .serializers import JobSerializer, SkillSerializer
from .permissions import IsEmployerOrReadOnly

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = JobSerializer
    permission_classes = [IsEmployerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['location', 'job_type']
    search_fields = ['title', 'description', 'skills_required__name']

    def get_queryset(self):
        qs = Job.objects.select_related('employer').prefetch_related('skills_required')
        if self.request.user.is_authenticated and self.request.user.role == 'EMPLOYER':
            return qs.filter(Q(employer=self.request.user) | (Q(is_active=True) & (Q(deadline__isnull=True) | Q(deadline__gte=timezone.localdate())))).order_by('-created_at')
        return qs.filter(is_active=True).filter(Q(deadline__isnull=True) | Q(deadline__gte=timezone.localdate())).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user)

class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
