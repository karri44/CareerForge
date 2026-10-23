from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ApplicationViewSet, CandidateProfileView

router = DefaultRouter()
router.register('applications', ApplicationViewSet, basename='application')

urlpatterns = [
    path('candidate/profile/', CandidateProfileView.as_view(), name='candidate-profile'),
] + router.urls