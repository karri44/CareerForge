from rest_framework.routers import DefaultRouter
from .views import JobViewSet, SkillViewSet

router = DefaultRouter()
router.register('jobs', JobViewSet, basename='job')
router.register('skills', SkillViewSet, basename='skill')

urlpatterns = router.urls